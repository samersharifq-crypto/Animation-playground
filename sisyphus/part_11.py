"""بصيرة · فيديو سيزيف · الجزء ١١: «الأكتاف المنحنية» (5:00–5:30). Collage on grid paper:
a camera films 46 people in recovery; the body shows shame; the shame's shadow becomes the rock."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
import basira_engine as E
import part_6 as P6                                     # grid paper

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames11"); os.makedirs(OUT, exist_ok=True)
grid_bg = P6.grid_bg

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(am=0.6, sawwar=2.0, jamia=2.8, kulumbiya=3.2, britaniya=3.7, sana=4.1,
         sitta=4.6, arbain=5.1, mutaafin=5.7, kuhul=6.3, yatahaddathun=7.2,
         lam=9.6, ajsad=11.0, aktaf=12.6, munhaniya=13.4, sadr=14.4, munkamish=15.1,
         alamat=17.0, khizy=17.8, baad=19.6, ashhur=20.3, akthar=22.0, intikasan=22.6,
         akthar2=24.2, shurban=24.8, intakasu=26.2)
_tj = os.path.join(HERE, "proj", "times_11.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["intakasu"] + 2.6
CUT_CAM = T["ajsad"] - 0.4                              # the lab -> through the viewfinder
CUT_SHADOW = T["baad"] - 0.2                            # the viewfinder -> the shadow on the wall
DIM_T = T["khizy"]


# ------------------------------------------------------------------ 1. the lab: camera rolls in, 46 chairs tick into rows
CAM_H = 640; CAM = (400, 600)
ROWS = [(16, 470, 118), (15, 650, 136), (15, 850, 156)]  # chairs per row, y, height (back row smaller)
CHAIRS = []
for n, y, h in ROWS:
    sp = 72 * h / 136
    for j in range(n): CHAIRS.append((1830 - j * sp, y, h))
CHAIRS_T0, CHAIRS_T1 = T["sitta"] - 0.1, T["kuhul"] + 0.2


def chair_t(i):
    return CHAIRS_T0 + (CHAIRS_T1 - CHAIRS_T0) * (i / 45) ** 0.85   # ticks in, a little faster each time


def scene_lab(t, f, c):
    c.alpha_composite(grid_bg(f))
    k = E.step(t, 0.0, 1.0)
    E.paste(c, E.scaled("video_camera", CAM_H), CAM[0] - 700 * (1 - k), CAM[1], seed=31, f=f)
    if t >= T["sawwar"] and (int(t * 2) % 2 == 0):         # the red REC light blinks
        d = ImageDraw.Draw(c); x, y = CAM[0] + 52 - 700 * (1 - k), CAM[1] - 258
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(214, 40, 30, 255))
    for i, (x, y, h) in enumerate(CHAIRS):
        t0 = chair_t(i)
        if t < t0: break
        s = 1.25 if t - t0 < 0.09 else 1.0               # each chair taps down
        E.paste(c, E.scaled("chair", int(h * s)), x, y - (10 if t - t0 < 0.09 else 0), seed=200 + i, f=f,
                boil=(f // 2 + i) % 4 == 0)


# ------------------------------------------------------------------ 2. through the viewfinder: upright -> slumped
MAN_K = 1.22                                            # same scale for both photos so chair and feet stay put
MAN_FOOT = (1240, 1050)                                  # bottom-centre of the cut-out


def man_img(name):
    im = E.load(name)
    return E.scaled(name, int(im.height * MAN_K))


def paste_man(c, name, f, dx=0, dy=0, seed=71):
    im = man_img(name)
    E.paste(c, im, MAN_FOOT[0] + dx, MAN_FOOT[1] - im.height / 2 + dy, seed=seed, f=f)


@functools.lru_cache(None)
def viewfinder():
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    col = E.CREAM + (255,); L, m = 90, 70
    for (x, y, sx, sy) in ((m, m, 1, 1), (E.W - m, m, -1, 1), (m, E.H - m, 1, -1), (E.W - m, E.H - m, -1, -1)):
        d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=E.INK + (255,), width=16)
        d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=col, width=8)
    return lay


def rec_overlay(c, t):
    d = ImageDraw.Draw(c); font = ImageFont.truetype(E.FONT, 48)
    if int(t * 2) % 2 == 0: d.ellipse((140, 128, 172, 160), fill=(214, 40, 30, 255))
    d.text((186, 116), "REC", font=font, fill=E.CREAM + (255,), stroke_width=4, stroke_fill=E.INK + (255,))
    s = int((t - CUT_CAM) * 25)
    tc = f"00:{14 + s // 1500:02d}:{(s // 25) % 60:02d}:{s % 25:02d}"
    d.text((1500, 116), tc, font=font, fill=E.CREAM + (255,), stroke_width=4, stroke_fill=E.INK + (255,))


def scene_view(t, f, c):
    c.alpha_composite(grid_bg(f))
    if t < T["munhaniya"]:
        paste_man(c, "man_seated", f)
    else:
        # one in-between frame: the shoulders start to drop
        jolt = 8 if int((t - T["munhaniya"]) * E.FPS) == 0 else 0
        paste_man(c, "man_slumped", f, dy=jolt)
    c.alpha_composite(viewfinder())
    rec_overlay(c, t)
    dim(c, 0.5 * E.step(t, DIM_T - 0.05, DIM_T + 0.35))   # «الخزي»: the scene goes dark under the red word


def dim(c, a):
    """darken the scene under the labels (labels are drawn after the scene, so «الخزي» stays bright red)"""
    if a > 0: c.alpha_composite(Image.new("RGBA", c.size, (8, 10, 18, int(255 * a))))


# ------------------------------------------------------------------ 3. the shadow on the wall grows heavy and becomes the rock
SH_BOX = 1100                                           # common canvas for the morph


@functools.lru_cache(None)
def _sdf(name, h):
    """signed distance field of a cut-out's silhouette (inside < 0), on a square canvas, feet at the bottom centre"""
    im = E.scaled(name, h)
    m = np.zeros((SH_BOX, SH_BOX), bool)
    a = np.asarray(im.getchannel("A")) > 128
    a = ndimage.binary_fill_holes(ndimage.binary_closing(a, iterations=8))
    y0 = SH_BOX - a.shape[0] - 20; x0 = (SH_BOX - a.shape[1]) // 2
    m[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    return ndimage.distance_transform_edt(~m) - ndimage.distance_transform_edt(m)


@functools.lru_cache(None)
def shadow_shape(u_q, seed):
    """u 0..1: the slumped man's silhouette -> the rock's silhouette; returns an RGBA ink shadow"""
    u = u_q / 16
    sd = _sdf("man_slumped", 700) * (1 - u) + _sdf("rock", 760) * u
    r = np.random.default_rng(seed)
    wob = ndimage.gaussian_filter(r.standard_normal(sd.shape), 5); wob /= np.abs(wob).max()
    m = (sd + 3 * wob) < 0
    a = ndimage.gaussian_filter(m.astype(float), 4)
    lay = np.zeros(sd.shape + (4,), np.uint8)
    lay[..., :3] = (14, 18, 28); lay[..., 3] = (a * 225).astype(np.uint8)
    out = Image.fromarray(lay, "RGBA")
    if u > 0.55:                                        # the rock's own grain surfaces inside the shadow
        rk = E.scaled("rock", 760).convert("RGB")
        g = np.asarray(rk).mean(axis=2) / 255
        tex = np.zeros((SH_BOX, SH_BOX, 4), np.uint8)
        y0 = SH_BOX - rk.height - 20; x0 = (SH_BOX - rk.width) // 2
        col = (20 + 70 * g)[..., None] * np.array([1.0, 1.05, 1.25])[None, None, :]
        tex[y0:y0 + rk.height, x0:x0 + rk.width, :3] = np.clip(col, 0, 255).astype(np.uint8)
        tex[..., 3] = (a * 255 * min(1, (u - 0.55) / 0.45) * 0.8).astype(np.uint8)
        out.alpha_composite(Image.fromarray(tex, "RGBA"))
    return out


GROW0, GROW1 = T["baad"] + 0.2, T["akthar"] + 0.3       # shadow grows and turns into the rock
FLOOR_Y = 1000


def scene_shadow(t, f, c):
    c.alpha_composite(grid_bg(f))
    d = ImageDraw.Draw(c)                               # a torn strip of darker paper: the floor
    r = np.random.default_rng(5)
    d.polygon([(-20, FLOOR_Y + r.normal(0, 3)) if i == 0 else (i * 60, FLOOR_Y + r.normal(0, 4)) for i in range(34)] +
              [(E.W + 20, E.H + 20), (-20, E.H + 20)], fill=(196, 188, 170, 255))
    u = E.step(t, GROW0, GROW1)
    uq = round(u * 16)
    sh = shadow_shape(uq, (f // 2) % 3)
    s = 1.15 + 0.2 * uq / 16
    sh = sh.resize((int(sh.width * s), int(sh.height * s)), Image.BILINEAR)
    fx = 960 - 40 * uq / 16                             # cast up the wall behind him, leaning over him as it grows
    E.safe(c, sh, int(fx - sh.width / 2), int(FLOOR_Y + 10 - sh.height))
    im = man_img("man_slumped")
    E.paste(c, im, 640, FLOOR_Y + 20 - im.height / 2, seed=72, f=f)
    dim(c, 0.28 + 0.14 * u)


SCENES = [
    E.Scene(0, CUT_CAM, scene_lab, bg=None),
    E.Scene(CUT_CAM, CUT_SHADOW, scene_view, bg=None, rip=True),
    E.Scene(CUT_SHADOW, DUR, scene_shadow, bg=None, rip=True),
]

LABELS = [
    E.Label("جامعة كولومبيا البريطانية · ٢٠١٣", (), [T["jamia"], T["kulumbiya"], T["britaniya"], T["sana"], T["sana"]],
            hide=T["sitta"] - 0.1, x=1180, y=200, size=70),
    E.Label("٤٦ متعافيًا من الكحول", ("٤٦",), [T["sitta"], T["mutaafin"], T["kuhul"] - 0.25, T["kuhul"]],
            hide=CUT_CAM, x=1200, y=200, size=70),
    E.Label("الأكتاف المنحنية · الصدر المنكمش", ("المنحنية", "المنكمش"),
            [T["aktaf"], T["munhaniya"], T["munhaniya"] + 0.1, T["sadr"], T["munkamish"]], hide=T["khizy"] - 0.1, x=640, y=280, size=60),
    E.Label("الخزي", ("الخزي",), [T["khizy"]], hide=CUT_SHADOW, x=640, y=560, size=190),
    E.Label("أكثرَ انتكاساً", ("انتكاساً",), [T["akthar"], T["intikasan"]], hide=DUR, x=1480, y=170, size=86),
]


def post(arr, t, f, idx):
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys11"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
