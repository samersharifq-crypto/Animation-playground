"""بصيرة · فيديو سيزيف · الجزء ٤: «الصعود» (1:30–2:00). Also the base of the vertical Short."""
import sys, os, json, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "frames4"); os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates)
T = dict(khutwa=0.0, thumma=1.6, araq=4.0, yaqtarib=9.0, ala=12.0, bud=12.4, dhira=12.8,
         intasar=15.0, aflatat=16.0, alqa=21.0, saqat=23.0, ala2=25.0, wajhih=25.4)
_tj = os.path.join(HERE, "proj", "times_4.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["wajhih"] + 2.8
FREEZE = (T["intasar"], T["aflatat"])        # «انتصر» … everything holds still

# ------------------------------------------------------------------ the climb path on the hill (world = screen at zoom 1)
PATH = [(420, 965), (700, 705), (1000, 475), (1300, 285), (1470, 170)]
SEG = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:])]
PEAK = (1560, 105)
K = 0.47                                      # world scale: zoom 2.1 -> Sisyphus ~700 px like other parts
PUSH_H = int(E.load("sis_push").height * 700 / E.load("sis_walk").height * 0.93 * K)
ROCK_H = int(PUSH_H * 0.74)
FALL_H = int(E.load("sis_fallen").height * PUSH_H / E.load("sis_push").height)


def on_path(s):
    """point and slope angle (deg, screen-up positive) at fraction s (0 = foot, 1 = peak)"""
    d = max(0.0, min(1.0, s)) * sum(SEG)
    for (a, b), L in zip(zip(PATH, PATH[1:]), SEG):
        if d <= L or L == SEG[-1]:
            u = min(1, d / L)
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), math.degrees(math.atan2(a[1] - b[1], b[0] - a[0]))
        d -= L


def zoom_on(img, z, cx, cy):
    if z <= 1.0001: return img
    cw, ch = E.W / z, E.H / z
    x = float(np.clip(cx - cw / 2, 0, E.W - cw)); y = float(np.clip(cy - ch / 2, 0, E.H - ch))
    return img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((E.W, E.H), Image.BICUBIC)


def put(c, name, h, pos, ang, f, seed, lift=0.0, rot_extra=0.0):
    """stand a cut-out on the slope: tilted with the hill, feet on the path point; rot_extra spins it in place"""
    im = E.scaled(name, int(h))
    tilt = ang * 0.55
    r = math.radians(tilt)
    cx = pos[0] - math.sin(r) * (im.height / 2 + lift)
    cy = pos[1] - math.cos(r) * (im.height / 2 + lift)
    E.paste(c, im, cx, cy, rot=tilt + rot_extra, seed=seed, f=f)


# ------------------------------------------------------------------ the climb: «خطوةٌ… ثم خطوة», heavy stepped rhythm
def climb_s(t):
    """rock position along the path. Each step is a short heavy shove, then a hold."""
    if t < T["aflatat"]:
        if t < T["yaqtarib"]:
            n, period, s0, s1, ta = 12, 0.75, 0.12, 0.55, T["khutwa"]
        else:
            n, period, s0, s1, ta = 8, 0.75, 0.62, 0.90, T["yaqtarib"]
        k = (t - ta) / period
        whole = math.floor(k); part = min(1.0, (k - whole) / 0.35)
        steps = min(n, whole + (1 - (1 - part) ** 3))
        return s0 + (s1 - s0) * steps / n if t >= ta else s0
    return 0.90


def rock_fall_s(t):
    """«أفلتت»: rolls down from 0.90 to the foot, accelerating, bouncing"""
    u = min(1.0, (t - T["aflatat"]) / (T["alqa"] - T["aflatat"]))
    return 0.90 * (1 - u ** 1.6) - 0.06 * u


def bounce(t):
    """vertical hop of the rock at each impact while it tumbles"""
    if not T["aflatat"] <= t < T["alqa"]: return 0.0
    k = (t - T["aflatat"]) / 0.62
    return 34 * abs(math.sin(math.pi * k)) * (1 - (t - T["aflatat"]) / (T["alqa"] - T["aflatat"]))


def world(t, f):
    c = E.image_bg("hill", f, pan=0.5, sat=0.95)
    # Sisyphus
    if t < T["aflatat"]:
        s = climb_s(t)
        rp, ang = on_path(s)
        gap = (E.scaled("sis_push", PUSH_H).width * 0.5 + ROCK_H * 0.5 - 70) / sum(SEG)
        sp, _ = on_path(s - gap)
        put(c, "sis_push", PUSH_H, sp, ang, f, 3)
        put(c, "rock", ROCK_H, rp, ang, f, 8, lift=-14, rot_extra=-((s * 900) % 360))
    else:
        top, ang = on_path(0.83)
        if t < T["saqat"]:
            put(c, "sis_push", PUSH_H, top, ang, f, 3)
        elif t < T["ala2"]:
            # he goes down with it, tumbling
            u = (t - T["saqat"]) / (T["ala2"] - T["saqat"])
            p, a2 = on_path(0.83 * (1 - u ** 1.4) + 0.02 * u)
            put(c, "sis_push", PUSH_H, p, a2, f, 3, lift=20, rot_extra=-540 * u)
        else:
            foot, _ = on_path(0.0)
            E.paste(c, E.scaled("sis_fallen", FALL_H), foot[0] + 360, foot[1] - FALL_H / 2 + 10, rot=-4, seed=3, f=f)
        rs = rock_fall_s(t)
        rp, ang = on_path(rs)
        if rs < 0: rp = (rp[0] - 400 * (-rs), rp[1] + 30 * (-rs))
        roll = (0.90 - rs) * 2600
        put(c, "rock", ROCK_H, rp, ang, f, 8, lift=bounce(t), rot_extra=roll)
    return c


