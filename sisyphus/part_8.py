"""بصيرة · فيديو سيزيف · الجزء ٨: «الدماغ يتذكّر» (3:30–4:00). Collage on grid paper: red threads tie the habit to a place, a time, a feeling."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import basira_engine as E
import part_6 as P6                                     # grid paper

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames8"); os.makedirs(OUT, exist_ok=True)
grid_bg = P6.grid_bg

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(fidyo=0.0, laysa=2.6, ladha=3.0, bal=3.5, raghba=4.0, makan=10.0, waqt=11.5, shuur=13.0,
         tamurr=15.0, malal=17.2, tashtail=19.0, qimma=22.0, back=23.4, damaghak=26.0, yatadhakkar=26.6)
_tj = os.path.join(HERE, "proj", "times_8.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
CUT1 = T["raghba"] - 0.3                                # Tantalus tears away just before «رغبة»
DUR = T["yatadhakkar"] + 3.0


# ------------------------------------------------------------------ 1. «فيديو الدوبامين»: Tantalus in the corner, the fruit pulls away
S_T = 0.68                                              # same scale for both pieces keeps them matched


@functools.lru_cache(None)
def tant(i):
    im = E.pieces("tantalus_reach")[i]
    return im.resize((int(im.width * S_T), int(im.height * S_T)), Image.LANCZOS)


def scene_tantalus(t, f, c):
    c.alpha_composite(grid_bg(f))
    rise = E.step(t, 0.0, 0.6)
    reach = E.step(t, 1.0, 2.6)
    away = E.step(t, 1.2, 2.8)
    E.paste(c, tant(1), 1058 + 150 * away, 634 - 70 * away, rot=-8 * away, seed=11, f=f)
    E.paste(c, tant(0), 500 + 40 * reach, 1300 - 500 * rise - 25 * reach, seed=12, f=f)


# ------------------------------------------------------------------ 2. the brain and its three threads
BRAIN = (960, 610); BRAIN_H = 460
PHOTOS = [  # name, height, centre, pin on the photo, anchor on the brain, time, rotation
    ("street", 330, (1560, 380), (1420, 400), (1150, 520), T["makan"], 3),
    ("wall_clock", 290, (1580, 830), (1450, 800), (1160, 700), T["waqt"], -4),
    ("bored_man", 380, (370, 620), (500, 690), (760, 600), T["shuur"], -3),
]
GROW = 0.6                                              # seconds for a thread to stretch out


def curve(a, b, n=40, sag=70):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag
    return [((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * mx + u * u * b[0],
             (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * my + u * u * b[1]) for u in np.linspace(0, 1, n)]


def glow_level(t):
    """0 before «لتشتعل», ramps on, stays lit; beats on «دماغك يتذكّر»"""
    if t < T["tashtail"]: return 0.0
    g = E.step(t, T["tashtail"], T["tashtail"] + 0.6)
    if t >= T["damaghak"]:
        k = int((t - T["damaghak"]) * E.FPS)
        g = (1.0, 0.45, 0.8, 0.45)[k // 2 % 4] if k < 40 else 0.8
    return g


def pin(d, p):
    x, y = p
    d.ellipse((x - 13, y - 13, x + 13, y + 13), fill=E.CREAM + (255,))
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=E.BRICK + (255,))
    d.ellipse((x - 4, y - 6, x + 1, y - 1), fill=(250, 220, 200, 255))


def spark_pos(t, i):
    """a bright bead running from a photo into the brain («تمرّ بالمكان», «بالملل»)"""
    for key, j in (("tamurr", 0), ("malal", 2)):
        u = (t - T[key]) / 0.8
        if j == i and 0 <= u < 1: return 1 - u
    return None


def brain_board(t, f):
    c = grid_bg(f)
    g = glow_level(t)
    if g > 0:
        r = 330 + 40 * g
        c.alpha_composite(E.glow_spot((BRAIN[0] - r, BRAIN[1] - r * 0.8, BRAIN[0] + r, BRAIN[1] + r * 0.8),
                                      color=(255, 200, 110), alpha=int(150 * g), blur=70))
    # the photos, each popping in when its thread arrives
    for i, (name, h, ctr, p, a, t0, rot) in enumerate(PHOTOS):
        ta = t0 + GROW
        if t < ta - 0.05: continue
        k = int((t - ta + 0.05) * E.FPS)
        s = {0: 0.6, 1: 1.08, 2: 0.97}.get(k, 1.0)
        jolt = 0
        for key, j in (("tamurr", 0), ("malal", 2)):
            if j == i and 0 <= t - (T[key] + 0.8) < 0.17: s, jolt = 1.06, 6
        E.paste(c, E.scaled(name, int(h * s)), ctr[0], ctr[1] + jolt, rot=rot, seed=20 + i, f=f)
    # the brain: pops in on «رغبة»
    if t >= T["raghba"] - 0.05:
        k = int((t - T["raghba"] + 0.05) * E.FPS)
        s = {0: 0.6, 1: 1.08, 2: 0.97}.get(k, 1.0)
        if g > 0 and t >= T["damaghak"]: s = 1.0 + 0.03 * (g - 0.45)
        E.paste(c, E.scaled("brain", int(BRAIN_H * s)), BRAIN[0], BRAIN[1], seed=19, f=f)
    # the threads on top, pinned at both ends
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    glow = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    for i, (name, h, ctr, p, a, t0, rot) in enumerate(PHOTOS):
        u = E.step(t, t0, t0 + GROW)
        if u <= 0: continue
        r = np.random.default_rng(i * 10 + (f // 2) % 3)
        pts = curve(a, p)
        pts = [(x + r.normal(0, 0.8), y + r.normal(0, 0.8)) for x, y in pts[:max(2, int(len(pts) * u))]]
        if g > 0: gd.line(pts, fill=(255, 214, 120, int(230 * g)), width=int(26 + 14 * g), joint="curve")
        d.line([(x + 4, y + 6) for x, y in pts], fill=(5, 8, 16, 90), width=8, joint="curve")
        d.line(pts, fill=(int(178 + 60 * g), int(62 + 60 * g), int(42 + 30 * g), 255), width=int(7 + 3 * g), joint="curve")
        pin(d, a)
        if u >= 1: pin(d, p)
        sp = spark_pos(t, i)
        if sp is not None:
            x, y = curve(a, p)[int(sp * 39)]
            gd.ellipse((x - 40, y - 40, x + 40, y + 40), fill=(255, 230, 150, 240))
            d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(255, 250, 230, 255))
    c.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))
    c.alpha_composite(lay)
    return c


def first_frame(t, t0): return int((t - t0) * E.FPS) == 0


def scene_brain(t, f, c):
    img = brain_board(t, f)
    c.alpha_composite(E.glitch(img, f) if first_frame(t, T["back"]) else img)


# ------------------------------------------------------------------ 3. «قرب القمة»: a short flash of the rock slipping off the hill
def scene_hill(t, f, c):
    bg = E.image_bg("hill", f, pan=0.5, sat=0.95)
    u = E.step(t, T["qimma"] + 0.15, T["back"]) ** 1.4
    u = round(u * 16) / 16
    E.paste(bg, E.scaled("rock", 260), 1460 - 980 * u, 520 + 300 * u, rot=-640 * u, seed=8, f=f)
    c.alpha_composite(E.glitch(bg, f) if first_frame(t, T["qimma"]) else bg)


SCENES = [
    E.Scene(0, CUT1, scene_tantalus, bg=None),
    E.Scene(CUT1, T["qimma"], scene_brain, bg=None, rip=True),
    E.Scene(T["qimma"], T["back"], scene_hill, bg=None, rip=False),
    E.Scene(T["back"], DUR, scene_brain, bg=None, rip=False),
]

LABELS = [
    E.Label("ليس لذّة بل رغبة", ("رغبة",), [T["laysa"], T["ladha"], T["bal"], T["raghba"]], hide=T["makan"] - 0.2, y=150),
    E.Label("دماغك يتذكّر", ("دماغك", "يتذكّر"), [T["damaghak"], T["yatadhakkar"]], hide=DUR + 1, y=150),
]


def post(arr, t, f, idx):
    if T["back"] <= t < T["damaghak"]: return arr              # quiet beat after the flash
    if t >= T["damaghak"]:                                     # warm beat of the whole page with the threads
        g = glow_level(t)
        arr = arr * (0.96 + 0.06 * g)
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys8"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
