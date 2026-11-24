"""بصيرة · فيديو سيزيف · الجزء ١٣: «سرّ فيتنام» (6:00–6:30). Collage on grid paper:
20% of the soldiers on heroin, the flight home, only 5% relapsed - the land, the friends, the cues changed. Ends in desert dark."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import basira_engine as E
import part_6 as P6                                     # grid paper

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames13"); os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(hunak=0.0, dars=0.6, harb=2.0, vietnam=2.5, adman=3.6, ishrin=5.0, bilmia=5.5, heroin=7.4,
         khaf=8.2, awdatihim=9.2, lakin=10.2, alima=10.8, li=12.0, robins=12.4, tabaat=13.0,
         fawajadat=15.0, khamsa=16.0, bilmia2=16.5, intakasu=17.5, sana=18.3,
         ard=19.5, rifaq=21.0, muthirat=22.4, fataghayyar=23.6, insan=24.2,
         yara=25.2, min=27.0, aqwa=27.4, durus=27.9, taafi=28.5)
_tj = os.path.join(HERE, "proj", "times_13.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["taafi"] + 2.6
FLY0, FLY1 = T["awdatihim"] - 0.2, T["awdatihim"] + 2.2  # the camera follows the plane across the paper ocean
DARK = T["taafi"] + 0.7                                 # tear into the night desert (into part 14)


# ------------------------------------------------------------------ paper scraps: «٢٠%» that tears into «٥%»
@functools.lru_cache(None)
def scrap(text, size, color, seed):
    font = ImageFont.truetype(E.FONT, size)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = tmp.textlength(text, font=font)
    w, h = int(tw + 110), int(size * 1.45)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed); pts = []
    for x in np.linspace(8, w - 8, 30): pts.append((x, 10 + r.normal(0, 4)))
    for y in np.linspace(10, h - 10, 8): pts.append((w - 8 + r.normal(0, 4), y))
    for x in np.linspace(w - 8, 8, 30): pts.append((x, h - 10 + r.normal(0, 4)))
    for y in np.linspace(h - 10, 10, 8): pts.append((8 + r.normal(0, 4), y))
    d.polygon(pts, fill=E.CREAM + (255,))
    d.text((55, h / 2 - size * 0.62), text, font=font, fill=color + (255,))
    return im


def big20(): return scrap("٢٠%", 230, E.BRICK, 5)
def big5(): return scrap("٥%", 230, E.INK, 6)


@functools.lru_cache(None)
def halves(seed=77):
    im = big20(); r = np.random.default_rng(seed)
    xs = [im.width * 0.5 + r.normal(0, 16) for _ in range(12)]
    ys = np.linspace(-5, im.height + 5, 12)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).polygon([(im.width + 5, -5)] + list(zip(xs, ys)) + [(im.width + 5, im.height + 5)], fill=255)
    out = []
    for side, mask in ((1, m), (-1, m.point(lambda v: 255 - v))):
        h = Image.new("RGBA", im.size, (0, 0, 0, 0)); h.paste(im, (0, 0), mask)
        ImageDraw.Draw(h).line(list(zip(xs, ys)), fill=(255, 250, 238, 255), width=9)
        out.append((side, h))
    return out


# ------------------------------------------------------------------ the world: two screens wide (right = Vietnam, left = home)
WW = 2 * E.W


def cam_x(t):
    u = round(E.step(t, FLY0, FLY1) * 24) / 24
    return E.W * (1 - u)


P0, P1, P2 = (3260, 560), (2050, 60), (420, 420)       # plane flight: from the map, arcing over the ocean, to the coast


def flight(u):
    x = (1 - u) ** 2 * P0[0] + 2 * u * (1 - u) * P1[0] + u * u * P2[0]
    y = (1 - u) ** 2 * P0[1] + 2 * u * (1 - u) * P1[1] + u * u * P2[1]
    dx = 2 * (1 - u) * (P1[0] - P0[0]) + 2 * u * (P2[0] - P1[0]); dy = 2 * (1 - u) * (P1[1] - P0[1]) + 2 * u * (P2[1] - P1[1])
    return x, y, math.degrees(math.atan2(-dy, -dx))     # plane faces left


def plane_u(t):
    return E.step(t, FLY0 - 0.1, FLY1 + 0.4) if t < FLY1 + 0.4 else 1.0


COAST = 1900                                            # the ocean ends here (world x); Vietnam has dry paper


def ocean(c, t, f, ox):
    """three torn bands of pale blue-grey paper, sinking away once he is home"""
    sink = 700 * E.step(t, T["sana"] - 0.3, T["sana"] + 0.7)
    d = ImageDraw.Draw(c)
    for i, col in enumerate(((184, 196, 202), (164, 180, 190), (146, 164, 176))):
        yy = 650 + i * 120 + sink
        if yy > E.H + 40: continue
        pts = [(x - ox, yy + 16 * math.sin(x / 90 + (f // 2) * 0.7 + i * 1.7)) for x in range(-40, COAST + 1, 40)]
        pts = [p for p in pts if -80 < p[0] < E.W + 80]
        if len(pts) < 2: continue
        rr = np.random.default_rng(i * 13 + (f // 2) % 3)       # torn end of the paper ocean, off the Vietnam shore
        end = [(COAST - ox + 30 * i + rr.normal(0, 10), y) for y in np.linspace(pts[-1][1], E.H + 40, 8)]
        d.polygon(pts + end + [(pts[0][0], E.H + 40)], fill=col + (255,))
        d.line(pts, fill=(250, 248, 240, 255), width=5)


def dashes(c, t, ox):
    u = plane_u(t)
    if u <= 0 or t >= T["sana"]: return
    d = ImageDraw.Draw(c)
    n = int(60 * u)
    for i in range(0, n, 2):                            # dashed track behind the plane
        a, b = flight(i / 60), flight(min(u, (i + 1) / 60))
        d.line([(a[0] - ox, a[1] + 40), (b[0] - ox, b[1] + 40)], fill=E.INK + (255,), width=6)


def scene_world(t, f, c):
    ox = cam_x(t)
    c.alpha_composite(P6.grid_bg(f))
    # Vietnam (world x 1920..3840)
    if ox > 1:
        k = E.step(t, T["harb"] - 0.1, T["harb"] + 0.6)
        if k > 0:
            E.paste(c, E.scaled("vietnam_map", 760), 3330 - ox, 560 - 900 * (1 - k), rot=-4, seed=31, f=f)
        k = E.step(t, T["vietnam"] - 0.1, T["vietnam"] + 0.6)
        if k > 0:
            E.paste(c, E.scaled("soldiers", 560), 2560 - ox - 1300 * (1 - k), 620, rot=3, seed=32, f=f)
        if t >= T["ishrin"] - 0.05:
            j = int((t - T["ishrin"] + 0.05) * E.FPS); s = {0: 0.5, 1: 1.12, 2: 0.96}.get(j, 1.0)
            im = big20(); im = im.resize((int(im.width * s * 0.8), int(im.height * s * 0.8)), Image.LANCZOS)
            E.paste(c, im, 2600 - ox, 790, rot=-6, seed=33, f=f)
    ocean(c, t, f, ox)
    dashes(c, t, ox)
    u = plane_u(t)
    if 0 < u < 1 or (u >= 1 and t < T["li"]):
        x, y, ang = flight(u)
        if u >= 1: x -= 900 * (t - FLY1 - 0.4); y -= 400 * (t - FLY1 - 0.4)   # flies on, off the top-left
        E.paste(c, E.scaled("airplane", 170), x - ox, y, rot=-ang * 0.35, seed=34, f=f)
    home(c, t, f)
    rate(c, t, f)


# ------------------------------------------------------------------ home: the land, the friends, the man himself
HOME = [("house", "ard", 390, (430, 660), -3), ("family", "rifaq", 420, (1000, 720), 2), ("soldier_home", "insan", 620, (1570, 650), -2)]


def home(c, t, f):
    for i, (name, key, h, (x, y), rot) in enumerate(HOME):
        t0 = T[key] - 0.1
        if t < t0: continue
        k = E.step(t, t0, t0 + 0.55)
        j = int((t - t0) * E.FPS); s = {0: 0.6, 1: 1.08, 2: 0.97}.get(j, 1.0)
        im = E.scaled(name, int(h * s))
        E.paste(c, im, x, y + 260 * (1 - k), rot=rot, seed=40 + i, f=f)


def rate(c, t, f):
    """«فوجدت…»: the 20% scrap slides back in and tears on «خمسة», showing 5% beneath; then it settles in the corner"""
    t_in, t_tear = T["fawajadat"] - 0.2, T["khamsa"]
    if t < t_in: return
    k = E.step(t, t_in, t_in + 0.6)
    x, y = 960 + 1200 * (1 - k), 560
    corner = E.step(t, T["sana"] - 0.2, T["sana"] + 0.5)
    if t >= t_tear:
        sc = 1 - 0.55 * corner
        im = big5()
        j = int((t - t_tear) * E.FPS)
        if j < 3: sc *= {0: 0.85, 1: 1.1, 2: 0.98}[j]
        im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
        E.paste(c, im, x + (1640 - x) * corner, y + (180 - y) * corner, rot=-3, seed=36, f=f)
        u = t - t_tear
        if u < 1.4:
            for side, h in halves():
                E.paste(c, h, x + side * (60 * min(1, u / 0.2) + 160 * u), y + 1300 * max(0, u - 0.15) ** 2,
                        rot=-5 - side * (10 * min(1, u / 0.2) + 60 * u), seed=37 + side, f=f)
    else:
        E.paste(c, big20(), x, y, rot=-5, seed=37, f=f)


# ------------------------------------------------------------------ the night desert (lead into part 14)
def scene_desert(t, f, c):
    c.alpha_composite(E.paper_bg(f, (16, 22, 38)))
    d = ImageDraw.Draw(c); r = np.random.default_rng(9)
    for _ in range(70):                                  # a few cream stars, flickering
        x, y = r.uniform(0, E.W), r.uniform(0, 560); s = r.uniform(1.5, 3.5)
        if (f + int(x)) % 7: d.ellipse((x - s, y - s, x + s, y + s), fill=(236, 226, 200, 255))
    for i, (col, base, amp) in enumerate((((44, 40, 50), 760, 80), ((34, 32, 44), 860, 60), ((24, 24, 36), 960, 40))):
        drift = (t - DARK) * 14 * (i + 1)
        pts = [(x, base + amp * math.sin((x + drift) / (380 - 60 * i) + i) + 0.4 * amp * math.sin((x + drift) / 150))
               for x in range(-40, E.W + 80, 30)]
        d.polygon(pts + [(E.W + 40, E.H + 20), (-40, E.H + 20)], fill=col + (255,))


SCENES = [
    E.Scene(0, DARK, scene_world, bg=None),
    E.Scene(DARK, DUR, scene_desert, bg=None, rip=True),
]

LABELS = [
    E.Label("عشرين بالمئة", ("عشرين", "بالمئة"), [T["ishrin"], T["bilmia"]], hide=FLY0, x=2580 - E.W + 0, y=150, size=84),
    E.Label("لي روبنز", (), [T["li"], T["robins"]], hide=T["fawajadat"] - 0.3, y=170, size=96),
    E.Label("من أقوى دروس التعافي", (), [T["min"], T["aqwa"], T["durus"], T["taafi"]], hide=DARK, y=150, size=84),
]


def post(arr, t, f, idx):
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys13"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