def camera(t):
    """(zoom, cx, cy)"""
    if t < T["yaqtarib"]:
        rp, _ = on_path(climb_s(t) - 0.04)
        return 2.1, rp[0], rp[1] - 110
    if t < T["ala"]:
        return 1.0, 960, 540
    if t < T["aflatat"]:
        rp, _ = on_path(climb_s(t))
        z = 1 + 1.3 * E.step(t, T["ala"], T["ala"] + 1.6)
        return z, (rp[0] + PEAK[0]) / 2, (rp[1] + PEAK[1]) / 2 + 40
    if t < T["ala2"]:
        z = 2.3 - 1.3 * E.step(t, T["aflatat"], T["aflatat"] + 0.8)
        return z, 1300, 260
    foot, _ = on_path(0.0)
    return 1.8, foot[0] + 260, foot[1] - 110


def scene_hill(t, f, c):
    if FREEZE[0] <= t < FREEZE[1]:                # the whole frame holds: no boil, no grain shift
        t, f = FREEZE[0], int(FREEZE[0] * E.FPS)
    z, cx, cy = camera(t)
    c.alpha_composite(zoom_on(world(t, f), round(z * 40) / 40, cx, cy))


# ------------------------------------------------------------------ «العرق»: close-up, paper drops of sweat
def drop(d, x, y, s):
    d.polygon([(x, y - 2.2 * s), (x - s, y), (x, y + s), (x + s, y)], fill=(244, 236, 220, 255), outline=(22, 30, 48, 255))
    d.ellipse((x - s, y - s * 0.2, x + s, y + s * 1.2), fill=(244, 236, 220, 255), outline=(22, 30, 48, 255), width=2)


def scene_sweat(t, f, c):
    bg = E.image_bg("hill", f, pan=0.35, blur=4, sat=0.8)
    c.alpha_composite(zoom_on(bg, 1.4, 700, 600))
    h = 960
    im = E.scaled("sis_strain", h); s = h / E.load("sis_strain").height
    cx, cy = 900, 560 + h * 0.02
    r = np.random.default_rng(f)
    shake = 5 if (f // 2) % 2 else -5
    E.paste(c, im, cx + r.normal(0, 3) + shake, cy + r.normal(0, 3), seed=3, f=f)
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, y0 = cx - im.width / 2, cy - im.height / 2
    rr = np.random.default_rng(9)
    for i in range(9):                                  # drops start on the brow/temple and run down
        sx, sy = rr.uniform(430, 560) * s, rr.uniform(170, 250) * s
        st = T["araq"] + 0.3 + rr.uniform(0, 3.8)
        u = t - st
        if 0 <= u < 1.6:
            drop(d, x0 + sx + 6 * u, y0 + sy + 380 * u * u + 30 * u, 13 + 6 * min(1, u * 2))
    c.alpha_composite(lay)


SCENES = [
    E.Scene(0, T["araq"], scene_hill, bg=None),
    E.Scene(T["araq"], T["yaqtarib"], scene_sweat, bg=None, rip=True),
    E.Scene(T["yaqtarib"], DUR, scene_hill, bg=None, rip=True),
]

LABELS = [
    E.Label("على بُعد ذراع", (), [T["ala"], T["bud"], T["dhira"]], hide=T["intasar"], x=640, y=150),
    E.Label("أفلتت", ("أفلتت",), [T["aflatat"]], hide=T["alqa"], x=520, y=150),
    E.Label("على وجهه", ("على", "وجهه"), [T["ala2"], T["wajhih"]], hide=DUR, x=1300, y=170),
]


def post(arr, t, f, idx):
    # «أفلتت»: the label and the frame jolt on every impact of the rock
    if T["aflatat"] <= t < T["alqa"]:
        k = (t - T["aflatat"]) / 0.62
        if (k % 1) < 0.17 and k >= 0.5:
            a = int(10 * (1 - (t - T["aflatat"]) / (T["alqa"] - T["aflatat"]))) + 3
            arr = np.roll(arr, (a if f % 2 else -a, a), axis=(1, 0))
    # it comes to rest at the foot: one heavy thud
    for tt, a in ((T["alqa"], 12), (T["ala2"], 9)):
        k = int(math.floor((t - tt) * E.FPS + 1e-6))
        if 0 <= k < 3: arr = np.roll(arr, ((a, -a, a // 2)[k], 0), axis=(1, 0))
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys4"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
