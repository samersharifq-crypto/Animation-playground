"""Creative post pass over the finished short. Same length, same audio, same on-screen text.
usage: regrade.py SRC OUT.mp4 first last     (frame range, last exclusive)
       regrade.py SRC sheet.png t1 t2 ...     (preview sheet at those seconds)
"""
import sys, math, subprocess
import numpy as np, cv2

W, H, FPS, N = 1080, 1920, 24, 1284
FADE_IN, FADE_OUT = 6, 1266            # source frames < 6 and >= 1266 are faded to black
OPEN = [6, 9]                          # two clean opening poses (8 fps animation, 3 frames each)
HOLD = [1257, 1260, 1263]              # last clean poses before the source fade-out

# ---------------------------------------------------------------- look keyframes
#        t      sat   temp   expo  bloom  vig   zoom  ay    dust
KEYS = [
    (0.00, 1.06, 0.03, 1.00, 0.40, 0.15, 1.000, 0.0, 0.55),
    (6.00, 1.06, 0.03, 1.00, 0.40, 0.18, 1.045, 0.0, 0.55),
    (6.45, 0.84, -0.07, 0.98, 0.30, 0.28, 1.000, 0.5, 0.00),
    (8.70, 0.84, -0.07, 0.98, 0.30, 0.30, 1.035, 0.5, 0.00),
    (8.75, 0.80, -0.04, 1.00, 0.10, 0.25, 1.000, 1.0, 0.00),
    (13.30, 0.50, -0.05, 0.92, 0.05, 0.60, 1.055, 1.0, 0.00),
    (13.85, 0.82, -0.03, 1.00, 0.30, 0.30, 1.000, 0.0, 0.00),
    (17.90, 0.82, -0.03, 1.00, 0.30, 0.34, 1.035, 0.0, 0.00),
    (18.05, 0.22, -0.06, 0.92, 0.00, 0.62, 1.035, 0.0, 0.00),
    (20.05, 0.18, -0.06, 0.88, 0.00, 0.70, 1.050, 0.0, 0.00),
    (20.60, 1.00, 0.02, 1.00, 0.06, 0.00, 1.000, 0.5, 0.45),
    (33.55, 1.00, 0.03, 1.00, 0.06, 0.00, 1.030, 0.5, 0.45),
    (34.10, 0.80, -0.02, 0.96, 0.30, 0.40, 1.000, 0.5, 0.10),
    (36.70, 0.85, 0.00, 0.98, 0.35, 0.36, 1.015, 0.5, 0.20),
    (39.90, 0.98, 0.02, 1.00, 0.50, 0.28, 1.030, 0.5, 0.45),
    (40.00, 1.14, 0.05, 1.06, 0.95, 0.08, 1.030, 0.5, 1.00),
    (41.50, 1.12, 0.05, 1.02, 0.60, 0.08, 1.040, 0.5, 1.00),
    (43.10, 1.12, 0.05, 1.02, 0.60, 0.08, 1.045, 0.5, 1.00),
    (43.60, 1.12, 0.05, 1.00, 0.50, 0.10, 1.035, 0.0, 0.80),
    (46.50, 1.14, 0.05, 1.02, 0.55, 0.06, 1.000, 0.0, 0.90),
    (53.50, 1.16, 0.06, 1.03, 0.60, 0.04, 1.000, 0.0, 0.90),
]
KT = np.array([k[0] for k in KEYS]); KV = np.array([k[1:] for k in KEYS])

def look(t):
    return [float(np.interp(t, KT, KV[:, i])) for i in range(KV.shape[1])]

#  (time, amplitude px, duration)
SHAKES = [(8.42, 16, 0.42), (18.0, 12, 0.40), (36.75, 6, 0.25), (37.75, 6, 0.25),
          (39.50, 8, 0.30), (40.0, 11, 0.40), (44.42, 11, 0.38)]
KICKS = [(3.75, 0.022, 0.4), (13.75, 0.02, 0.35), (18.0, 0.03, 0.5), (40.0, 0.03, 0.8), (46.0, 0.0, 0.5)]
SPLITS = [(8.42, 9, 0.4), (18.0, 8, 0.45)]             # chroma split px
REDPULSE = [(13.75, 0.30, 0.6)]                        # warning vignette
FLASH = [(40.0, 0.20, 0.45), (46.0, 0.10, 0.5)]        # warm light burst
GLITCH = [(18.0, 0.25)]

def env(t, t0, dur):
    """1 -> 0 over dur, stepped at 8 fps like the animation."""
    if t < t0 or t >= t0 + dur: return 0.0
    u = math.floor((t - t0) * 8 + 1e-6) / 8 / dur
    return (1 - u) ** 2

