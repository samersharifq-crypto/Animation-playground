"""بصيرة · فيديو سيزيف · الجزء ٥: «إلى الأبد» (2:00–2:30)."""
import sys, os, json, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import basira_engine as E
import part_4 as P4                                   # same hill, same path, same scale

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames5"); os.makedirs(OUT, exist_ok=True)
put, zoom_on, PATH, SEG = P4.put, P4.zoom_on, P4.PATH, P4.SEG
PUSH_H, ROCK_H, FALL_H = P4.PUSH_H, P4.ROCK_H, P4.FALL_H
WALK_H = int(700 * P4.K)

# ------------------------------------------------------------------ timing (video seconds, estimates)
T = dict(nahad=0.0, min_jadid=4.5, wafi=6.0, iqab=12.0, awda=15.0, ila=15.4, bidaya=15.8,
         akhbirni=19.0, hadhihi=23.0, akhir=23.4, marra=23.8, aadat=27.0, sakhra=27.5)
_tj = os.path.join(HERE, "proj", "times_5.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["aadat"] + 2.3
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice
BLACK = T["aadat"] + 1.6                               # the rock fills the screen -> black
STILL = (T["iqab"], T["awda"])


def on_path(s):
    """like part 4, but continues below the foot along the first segment"""
    if s >= 0: return P4.on_path(s)
    (a, b), L = (PATH[0], PATH[1]), SEG[0]
    d = s * sum(SEG)
    return (a[0] + (b[0] - a[0]) * d / L, a[1] + (b[1] - a[1]) * d / L), P4.on_path(0)[1]


GAP = (E.scaled("sis_push", PUSH_H).width * 0.5 + ROCK_H * 0.5 - 70) / sum(SEG)
ROCK0 = 0.02                                          # rock resting at the foot


def pushing(c, f, s, spin=True):
    rp, ang = on_path(s); sp, _ = on_path(s - GAP)
    put(c, "sis_push", PUSH_H, sp, ang, f, 3)
    put(c, "rock", ROCK_H, rp, ang, f, 8, lift=-14, rot_extra=-((s * 900) % 360) if spin else 0)


def rock_at(c, f, s, roll=0.0, lift=-14):
    rp, ang = on_path(s); put(c, "rock", ROCK_H, rp, ang, f, 8, lift=lift, rot_extra=roll)


# ------------------------------------------------------------------ the cycles: faster and faster
CYCLES = [(T["wafi"], 2.4), (T["wafi"] + 2.4, 1.9), (T["wafi"] + 4.3, 1.45)]


def cycle_state(t):
    for t0, d in CYCLES:
        if t0 <= t < t0 + d:
            u = (t - t0) / d
            if u < 0.62:                                  # up, in quick heavy steps
                k = u / 0.62; n = 6
                steps = min(n, math.floor(k * n) + min(1, (k * n % 1) / 0.4))
                return "up", ROCK0 + (0.86 - ROCK0) * steps / n
            v = (u - 0.62) / 0.38                         # it slips and rolls back down; he follows
            return "down", 0.86 - (0.86 - ROCK0) * v ** 1.4, v
    return None


def world(t, f):
    c = E.image_bg("hill", f, pan=0.5, sat=0.95)
    foot, _ = on_path(ROCK0)
    if t < T["min_jadid"]:
        # «نهض»: he gets up next to the rock, then walks round behind it
        rock_at(c, f, ROCK0)
        if t < T["nahad"] + 0.7:
            E.paste(c, E.scaled("sis_fallen", FALL_H), foot[0] + 360, foot[1] - FALL_H / 2 + 10, rot=-4, seed=3, f=f)
        else:
            k = P4.E.step(t, T["nahad"] + 0.9, T["min_jadid"] - 0.2)
            x = foot[0] + 330 - (330 + 250) * k
            bob = 0 if k in (0, 1) else (6 if f % 2 else 0)
            E.paste(c, E.scaled("sis_walk_l", WALK_H), x, foot[1] + 5 - WALK_H / 2 - bob, seed=3, f=f)
    elif t < T["wafi"]:
        pushing(c, f, ROCK0, spin=False)               # «من جديد»: hands on the rock
    elif t < T["iqab"]:
        st = cycle_state(t)
        if st is None or st[0] == "up":
            pushing(c, f, st[1] if st else ROCK0)
        else:
            _, s, v = st
            sp, _ = on_path(max(s + GAP * 0.9, (0.86 - GAP) * (1 - v) + (ROCK0 + GAP * 0.9) * v))
            put(c, "sis_walk_l", WALK_H, sp, 0, f, 3)          # he walks down after it
            rock_at(c, f, s, roll=(0.86 - s) * 2600, lift=-14 + 24 * abs(math.sin(v * 9)))
    else:
        rock_at(c, f, ROCK0)
        sp, _ = on_path(ROCK0 - GAP)
        put(c, "sis_walk", WALK_H, (sp[0] + 20, sp[1]), 0, f, 3)
    return c


def scene_hill(t, f, c):
    if STILL[0] <= t < STILL[1]:                      # «العقاب الحقيقي»: everything stands still
        t, f = STILL[0], int(STILL[0] * E.FPS)
    foot, _ = on_path(ROCK0)
    if t < T["wafi"]:
        z, cx, cy = 1.8, foot[0] + 150, foot[1] - 170
    elif t < T["iqab"]:
        z, cx, cy = 1.0, 960, 540
    else:
        z, cx, cy = 1.6 - 0.6 * P4.E.step(t, T["awda"], T["awda"] + 0.8), foot[0] + 220, foot[1] - 200
    c.alpha_composite(zoom_on(world(t, f), round(z * 40) / 40, cx, cy))
    if T["awda"] <= t < T["akhbirni"]:
        arrow(c, t, f)


# ------------------------------------------------------------------ «العودة إلى البداية»: a paper arrow circling the hill
def arrow(c, t, f):
    u = min(1.0, (t - T["awda"]) / 1.4)
    if u <= 0: return
    cx, cy, rx, ry = 1000, 560, 780, 360
    a0 = math.radians(200); a1 = a0 + math.radians(320) * u
    n = max(3, int(60 * u))
    pts = [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = np.random.default_rng(f // 2)
    jag = [(x + r.normal(0, 2), y + r.normal(0, 2)) for x, y in pts]
    d.line(jag, fill=E.INK + (255,), width=34, joint="curve")
    d.line(jag, fill=E.CREAM + (255,), width=24, joint="curve")
    d.line(jag, fill=E.BRICK + (255,), width=10, joint="curve")
    x, y = pts[-1]; ang = a1 + math.pi / 2
    tip = [(x + 46 * math.cos(ang), y + 46 * math.sin(ang)),
           (x + 30 * math.cos(ang + 2.3), y + 30 * math.sin(ang + 2.3)),
           (x + 30 * math.cos(ang - 2.3), y + 30 * math.sin(ang - 2.3))]
    d.polygon(tip, fill=E.BRICK + (255,), outline=E.CREAM + (255,), width=6)
    sh = Image.new("RGBA", lay.size, (5, 8, 16, 0)); sh.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.5)))
    c.alpha_composite(sh, (8, 10)); c.alpha_composite(lay)


