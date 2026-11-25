"""بصيرة · فيديو سيزيف · الجزء ٩: «الدماغ يتعافى» (4:00–4:30). Collage on grid paper: the scanner, a pale scan, a year of calendar pages, the colour comes back."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import basira_engine as E
import part_6 as P6                                     # grid paper

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames9"); os.makedirs(OUT, exist_ok=True)
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(khabar=0.0, aam=2.6, nura=4.0, folko=4.5, ashhur=9.0, jadid=15.0, sana=16.3, irtafaat=20.0,
         yastati=24.0, an=24.5, yataafa=25.0, lakinnahu=27.0, waqtan=28.0)
_tj = os.path.join(HERE, "proj", "times_9.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["waqtan"] + 3.0
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice
CUT1 = T["ashhur"] - 0.4                                # scanner -> scans board
CUT2 = T["lakinnahu"]                                   # board -> hourglass
FLIP0, FLIP1 = T["jadid"], T["jadid"] + 3.2             # calendar pages fly
SCAN2_IN = FLIP1 + 0.2


def warm_grid(f, k=1.0):
    """grid paper lit a little warmer, as if a lamp came on («خبراً جميلاً»)"""
    c = P6.grid_bg(f)
    if k > 0: c.alpha_composite(E.glow_spot((260, 80, 1660, 1000), color=(255, 214, 150), alpha=int(60 * k), blur=160))
    return c


def scrap(text, x, y, t, t0, f, seed, size=54, rot=-4):
    """small torn paper scrap with a few ink words, popping in at t0"""
    if t < t0 - 0.05: return None
    k = int((t - t0 + 0.05) * E.FPS)
    s = {0: 0.6, 1: 1.08, 2: 0.97}.get(k, 1.0)
    im = E._strip(text, (), len(text.split(" ")), seed, size)
    if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    return im, x, y, rot, seed


# ------------------------------------------------------------------ 1. the scanner rolls in, «٢٠٠١», «نورا فولكو»
def scene_scanner(t, f, c):
    c.alpha_composite(warm_grid(f, E.step(t, 0.0, 1.2)))
    k = E.step(t, 0.3, 1.8)
    k = round(k * 14) / 14
    E.paste(c, E.scaled("scanner", 560), 2400 - (2400 - 900) * k, 640 - (0 if k >= 1 or f % 2 else 6), seed=31, f=f)
    s = scrap("عام 2001".translate(AR), 1520, 330, t, T["aam"], f, 41, size=60, rot=5)
    if s: E.paste(c, s[0], s[1], s[2], rot=s[3], seed=s[4], f=f)


# ------------------------------------------------------------------ 2. the board: two scans, the calendar between them
SCAN_H = 470
SCAN1 = (1420, 560); SCAN2 = (500, 560)
SCAN_C = (279, 282)                                     # brain centre inside the scan cut-out


@functools.lru_cache(None)
def scan_pair():
    col = E.scaled("brain_scan", SCAN_H)
    rgb = col.convert("RGB")
    pale = ImageEnhance.Contrast(ImageEnhance.Color(rgb).enhance(0.1)).enhance(0.8)   # grey, flat; the cream border stays cream
    pale = pale.convert("RGBA"); pale.putalpha(col.getchannel("A"))
    return col, pale


def scan_img(u):
    """u 0 = pale (low dopamine), 1 = full colour; the colour fills outward from the centre"""
    col, pale = scan_pair()
    if u <= 0: return pale
    if u >= 1: return col
    s = SCAN_H / E.load("brain_scan").height
    cx, cy = SCAN_C[0] * s, SCAN_C[1] * s
    R = 30 + 300 * u
    m = Image.new("L", col.size, 0)
    ImageDraw.Draw(m).ellipse((cx - R, cy - R * 1.15, cx + R, cy + R * 1.15), fill=255)
    return Image.composite(col, pale, m.filter(ImageFilter.GaussianBlur(26)))


CAL_H = 330
PAGE_BOX = (96, 158, 366, 550)                          # the blank top page inside the calendar cut-out


@functools.lru_cache(None)
def cal_page(h):
    s = h / E.load("calendar_block").height
    pg = E.load("calendar_block").crop(PAGE_BOX)
    return pg.resize((int(pg.width * s), int(pg.height * s)), Image.LANCZOS)


def cal_pos(t):
    """calendar sits between the scans; slides down to make room for the arrow"""
    k = E.step(t, T["yastati"] - 0.3, T["yastati"] + 0.4)
    return 960, 640 + 250 * k, int(CAL_H - 80 * k)


def calendar(c, t, f):
    if t < T["ashhur"] + 0.4: return
    x, y, h = cal_pos(t)
    k = E.step(t, T["ashhur"] + 0.4, T["ashhur"] + 0.9)
    E.paste(c, E.scaled("calendar_block", h), x, y + 600 * (1 - k), seed=51, f=f)
    if not (FLIP0 <= t < FLIP1 + 1.2): return
    s = h / E.load("calendar_block").height
    W0 = E.load("calendar_block").width * s; H0 = E.load("calendar_block").height * s
    px = x - W0 / 2 + (PAGE_BOX[0] + PAGE_BOX[2]) / 2 * s
    py = y - H0 / 2 + (PAGE_BOX[1] + PAGE_BOX[3]) / 2 * s
    pg = cal_page(h)
    r = np.random.default_rng(9)
    for i in range(28):                                 # a page every ~0.11 s, each tears off and flies up-left
        t0 = FLIP0 + i * (FLIP1 - FLIP0) / 28
        u = t - t0
        if u < 0 or u > 1.1: continue
        vx, vy, spin = r.uniform(-900, -500), r.uniform(-700, -400), r.uniform(-500, -250)
        E.paste(c, pg, px + vx * u, py + vy * u + 900 * u * u, rot=-spin * u, shadow=u > 0.1, seed=60 + i, f=f, boil=False)


def arrow(c, t, f):
    """paper arrow pointing right-to-left, from the old scan to the new one"""
    u = E.step(t, T["yastati"], T["yastati"] + 0.6)
    if u <= 0: return
    x1 = 1150; x0 = x1 - (x1 - 770) * u; y = 560
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = np.random.default_rng(f // 2)
    pts = [(x1, y + r.normal(0, 1.5)), (x0 + 30, y + r.normal(0, 1.5))]
    d.line(pts, fill=E.CREAM + (255,), width=40); d.line(pts, fill=E.BRICK + (255,), width=24)
    d.polygon([(x0 - 20, y), (x0 + 50, y - 50), (x0 + 50, y + 50)], fill=E.BRICK + (255,), outline=E.CREAM + (255,), width=7)
    sh = Image.new("RGBA", lay.size, (5, 8, 16, 0)); sh.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.4)))
    c.alpha_composite(sh, (6, 8)); c.alpha_composite(lay)


def pop_scale(t, t0):
    k = int((t - t0 + 0.05) * E.FPS)
    return {0: 0.6, 1: 1.08, 2: 0.97}.get(k, 1.0)


def scene_board(t, f, c):
    c.alpha_composite(warm_grid(f))
    # scan 1: after a few months - pale
    if t >= T["ashhur"] - 0.05:
        im = scan_img(0)
        s = pop_scale(t, T["ashhur"])
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        E.paste(c, im, *SCAN1, rot=3, seed=21, f=f)
        sc = scrap("بعد أشهر", SCAN1[0], SCAN1[1] + 300, t, T["ashhur"] + 0.4, f, 43, rot=-3)
        if sc: E.paste(c, sc[0], sc[1], sc[2], rot=sc[3], seed=sc[4], f=f)
    calendar(c, t, f)
    # scan 2: a year later - the colour fills back in on «ارتفعت»
    if t >= SCAN2_IN - 0.05:
        u = E.step(t, T["irtafaat"], T["irtafaat"] + 1.6); u = round(u * 12) / 12
        im = scan_img(u)
        s = pop_scale(t, SCAN2_IN)
        if 0 <= t - (T["irtafaat"] + 1.6) < 0.17: s = 1.05             # little bump when it is full
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        E.paste(c, im, *SCAN2, rot=-3, seed=22, f=f)
        sc = scrap("بعد سنة", SCAN2[0], SCAN2[1] + 300, t, SCAN2_IN + 0.2, f, 44, rot=3)
        if sc: E.paste(c, sc[0], sc[1], sc[2], rot=sc[3], seed=sc[4], f=f)
    arrow(c, t, f)


# ------------------------------------------------------------------ 3. «وقتاً»: the hourglass, sand running this time
HG_H = 640; HG = (960, 590)


def scene_hourglass(t, f, c):
    c.alpha_composite(warm_grid(f))
    z = 1 + 0.12 * round(E.step(t, CUT2, DUR) * 10) / 10      # slow stepped push-in
    h = int(HG_H * z)
    k = E.step(t, CUT2 + 0.2, CUT2 + 0.8)
    E.paste(c, E.scaled("hourglass", h), HG[0], HG[1] - 700 * (1 - k), seed=81, f=f)
    if k < 1 or t < T["waqtan"]: return
    # the stream of sand through the neck, and grains landing
    d = ImageDraw.Draw(c); r = np.random.default_rng(f)
    y0, y1 = HG[1] - 0.01 * h, HG[1] + 0.20 * h
    for _ in range(70):
        yy = r.uniform(y0, y1); xx = HG[0] + r.normal(0, 2.2)
        d.ellipse((xx - 2.5, yy - 2.5, xx + 2.5, yy + 2.5), fill=(150, 120, 80, 255))
    d.line([(HG[0], y0), (HG[0], y1)], fill=(170, 140, 95, 200), width=3)
    for _ in range(14):
        xx = HG[0] + r.normal(0, 18); yy = y1 + r.uniform(-6, 6)
        d.ellipse((xx - 3, yy - 3, xx + 3, yy + 3), fill=(160, 128, 86, 255))


SCENES = [
    E.Scene(0, CUT1, scene_scanner, bg=None),
    E.Scene(CUT1, CUT2, scene_board, bg=None, rip=True),
    E.Scene(CUT2, DUR, scene_hourglass, bg=None, rip=True),
]

LABELS = [
    E.Label("نورا فولكو", (), [T["nura"], T["folko"]], hide=CUT1, y=150),
    E.Label("يستطيع أن يتعافى", ("يستطيع", "أن", "يتعافى"), [T["yastati"], T["an"], T["yataafa"]], hide=CUT2 + 0.3, y=150),
]


def post(arr, t, f, idx):
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys9"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
