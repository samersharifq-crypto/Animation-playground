"""بصيرة · فيديو سيزيف · الجزء ٦: «اسمُ الصخرة» (2:30–3:00). From here the world turns to collage on grid paper."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "frames6"); os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates)
T = dict(sijara=0.6, shasha=2.5, aada=4.5, intikasa=9.0, fashilna=12.5, duafa=14.5, lan=16.5,
         ilm=20.0, tariqa=25.0, mukhtalifa=25.6, tamaman=26.2)
_tj = os.path.join(HERE, "proj", "times_6.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["tamaman"] + 2.4
LETGO = T["aada"] + 2.4
LENS_T0 = T["tamaman"] + 0.5


def zoom_on(img, z, cx, cy):
    if z <= 1.0001: return img
    cw, ch = E.W / z, E.H / z
    x = float(np.clip(cx - cw / 2, 0, E.W - cw)); y = float(np.clip(cy - ch / 2, 0, E.H - ch))
    return img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((E.W, E.H), Image.BICUBIC)


# ------------------------------------------------------------------ 1. the bridge: the rock becomes our rocks
FLASH = 0.55
SWAPS = [(T["sijara"], "pack"), (T["shasha"], "phone")]
PHONE = None


def swap_at(t):
    for t0, what in SWAPS:
        if t0 <= t < t0 + FLASH: return what, int((t - t0) * E.FPS) == 0
    return None, False


def scene_bridge(t, f, c):
    global PHONE
    bg = E.image_bg("hill", f, pan=0.5, sat=0.95)
    u = round(min(1, t / T["aada"]) * 24) / 24
    x, y = 1520 - 1000 * u, 560 + 240 * u
    what, first = swap_at(t)
    if what == "pack":
        E.paste(bg, E.scaled("cigarette_pack", 430), x, y - 40, rot=-8, seed=31, f=f)
    elif what == "phone":
        if PHONE is None: PHONE = E.make_phone(400)
        bg.alpha_composite(E.glow_spot((x - 260, y - 300, x + 260, y + 220), alpha=70, blur=90))
        E.paste(bg, PHONE, x, y - 30, rot=-6, shadow=False, seed=32, f=f)
    else:
        E.paste(bg, E.scaled("rock", 300), x, y, rot=-720 * u, seed=8, f=f)
    c.alpha_composite(E.glitch(bg, f) if first or (what is None and any(int((t - t0 - FLASH) * E.FPS) == 0 for t0, _ in SWAPS)) else bg)


HAND_H = 380


def scene_hand(t, f, c):
    """«أو عادةً…»: a hand holds a small rock over the hill, then lets it go"""
    c.alpha_composite(zoom_on(E.image_bg("hill", f, pan=0.5, sat=0.9, blur=1.5), 1.25, 900, 640))
    k = E.step(t, T["aada"], T["aada"] + 0.7)
    lift = 30 * E.step(t, LETGO, LETGO + 0.4)
    hx, hy = -500 + (560 + 500) * k, 330 - lift
    tip = (hx + 330, hy + 115)
    if t < LETGO:
        rx, ry, rot = tip[0] - 10, tip[1] + 75, 0
    else:
        u = t - LETGO
        rx, ry, rot = tip[0] - 10 - 120 * u, tip[1] + 75 + 1100 * u * u, 260 * u
    if ry < E.H + 200:
        E.paste(c, E.scaled("rock", 230), rx, ry, rot=rot, seed=8, f=f)
    E.paste(c, E.scaled("hand_letgo", HAND_H), hx, hy, seed=33, f=f)


# ------------------------------------------------------------------ 2. the collage world: grid paper
GRID = (246, 242, 232)


@functools.lru_cache(None)
def _grid_lines():
    lay = Image.new("RGBA", (E.W + 80, E.H + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i, x in enumerate(range(0, E.W + 80, 40)):
        d.line([(x, 0), (x, E.H + 80)], fill=(120, 160, 190, 120 if i % 5 == 0 else 55), width=2 if i % 5 == 0 else 1)
    for i, y in enumerate(range(0, E.H + 80, 40)):
        d.line([(0, y), (E.W + 80, y)], fill=(120, 160, 190, 120 if i % 5 == 0 else 55), width=2 if i % 5 == 0 else 1)
    return lay


def grid_bg(f):
    r0 = np.random.default_rng(f); ox, oy = r0.integers(0, 12), r0.integers(0, 12)
    arr = (np.array(GRID, float)[None, None, :] + E.TEX[oy:oy + E.H, ox:ox + E.W][..., None]) * (0.8 + 0.2 * E.VIG)
    c = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    r = np.random.default_rng(f // 2)
    c.alpha_composite(_grid_lines().crop((int(r.integers(0, 4)), int(r.integers(0, 4)), int(r.integers(0, 4)) + E.W, 0 + E.H)))
    return c


STAMPS = [("فاشل", "fashilna", (540, 380), -9), ("ضعيف", "duafa", (1250, 340), 7), ("لن يتغيّر", "lan", (880, 760), -4)]


@functools.lru_cache(None)
def impression(text, seed):
    """red rubber-stamp ink: double border, uneven ink, a few gaps"""
    font = ImageFont.truetype(E.FONT, 120)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = tmp.textlength(text, font=font, direction="rtl", language="ar")
    w, h = int(tw + 120), 230
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = E.BRICK + (235,)
    d.rounded_rectangle((8, 8, w - 8, h - 8), 22, outline=col, width=10)
    d.rounded_rectangle((26, 26, w - 26, h - 26), 14, outline=col, width=4)
    d.text((60, 28), text, font=font, fill=col, direction="rtl", language="ar")
    a = np.asarray(im).copy()
    r = np.random.default_rng(seed)
    blot = r.random(a.shape[:2])
    from scipy import ndimage
    blot = ndimage.gaussian_filter(blot, 3)
    a[..., 3] = (a[..., 3] * np.clip((blot - 0.40) * 6, 0.25, 1)).astype(np.uint8)
    return Image.fromarray(a)


def stamps(c, t, f):
    for i, (text, key, (x, y), rot) in enumerate(STAMPS):
        t0 = T[key]
        if t < t0 - 0.3: continue
        # the impression (after impact), falling off the page when the microscope arrives
        if t >= t0:
            fall = max(0.0, t - (T["ilm"] + 0.25 * i))
            if fall < 1.4:
                E.paste(c, impression(text, i), x - 30 * fall, y + 1200 * fall * fall, rot=rot + 70 * fall * (1 if i % 2 else -1),
                        shadow=False, seed=40 + i, f=f)
        # the stamp comes down, hits, lifts away
        u = t - t0
        if -0.3 <= u < 0.45:
            if u < 0: yy = y - 120 - 700 * (-u / 0.3) ** 2
            elif u < 0.12: yy = y - 120
            else: yy = y - 120 - 900 * ((u - 0.12) / 0.33) ** 2
            E.paste(c, E.scaled("stamp", 420), x + 40, yy - 90, rot=rot, seed=50 + i, f=f)


MIC_H = 820
MIC_X, MIC_Y = 1450, 560


def lens_point():
    im = E.scaled("microscope", MIC_H); s = MIC_H / E.load("microscope").height
    return MIC_X - im.width / 2 + 247 * s, MIC_Y - im.height / 2 + 410 * s


LENS = lens_point()


def collage(t, f):
    c = grid_bg(f)
    stamps(c, t, f)
    if t >= T["ilm"]:
        k = E.step(t, T["ilm"], T["ilm"] + 1.0)
        E.paste(c, E.scaled("microscope", MIC_H), 2400 - (2400 - MIC_X) * k, MIC_Y, seed=60, f=f)
    return c


def scene_collage(t, f, c):
    img = collage(t, f)
    if t >= T["tariqa"]:
        z = 1 + 1.6 * E.step(t, T["tariqa"], LENS_T0 + 1.0)
        img = zoom_on(img, round(z * 40) / 40, LENS[0], LENS[1])
    if t >= LENS_T0:
        # the lens grows until it fills the screen: the way into part 7
        u = min(1.0, (t - LENS_T0) / 1.3) ** 2
        R = 40 + 1300 * u
        d = ImageDraw.Draw(img)
        z = 1 + 1.6 * E.step(t, T["tariqa"], LENS_T0 + 1.0)
        cx, cy = E.W / 2, E.H / 2 + 60 * (1 - u)
        d.ellipse((cx - R - 26, cy - R - 26, cx + R + 26, cy + R + 26), fill=(176, 146, 92, 255))
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(14, 18, 28, 255))
        d.ellipse((cx - R * 0.55, cy - R * 0.75, cx - R * 0.2, cy - R * 0.45), fill=(60, 70, 90, 255))
    c.alpha_composite(img)


SCENES = [
    E.Scene(0, T["aada"], scene_bridge, bg=None),
    E.Scene(T["aada"], T["intikasa"], scene_hand, bg=None, rip=True),
    E.Scene(T["intikasa"], DUR, scene_collage, bg=None, rip=True),
]

LABELS = [
    E.Label("الانتكاسة", ("الانتكاسة",), [T["intikasa"]], hide=T["fashilna"] - 0.2, y=540, size=150),
    E.Label("بطريقة مختلفة تماماً", (), [T["tariqa"], T["mukhtalifa"], T["tamaman"]], hide=LENS_T0 + 0.6, x=760, y=150),
]


def post(arr, t, f, idx):
    # each stamp hit: a short jolt
    for _, key, _, _ in STAMPS:
        k = int(math.floor((t - T[key]) * E.FPS + 1e-6))
        if k in (0, 1): arr = np.roll(arr, (0, 10 if k == 0 else -6), axis=(1, 0))
    if t >= LENS_T0 + 1.4: arr = arr * 0
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys6"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