# ------------------------------------------------------------------ «أخبرني أنت»: close on his face
def scene_look(t, f, c):
    bg = E.image_bg("hill", f, pan=0.3, blur=4, sat=0.8)
    c.alpha_composite(zoom_on(bg, 1.4, 600, 750))
    z = 1 + 0.1 * P4.E.step(t, T["akhbirni"], T["hadhihi"])
    h = int(940 * z)
    E.paste(c, E.scaled("sis_look", h), 960, 560 + h * 0.04, seed=3, f=f)


# ------------------------------------------------------------------ «هذه آخر مرة»: hill <-> modern room
FLASHES = [(T["hadhihi"], T["hadhihi"] + 2 / E.FPS), (T["akhir"], T["akhir"] + 3 / E.FPS),
           (T["marra"], T["marra"] + 4 / E.FPS), (T["marra"] + 0.9, T["marra"] + 0.9 + 2 / E.FPS)]


def room(f):
    c = E.image_bg("room", f, pan=0.5, sat=1.0)
    c.alpha_composite(E.glow_spot((1380, 690, 1620, 860), alpha=60 + (20 if f % 2 else 0), blur=70))
    return c


def scene_flicker(t, f, c):
    if E.in_any(t, FLASHES):
        img = room(f); start = max(a for a, b in FLASHES if a <= t)
        if int((t - start) * E.FPS) == 0: img = E.glitch(img, f)
    else:
        foot, _ = on_path(ROCK0)
        img = zoom_on(world(T["iqab"] + 0.01, f), 1.3, foot[0] + 400, foot[1] - 260)
        if any(int((t - b) * E.FPS) == 0 for a, b in FLASHES): img = E.glitch(img, f)
    c.alpha_composite(img)


