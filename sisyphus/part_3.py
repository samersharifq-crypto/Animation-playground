"""بصيرة · فيديو سيزيف · الجزء ٣: «العقاب» (1:00–1:30)."""
import sys, os, json, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "frames3"); os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates)
T = dict(lakin=0.0, maat=3.0, zeus=5.0, bilnar=8.0, wala=9.5, sakhra=11.5, watall=13.0,
         hatta=16.0, alqimma=16.5, alaysa=19.0, fawada=25.0, yadfa=27.5)
_tj = os.path.join(HERE, "proj", "times_3.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["yadfa"] + 2.6
VOID = T["maat"] + 0.5                       # tear into the empty navy

FEET = 1000
SIS_H = 700
SIS_X = 430
ROCK_H, ROCK_X = 520, 860
PUSH_H = int(round(E.load("sis_push").height * SIS_H / E.load("sis_walk").height * 0.93))
ZEUS_X = 1430
if not os.path.exists(os.path.join(E.ROOT, "cut", "zeus_l.png")):
    ImageOps.mirror(E.load("zeus")).save(os.path.join(E.ROOT, "cut", "zeus_l.png"))


def bottom_paste(c, name, h, x, feet, seed, f, extra=0.0, rot=0.0, alpha=1.0):
    im = E.scaled(name, int(h))
    if extra:
        r = np.random.default_rng(f * 13 + seed); x += r.normal(0, extra); feet += r.normal(0, extra)
    E.paste(c, im, x, feet - im.height / 2, rot=rot, alpha=alpha, seed=seed, f=f)


def darken(img, k):
    if k <= 0: return img
    a = np.asarray(img.convert("RGB")).astype(float) * (1 - k)
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")


def zoom_on(img, z, cx, cy):
    if z <= 1.0001: return img
    cw, ch = E.W / z, E.H / z
    x = float(np.clip(cx - cw / 2, 0, E.W - cw)); y = float(np.clip(cy - ch / 2, 0, E.H - ch))
    return img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((E.W, E.H), Image.BICUBIC)


def crown(name, h, x, feet):
    """screen point just above the top of a figure's head"""
    im = E.scaled(name, h); a = np.asarray(im.getchannel("A")) > 0
    cx = im.width // 2; col = a[:, cx - 40:cx + 40].any(1); top = np.argmax(col)
    return x, feet - im.height + top - 10


# ------------------------------------------------------------------ 1. the laugh dies
TH_H, TH_X = 860, 960


def scene_throne(t, f, c):
    fade = E.step(t, 0, T["maat"])                                   # Corinth goes pale
    bg = E.image_bg("corinth", f, pan=0.4, blur=2.5, sat=0.85 - 0.55 * fade)
    c.alpha_composite(darken(bg, 0.2 + 0.25 * fade))
    s = TH_H / E.load("sis_throne").height
    im = E.scaled("sis_throne", TH_H)
    x0, y0 = TH_X - im.width / 2, FEET + 20 - im.height
    cup0 = (x0 + 100 * s, y0 + 58 * s)
    if t < T["maat"]:
        bottom_paste(c, "sis_throne", TH_H, TH_X, FEET + 20, 3, f)
        E.paste(c, E.scaled("cup", int(E.load("cup").height * s)), *cup0, seed=12, f=f)
    else:
        # «مات»: the king is gone; only the cup is left, falling and rolling
        u = min(1.0, (t - T["maat"]) / 0.45)
        y = cup0[1] + (FEET - 20 - cup0[1]) * u * u
        bounce = 0 if u < 1 else -18 * math.exp(-(t - T["maat"] - 0.45) * 8)
        E.paste(c, E.scaled("cup", int(E.load("cup").height * s)), cup0[0] - 60 * u, y + bounce,
                rot=120 * u, seed=12, f=f)


# ------------------------------------------------------------------ 2. judgement in the void
def flames(c, t, f, cx, cy):
    """torn orange paper flames behind Zeus, flaring then dying"""
    k = (t - T["bilnar"]) / 0.9
    if not 0 <= k < 1: return
    a = math.sin(math.pi * k)
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = np.random.default_rng(f // 2 + 3)
    for i in range(11):
        bx = cx - 420 + i * 84 + r.normal(0, 20); h = (200 + r.uniform(0, 260) * (1 - abs(i - 5) / 6)) * a
        pts = E.torn_poly([(bx - 55, cy + 360), (bx - 20 + r.normal(0, 25), cy + 360 - h * 0.55), (bx + r.normal(0, 40), cy + 360 - h), (bx + 25, cy + 360 - h * 0.5), (bx + 55, cy + 360)], f, 90 + i, 10)
        d.polygon(pts, fill=(226, 110, 52, int(230 * a)))
        d.polygon(E.torn_poly([(bx - 40, cy + 360), (bx, cy + 360 - h * 0.6), (bx + 40, cy + 360)], f, 120 + i, 6),
                  fill=(250, 196, 90, int(240 * a)))
    c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2.5)))
    c.alpha_composite(E.glow_spot((cx - 600, cy - 300, cx + 600, cy + 500), color=(255, 150, 60), alpha=int(70 * a), blur=120))


def chain_moment(c, t, f):
    """«ولا بالسلاسل»: a chain appears between them, then tears in two and is gone"""
    t0, t1 = T["wala"], T["wala"] + 0.55
    if t < t0 or t > t1 + 0.6: return
    ch = E.scaled("chain", 200)
    cx, cy = 900, 520
    if t < t1:
        E.paste(c, ch, cx, cy, rot=-4, seed=24, f=f); return
    u = (t - t1) / 0.6
    w = ch.width // 2
    for i, sgn in enumerate((-1, 1)):
        part = ch.crop((i * w, 0, (i + 1) * w, ch.height))
        E.paste(c, part, cx + sgn * (w / 2 + 260 * u), cy + 500 * u * u, rot=sgn * 80 * u,
                alpha=max(0.0, 1 - u), seed=25 + i, f=f)


