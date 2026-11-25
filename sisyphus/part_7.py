"""بصيرة · فيديو سيزيف · الجزء ٧: «لستَ وحدك» (3:00–3:30). Collage on grid paper."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import basira_engine as E
import part_6 as P6                                     # grid paper, stamp ink, zoom

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames7"); os.makedirs(OUT, exist_ok=True)
grid_bg, impression = P6.grid_bg, P6.impression

# ------------------------------------------------------------------ timing (video seconds, estimates)
T = dict(yaqul=0.5, arbain=3.5, wasittin=4.1, bilmia=4.7, daght=9.0, rabw=9.8, anta=16.0, fashil=16.5,
         la=20.0, tani=20.4, an=20.9, ilaj=21.3, fashal=21.9, tadil=26.0)
_tj = os.path.join(HERE, "proj", "times_7.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["tadil"] + 3.2
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice

BASE, FULL, BAR_W = 800, 640, 210                       # baseline y, px for 100 %, bar width
COLS = [  # x, low %, high %, icon, icon height, start time
    (520, 40, 60, "rock", 150, T["arbain"]),
    (960, 50, 70, "bp_gauge", 210, T["daght"]),
    (1400, 50, 70, "inhaler", 200, T["rabw"]),
]
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


@functools.lru_cache(None)
def font(size): return ImageFont.truetype(E.FONT, size)


def axis(c, f):
    d = ImageDraw.Draw(c)
    r = np.random.default_rng(f // 2)
    pts = [(260 + i * 40, BASE + r.normal(0, 1.5)) for i in range(37)]
    d.line(pts, fill=E.INK + (255,), width=6)


def bar(c, t, f, i, x, lo, hi, icon, ih, t0):
    """paper column rising to `hi` %, the 'lo..hi' range lighter, number on top, icon underneath"""
    if t < t0: return
    k = E.step(t, t0, t0 + 1.2)
    k = round(k * 12) / 12                                # stepped rise (stop-motion)
    top = BASE - FULL * hi / 100 * k
    lo_y = BASE - FULL * lo / 100 * min(1, k * hi / lo)
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = np.random.default_rng(i * 10 + (f // 2) % 3)
    def torn_rect(y0, y1, col):
        pts = [(x - BAR_W / 2 + r.normal(0, 2), y1)]
        pts += [(x - BAR_W / 2 + r.normal(0, 2.5), y) for y in np.linspace(y1, y0, 8)]
        pts += [(xx, y0 + r.normal(0, 3)) for xx in np.linspace(x - BAR_W / 2, x + BAR_W / 2, 10)]
        pts += [(x + BAR_W / 2 + r.normal(0, 2.5), y) for y in np.linspace(y0, y1, 8)]
        d.polygon(pts, fill=col)
    if BASE - top > 4:
        torn_rect(top, BASE, (226, 150, 128, 255))        # the range part (lighter)
        torn_rect(lo_y, BASE, E.BRICK + (255,))           # the solid part
        for yy in np.arange(top + 14, lo_y, 18):          # hatching on the range part
            d.line([(x - BAR_W / 2 + 8, yy), (x + BAR_W / 2 - 8, yy - 10)], fill=E.BRICK + (150,), width=3)
    sh = Image.new("RGBA", lay.size, (5, 8, 16, 0)); sh.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.4)))
    c.alpha_composite(sh, (8, 10)); c.alpha_composite(lay)
    if k >= 1:
        txt = f"{lo}–{hi}%".translate(AR)
        im = E._strip(txt, (), 1, 20 + i, 60)
        E.paste(c, im, x, top - 70, rot=-2 + i, seed=70 + i, f=f)
    ik = E.step(t, t0 - 0.1, t0 + 0.4)
    if ik > 0:
        E.paste(c, E.scaled(icon, int(ih * (0.6 + 0.4 * ik))), x, BASE + 30 + ih / 2, seed=80 + i, f=f)


def chart(t, f):
    c = grid_bg(f)
    axis(c, f)
    for i, col in enumerate(COLS): bar(c, t, f, i, *col)
    return c


# ------------------------------------------------------------------ «أنت فاشل»: the stamp comes at the patient and is struck out
STAMP_STOP = (1180, 190)


def failed_stamp(c, t, f):
    if t < T["anta"]: return
    # the doctor's stethoscope comes down beside the blood-pressure column
    E.drop_in(c, "stethoscope", 280, t, T["anta"], T["anta"] + 0.5, 1730, 170, f, seed=90)
    u = E.step(t, T["fashil"], T["fashil"] + 0.5)
    x = 2300 - (2300 - STAMP_STOP[0]) * u
    fall = max(0.0, t - (T["la"] - 0.4))
    if fall > 1.3: return
    y = STAMP_STOP[1] + 1100 * fall * fall
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0))
    im = impression("فاشل", 0)
    E.paste(lay, im, x, y, rot=-6 + 50 * fall, shadow=False, seed=91, f=f)
    s = min(1.0, max(0.0, (t - T["fashil"] - 0.7) / 0.4))        # the strike-through, drawn right to left
    if s > 0:
        d = ImageDraw.Draw(lay)
        x1, x0 = x + im.width / 2 + 20, x - im.width / 2 - 20
        d.line([(x1, y + 22), (x1 - (x1 - x0) * s, y - 18)], fill=E.INK + (255,), width=16)
    c.alpha_composite(lay)


# ------------------------------------------------------------------ «لا تعني»: one paper line levels the three columns
def level_line(c, t, f):
    if t < T["la"]: return
    u = E.step(t, T["la"], T["la"] + 0.8)
    y = BASE - FULL * 0.6
    x1 = 1620; x0 = x1 - (x1 - 300) * u
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pts = E.torn_poly([(x1, y), (x0, y)], f, 95, 3)
    d.line(pts, fill=E.INK + (255,), width=22); d.line(pts, fill=E.CREAM + (255,), width=12)
    c.alpha_composite(lay)


def scene_chart(t, f, c):
    img = chart(t, f)
    failed_stamp(img, t, f)
    level_line(img, t, f)
    c.alpha_composite(img)


# ------------------------------------------------------------------ «تعديلاً»: an old road map, the arrow turns and finds another road
PATH = [(1480, 740), (1260, 690), (1080, 640), (1000, 520), (980, 400), (820, 330), (560, 300), (420, 250)]


def scene_map(t, f, c):
    c.alpha_composite(grid_bg(f))
    E.paste(c, E.scaled("old_map", 800), 960, 560, rot=-2, seed=100, f=f)
    u = E.step(t, T["tadil"] + 0.4, T["tadil"] + 2.2)
    if u <= 0: return
    L = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(PATH, PATH[1:])]
    goal = sum(L) * u; pts = [PATH[0]]
    for (a, b), l in zip(zip(PATH, PATH[1:]), L):
        if goal >= l: pts.append(b); goal -= l
        else: pts.append((a[0] + (b[0] - a[0]) * goal / l, a[1] + (b[1] - a[1]) * goal / l)); break
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line(pts, fill=E.CREAM + (255,), width=30, joint="curve")
    d.line(pts, fill=E.BRICK + (255,), width=16, joint="curve")
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    ang = math.atan2(yb - ya, xb - xa)
    tip = [(xb + 40 * math.cos(ang), yb + 40 * math.sin(ang)),
           (xb + 30 * math.cos(ang + 2.4), yb + 30 * math.sin(ang + 2.4)),
           (xb + 30 * math.cos(ang - 2.4), yb + 30 * math.sin(ang - 2.4))]
    d.polygon(tip, fill=E.BRICK + (255,), outline=E.CREAM + (255,), width=6)
    # the old road it leaves: a short dashed stub that stops at a cross
    d.line([(1080, 640), (900, 610)], fill=E.INK + (200,), width=6)
    d.line([(885, 590), (915, 630)], fill=E.INK + (255,), width=8); d.line([(885, 630), (915, 590)], fill=E.INK + (255,), width=8)
    sh = Image.new("RGBA", lay.size, (5, 8, 16, 0)); sh.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.4)))
    c.alpha_composite(sh, (6, 8)); c.alpha_composite(lay)


SCENES = [
    E.Scene(0, T["tadil"], scene_chart, bg=None),
    E.Scene(T["tadil"], DUR, scene_map, bg=None, rip=True),
]

NIDA = "المعهد الوطني الأمريكي لأبحاث تعاطي المخدرات"
LABELS = [
    E.Label(NIDA, (), list(np.linspace(T["yaqul"], T["yaqul"] + 2.4, 7)), hide=T["arbain"] - 0.1, y=150, size=56),
    E.Label("أربعين وستين بالمئة", ("أربعين", "وستين", "بالمئة"), [T["arbain"], T["wasittin"], T["bilmia"]], hide=T["daght"] - 0.1, y=110),
    E.Label("لا تعني أن العلاج فشل", ("لا", "تعني", "أن", "العلاج", "فشل"),
            [T["la"], T["tani"], T["an"], T["ilaj"], T["fashal"]], hide=T["tadil"], y=110),
]


def post(arr, t, f, idx):
    k = int(math.floor((t - T["fashil"] - 0.5) * E.FPS + 1e-6))     # the stamp stops dead: a jolt
    if k in (0, 1): arr = np.roll(arr, (8 if k == 0 else -5), axis=1)
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys7"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