# ------------------------------------------------------------------ «عادت الصخرة»: it rolls at the camera
def scene_return(t, f, c):
    if t >= BLACK:
        c.alpha_composite(Image.new("RGBA", (E.W, E.H), (0, 0, 0, 255))); return
    c.alpha_composite(P4.darken(E.image_bg("hill", f, pan=0.5, sat=0.9), 0.25) if hasattr(P4, "darken") else E.image_bg("hill", f, pan=0.5))
    u = (t - T["aadat"]) / (BLACK - T["aadat"])
    u = round(u * 20) / 20
    h = int(260 + 2600 * u ** 2.2)
    x = 1350 - 390 * u; y = 330 + 400 * u + 60 * abs(math.sin(u * 14)) * (1 - u)
    E.paste(c, E.scaled("rock", h), x, y, rot=-700 * u, seed=8, f=f)


SCENES = [
    E.Scene(0, T["akhbirni"], scene_hill, bg=None),
    E.Scene(T["akhbirni"], T["hadhihi"], scene_look, bg=None, rip=True),
    E.Scene(T["hadhihi"], T["aadat"], scene_flicker, bg=None, rip=False),
    E.Scene(T["aadat"], DUR, scene_return, bg=None, rip=True),
]

LABELS = [
    E.Label("العودة إلى البداية", ("العودة", "إلى", "البداية"), [T["awda"], T["ila"], T["bidaya"]], hide=T["akhbirni"], x=960, y=120),
    E.Label("هذه آخر مرة", ("هذه", "آخر", "مرة"), [T["hadhihi"], T["akhir"], T["marra"]], hide=T["aadat"]),
]

AR = "٠١٢٣٤٥٦٧٨٩"


def ar(n): return "".join(AR[int(ch)] for ch in str(n))


def counter_value(t):
    if t < T["wafi"] or t >= T["iqab"]: return None
    n = sum(1 for t0, _ in CYCLES if t >= t0)
    fast0 = CYCLES[-1][0] + 0.5
    if t >= fast0:                                     # then it runs away: … ٩٩
        u = min(1.0, (t - fast0) / (T["iqab"] - 0.25 - fast0))
        n = 3 + int(96 * u ** 1.8)
    return n


def draw_counter(c, t, f):
    n = counter_value(t)
    if n is None: return
    im = E._strip(ar(n), (ar(n),), 1, 7, 96)
    prev = counter_value(t - 1 / E.FPS)
    s = 1.12 if prev != n else 1.0
    if s != 1: im = im.resize((int(im.width * s), int(im.height * s)))
    dx, dy, dr = E.jit(f, 61, 1.5, 0.4)
    E.paste(c, im, 1740 + dx, 140 + dy, rot=2 + dr)


def post(arr, t, f, idx):
    if T["wafi"] <= t < T["iqab"]:
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        draw_counter(im, t, f); arr = np.asarray(im.convert("RGB")).astype(float)
    if T["aadat"] <= t < BLACK:                        # the rock's weight shakes the camera harder and harder
        u = (t - T["aadat"]) / (BLACK - T["aadat"]); r = np.random.default_rng(f)
        a = int(4 + 18 * u)
        arr = np.roll(arr, (int(r.integers(-a, a + 1)), int(r.integers(-a, a + 1))), axis=(1, 0))
    if t >= BLACK: arr = arr * 0
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys5"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