def rock_fall(c, t, f):
    if t < T["sakhra"]: return
    u = min(1.0, (t - T["sakhra"]) / 0.35)
    bottom_paste(c, "rock", ROCK_H, ROCK_X, -ROCK_H + (FEET + 20 + ROCK_H) * u * u, 8, f, rot=-30 * (1 - u))


def judgement(t, f, c):
    if t >= T["zeus"]:
        k = E.step(t, T["zeus"] + 0.35, T["zeus"] + 1.0)
        flames(c, t, f, ZEUS_X, 470)
        bottom_paste(c, "zeus_l", 860, ZEUS_X, -860 + (FEET - 60 + 860) * k, 6, f)
    bottom_paste(c, "sis_walk", SIS_H, SIS_X, FEET, 3, f)
    chain_moment(c, t, f)
    rock_fall(c, t, f)


def scene_void(t, f, c):
    judgement(t, f, c)


# ------------------------------------------------------------------ 3. the hill
PEAK = (1615, 115)


def hill_world(t, f, rise=1.0):
    bg = darken(E.image_bg("hill", f, pan=0.5, sat=0.95), 0.08)
    if rise < 1:                                      # the hill rises out of the bottom of the frame
        base = E.paper_bg(f)
        base.alpha_composite(bg, (0, int(E.H * (1 - rise))))
        bg = base
    bottom_paste(bg, "sis_walk", SIS_H, SIS_X, FEET, 3, f)
    bottom_paste(bg, "rock", ROCK_H, ROCK_X, FEET + 20, 8, f)
    return bg


def scene_hill(t, f, c):
    rise = round(E.step(t, T["watall"], T["watall"] + 1.4) * 14) / 14
    w = hill_world(t, f, rise)
    z = 1 + 1.0 * E.step(t, T["hatta"], T["alaysa"] - 0.3)            # slow climb of the camera to the peak
    c.alpha_composite(zoom_on(w, round(z * 40) / 40, PEAK[0], PEAK[1] + 120))


def scene_look(t, f, c):
    """«أليس كذلك»: down at the foot, Sisyphus looks up at the summit"""
    w = hill_world(t, f)
    z = 1.75 + 0.15 * E.step(t, T["alaysa"], T["fawada"])
    c.alpha_composite(zoom_on(w, round(z * 40) / 40, SIS_X + 240, FEET - SIS_H * 0.62))


# ------------------------------------------------------------------ 4. the first push
def scene_push(t, f, c):
    w = darken(E.image_bg("hill", f, pan=0.5, sat=0.95), 0.08)
    shove = 40 * E.step(t, T["yadfa"], T["yadfa"] + 0.5)
    reach = 30 * (1 - E.step(t, T["fawada"], T["fawada"] + 0.8))      # he steps up and lays his hands on it
    rock_x = 1010 + shove
    im = E.scaled("sis_push", PUSH_H)
    px = rock_x - E.scaled("rock", ROCK_H).width / 2 - im.width / 2 + 215 - reach
    strain = 4 if t >= T["yadfa"] else 0
    bottom_paste(w, "sis_push", PUSH_H, px, FEET + 10, 3, f, extra=strain)
    bottom_paste(w, "rock", ROCK_H, rock_x, FEET + 20, 8, f, rot=-6 * shove / 40)
    z = 1.12 + 0.06 * E.step(t, T["fawada"], DUR)
    c.alpha_composite(zoom_on(w, round(z * 40) / 40, 760, 640))


SCENES = [
    E.Scene(0, VOID, scene_throne, bg=None),
    E.Scene(VOID, T["watall"], scene_void, rip=True),
    E.Scene(T["watall"], T["alaysa"], scene_hill, bg=None, rip=False),
    E.Scene(T["alaysa"], T["fawada"], scene_look, bg=None, rip=True),
    E.Scene(T["fawada"], DUR, scene_push, bg=None, rip=True),
]

LABELS = [
    E.Label("زيوس", ("زيوس",), [T["zeus"]], hide=T["bilnar"], x=ZEUS_X - 520, y=140),
    E.Label("صخرة", ("صخرة",), [T["sakhra"]], hide=T["watall"], x=ROCK_X + 420, y=150),
    E.Label("حتى القمة", (), [T["hatta"], T["alqimma"]], hide=T["alaysa"], x=620, y=150),
]

TIP = crown("sis_walk", SIS_H, SIS_X, FEET)


def post(arr, t, f, idx):
    # «زيوس»: the world drains to dark navy, lightning above Sisyphus' head
    if T["zeus"] <= t < T["watall"]:
        arr = E.drain(arr, E.step(t, T["zeus"], T["zeus"] + 0.75) * 0.3)
        arr = E.lightning(arr, t, T["zeus"], TIP)
    # the rock lands: heavy shake
    k = int(math.floor((t - T["sakhra"] - 0.35) * E.FPS + 1e-6))
    if 0 <= k < 4:
        a = (14, -12, 8, -5)[k]
        arr = np.roll(arr, (a, -a), axis=(1, 0))
    # the first push: a small jolt
    k = int(math.floor((t - T["yadfa"]) * E.FPS + 1e-6))
    if k in (0, 1): arr = np.roll(arr, (6 if k == 0 else -6), axis=1)
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys3"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