# ---------------------------------------------------------------- helpers
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
RAD = (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
VIGM = np.clip(RAD, 0, 2) ** 1.3 / 2 ** 1.3 * 1.6
VIGM = VIGM[..., None].astype(np.float32)

# verse card reading light
LINES = [480, 625, 780, 930, 1085]
T_READ0, T_LINE = 23.0, 1.95

def reading_light(t):
    """Per-row brightness: unread lines sit in shade, the current line is lit, read lines stay normal."""
    if t < 22.6 or t > 33.4: return None
    fade = min(1.0, (t - 22.6) / 0.4) * min(1.0, (33.4 - t) / 0.4)
    ts = math.floor(t * 8) / 8
    rows = np.ones(H, np.float32)
    y = np.arange(H, dtype=np.float32)
    for i, cy in enumerate(LINES):
        a = T_READ0 + i * T_LINE
        on = float(np.clip((ts - a) / 0.375, 0, 1))                 # line lights up
        cur = on * float(np.clip((a + T_LINE + 0.3 - ts) / 0.375, 0, 1))
        band = np.exp(-((y - cy) / 62) ** 4)
        rows += band * ((-0.30) * (1 - on) + 0.13 * cur)
    rows = 1 + (rows - 1) * fade
    m = np.ones((H, W), np.float32)
    xw = np.clip(np.minimum(np.arange(W) - 85, 1000 - np.arange(W)) / 40, 0, 1).astype(np.float32)
    m = 1 + (rows[:, None] - 1) * xw[None, :]
    return m[..., None]

_prng = np.random.default_rng(11)
P = _prng.uniform(0, 1, (90, 6))        # x, y, speed, size, phase, sway

def dust_layer(t, strength):
    """Gold dust motes rising through the light, moved on 8 fps steps."""
    ts = math.floor(t * 8) / 8
    lay = np.zeros((H // 4, W // 4), np.float32)
    for x, y, sp, sz, ph, sw in P:
        yy = (y - ts * (0.012 + 0.03 * sp)) % 1.0
        xx = x + 0.03 * math.sin(ts * (0.4 + sw) + ph * 6.28)
        tw = 0.55 + 0.45 * math.sin(ts * (1.5 + 2 * sw) + ph * 6.28)
        cv2.circle(lay, (int(xx * W / 4), int(yy * H / 4)), int(1 + sz * 2.2), float(tw), -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.1) + 0.6 * cv2.GaussianBlur(lay, (0, 0), 4)
    lay = cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)
    return lay[..., None] * np.array([120, 200, 255], np.float32) * (0.55 * strength)   # BGR gold

def grade(img, tl, n):
    """img: uint8 BGR source frame. tl: time used for the look. n: output frame (stepped clock)."""
    sat, temp, expo, bloom, vig, zoom, ay, dust = look(tl)
    f8 = n // 3
    r = np.random.default_rng(f8)
    a = img.astype(np.float32)

    if tl < 33.6:
        m = reading_light(tl)
        if m is not None: a *= m

    # saturation; in the despair look red survives while everything else drains
    g = a @ np.array([0.114, 0.587, 0.299], np.float32)
    s = np.float32(sat)
    if sat < 0.6:
        red = np.clip((a[..., 2] - np.maximum(a[..., 1], a[..., 0]) - 40) / 50, 0, 1)
        s = (sat + (1.15 - sat) * red)[..., None]
    a = g[..., None] + (a - g[..., None]) * s
    a *= np.array([1 - temp, 1.0, 1 + temp], np.float32) * expo

    # bloom with a candle flicker
    if bloom > 0.01:
        small = cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        lum = small.max(axis=2)
        hi = small * np.clip((lum - 150) / 80, 0, 1)[..., None]
        hi = cv2.GaussianBlur(hi, (0, 0), 14) + 0.5 * cv2.GaussianBlur(hi, (0, 0), 40)
        fl = 1 + 0.16 * r.normal()
        a += cv2.resize(hi, (W, H), interpolation=cv2.INTER_LINEAR) * (bloom * fl * 0.55) * np.array([0.75, 0.92, 1.0], np.float32)

    for t0, amt, d in FLASH:
        e = env(tl, t0, d)
        if e: a = a + (np.array([150, 215, 255], np.float32) - a * 0.4) * (amt * e)

    if dust > 0.01:
        a += dust_layer(tl, dust)

    # heartbeat in the close-up: two short thumps per beat, vignette tightens with it
    beat = 0.0
    if 9.2 <= tl < 13.35:
        ph = ((tl - 9.2) % 1.0)
        beat = 1.0 if ph < 0.125 else (0.6 if 0.25 <= ph < 0.375 else 0.0)
    a *= 1 - VIGM * (vig + 0.18 * beat)

    for t0, amt, d in REDPULSE:
        e = env(tl, t0, d)
        if e:
            k = np.clip(VIGM * 1.1, 0, 1) * (amt * e)
            a = a * (1 - k) + np.array([42, 62, 178], np.float32) * k

    a = np.clip(a, 0, 255)

    # camera: stepped push-in, kicks, shake
    z = 1 + (round((zoom - 1) * 400) / 400)
    for t0, amt, d in KICKS: z += amt * env(tl, t0, d)
    z += 0.006 * beat
    dx = dy = 0.0
    for t0, amp, d in SHAKES:
        e = env(tl, t0, d)
        if e: dx += r.normal(0, amp * e); dy += r.normal(0, amp * e)
    if z != 1 or dx or dy:
        cx, cy = W / 2, ay * H                      # anchor keeps labels at that edge in frame
        M = np.float32([[z, 0, cx - z * cx + dx], [0, z, cy - z * cy + dy]])
        a = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
        blur = cv2.GaussianBlur(a, (0, 0), 1.2)
        a = cv2.addWeighted(a, 1.25, blur, -0.25, 0)

    for t0, px, d in SPLITS:
        e = env(tl, t0, d)
        if e:
            k = int(round(px * e))
            if k:
                a[..., 2] = np.roll(a[..., 2], k, axis=1); a[..., 0] = np.roll(a[..., 0], -k, axis=1)
    for t0, d in GLITCH:
        if t0 <= tl < t0 + d:
            for y0 in range(0, H, 150):
                yb = y0 + int(r.integers(0, 90))
                a[yb:yb + 46] = np.roll(a[yb:yb + 46], int(r.integers(-60, 60)), axis=1)

    a += np.random.default_rng(5000 + n).normal(0, 0.9, (H, W, 1)).astype(np.float32)
    return np.clip(a, 0, 255).astype(np.uint8)

def tear(prev, cur, u, n):
    """Torn-paper wipe right -> left with a cream fibre edge."""
    r = np.random.default_rng(900 + n // 3)
    xb = W + 120 - u * (W + 360)
    ys = np.arange(-20, H + 60, 24)
    pts = np.array([[xb + 110 * (y / H) + r.normal(0, 12), y] for y in ys], np.int32)
    mask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(mask, [np.vstack([[[W + 50, -20]], pts, [[W + 50, H + 60]]]).astype(np.int32)], 255)
    out = np.where(mask[..., None] > 0, cur, prev)
    cv2.polylines(out, [pts + np.array([8, 0])], False, (16, 8, 5), 5, cv2.LINE_AA)
    cv2.polylines(out, [pts], False, (220, 236, 244), 13, cv2.LINE_AA)
    return out

def build(n, src, cache):
    """Output frame n from source frame `src` (already read) and cached clean frames."""
    t = n / FPS
    if n < FADE_IN:                                   # source fades in from black: open on the image instead
        return grade(cache[OPEN[(n // 3) % 2]], 0.3, n)
    if n >= FADE_OUT:                                 # source fades out: tear back into the opening (loop)
        k = n - FADE_OUT
        hold = grade(cache[HOLD[(k // 3) % 3]], 52.7, n)
        first = grade(cache[OPEN[(k // 3) % 2]], 0.3, n)
        return tear(hold, first, min(1.0, (k // 3 * 3 + 3) / 18), n)
    return grade(src, t, n)

def frames(wanted):
    cap = cv2.VideoCapture(sys.argv[1]); cache = {}; keep = set(OPEN + HOLD)
    for i in range(max(OPEN) + 1):                    # opening poses are needed before they are reached
        ok, im = cap.read()
        if i in keep: cache[i] = im.copy()
    cap.release(); cap = cv2.VideoCapture(sys.argv[1])
    last = max(wanted)
    for i in range(N):
        ok, im = cap.read()
        if not ok: break
        if i in keep: cache[i] = im.copy()
        if i in wanted: yield i, build(i, im, cache)
        if i >= last: break

if __name__ == "__main__":
    out = sys.argv[2]
    if out.endswith(".png"):
        ts = [float(x) for x in sys.argv[3:]]
        want = {int(round(t * FPS)): t for t in ts}
        ims = {}
        for i, im in frames(set(want)):
            im = cv2.resize(im, (360, 640), interpolation=cv2.INTER_AREA)
            cv2.putText(im, f"{want[i]:.2f}", (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            ims[i] = im
        ims = [ims[k] for k in sorted(ims)]
        cols = 8; rows = (len(ims) + cols - 1) // cols
        sheet = np.zeros((640 * rows, 360 * cols, 3), np.uint8)
        for j, im in enumerate(ims):
            sheet[(j // cols) * 640:(j // cols + 1) * 640, (j % cols) * 360:(j % cols + 1) * 360] = im
        cv2.imwrite(out, sheet)
    else:
        a, b = int(sys.argv[3]), int(sys.argv[4])
        enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                                "-s", f"{W}x{H}", "-r", "24", "-i", "-", "-c:v", "libx264", "-profile:v", "main",
                                "-level", "4.0", "-preset", "medium", "-crf", sys.argv[5] if len(sys.argv) > 5 else "24",
                                "-pix_fmt", "yuv420p", "-g", "48", out], stdin=subprocess.PIPE)
        for i, im in frames(set(range(a, b))):
            enc.stdin.write(im.tobytes())
        enc.stdin.close(); enc.wait()
