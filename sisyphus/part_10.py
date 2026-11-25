"""بصيرة · فيديو سيزيف · الجزء ١٠: «الفكرة التي تُسقطك» (4:30–5:00). Collage on grid paper: one slip, one thought, and the whole chain falls."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import basira_engine as E
import part_6 as P6                                     # grid paper

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames10"); os.makedirs(OUT, exist_ok=True)
grid_bg = P6.grid_bg

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(alan=1.0, marlat=1.5, khata=5.0, yaquluna=7.0, sijara=9.0, shahrayn=10.0, khalas=12.4, kharabt=12.9,
         kull=13.3, shay=13.7, faukmil=15.0, athar=18.0, khark=18.5, imtina=19.0, inhiyar=23.0,
         fikra=27.0, wahida=27.5)
_tj = os.path.join(HERE, "proj", "times_10.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["wahida"] + 3.0
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice
CUT1 = T["khata"] - 0.5                                 # typewriter -> head and bubble
FLASH0, FLASH1 = T["inhiyar"] - 0.2, T["inhiyar"] + 2.4  # Sisyphus lets the rock go


# ------------------------------------------------------------------ 1. the typewriter types his name
KEYS = [T["alan"], T["marlat"]]


def scene_typewriter(t, f, c):
    c.alpha_composite(grid_bg(f))
    k = E.step(t, 0.0, 0.8)
    jolt = 6 if any(0 <= t - tt < 0.09 for tt in KEYS) else 0     # the carriage jumps on each word
    E.paste(c, E.scaled("typewriter", 560), 960 - 6 * jolt, 1300 - 680 * k + jolt, seed=31, f=f)


# ------------------------------------------------------------------ 2. the head, the bubble, the 60-day chain
HEAD_H = 620; HEAD = (1560, 660)
MOUTH = (71, 325)                                       # mouth in head cut-out px
BUB = (800, 420); BUB_W, BUB_H = 760, 270


def mouth_xy():
    s = HEAD_H / E.load("head_silhouette").height; im = E.scaled("head_silhouette", HEAD_H)
    return HEAD[0] - im.width / 2 + MOUTH[0] * s, HEAD[1] - im.height / 2 + MOUTH[1] * s


@functools.lru_cache(None)
def bubble_img(n_words, seed=3):
    """cream paper speech bubble with a torn edge; the inner thought inks in word by word"""
    w, h = BUB_W + 260, BUB_H + 120
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    cx, cy = BUB_W / 2 + 20, BUB_H / 2 + 20
    pts = []
    for a in np.linspace(0, 2 * math.pi, 90, endpoint=False):
        rr = 1 + r.normal(0, 0.012)
        pts.append((cx + BUB_W / 2 * rr * math.cos(a), cy + BUB_H / 2 * rr * math.sin(a)))
    mx, my = mouth_xy(); tx, ty = mx - (BUB[0] - cx) - 26, my - (BUB[1] - cy)   # tail tip near the mouth, local coords
    tail = [(cx + BUB_W * 0.30, cy + BUB_H * 0.22), (tx, ty), (cx + BUB_W * 0.40, cy + BUB_H * 0.05)]
    for poly, col, wd in ((pts, E.INK, 14), (tail, E.INK, 14)):
        d.polygon(poly, fill=col + (255,), outline=col + (255,), width=wd)
    d.polygon(pts, fill=E.CREAM + (255,)); d.polygon(tail, fill=E.CREAM + (255,))
    if n_words:
        words = "خلاص خرّبت كل شيء".split(" ")[:n_words]
        font = ImageFont.truetype(E.FONT, 74)
        txt = " ".join(words)
        tw = d.textlength("خلاص خرّبت كل شيء", font=font, direction="rtl", language="ar")
        x_right = cx + tw / 2
        lw = d.textlength(txt, font=font, direction="rtl", language="ar")
        d.text((x_right - lw, cy - 52), txt, font=font, fill=E.INK + (255,), direction="rtl", language="ar")
    return im, cx, cy


def draw_bubble(c, t, f):
    if t < T["khata"] - 0.05: return
    n = sum(1 for k in ("khalas", "kharabt", "kull", "shay") if t >= T[k])
    im, cx, cy = bubble_img(n)
    k = int((t - T["khata"] + 0.05) * E.FPS)
    s = {0: 0.5, 1: 1.08, 2: 0.97}.get(k, 1.0)
    if any(0 <= t - T[kk] < 0.09 for kk in ("khalas", "kharabt", "kull", "shay")): s = 1.03
    ox = BUB[0] - cx + im.width / 2; oy = BUB[1] - cy + im.height / 2
    if t < T["fikra"]:
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        E.paste(c, im, ox, oy, rot=-1.5, seed=41, f=f)
        return
    # «فكرة واحدة»: the bubble rips in two down a jagged line, the halves fall apart
    u = t - T["fikra"]
    r = np.random.default_rng(77)
    xs = [im.width * 0.46 + r.normal(0, 14) for _ in range(14)]
    ys = np.linspace(-5, im.height + 5, 14)
    right_poly = [(im.width + 5, -5)] + list(zip(xs, ys)) + [(im.width + 5, im.height + 5)]
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).polygon(right_poly, fill=255)
    halves = []
    for side, mask in ((1, m), (-1, m.point(lambda v: 255 - v))):
        h = Image.new("RGBA", im.size, (0, 0, 0, 0)); h.paste(im, (0, 0), mask)
        d = ImageDraw.Draw(h); d.line(list(zip(xs, ys)), fill=E.CREAM + (255,), width=10)   # fibre edge
        halves.append((side, h))
    open_ = E.step(t, T["fikra"], T["fikra"] + 0.25)
    for side, h in halves:
        fall = max(0.0, u - 0.35)
        E.paste(c, h, ox + side * (40 * open_ + 120 * fall), oy + 1400 * fall * fall,
                rot=-1.5 - side * (6 * open_ + 50 * fall), seed=42 + side, f=f)


NCOL, NROW, SQ, GAP = 20, 3, 50, 9
X_RIGHT, Y_TOP = 1300, 720
CHAIN0 = T["sijara"] - 0.4                              # the squares tick in fast before «شهرين»
SLIP = T["shahrayn"] + 0.3                              # the red cross on day 60
TOPPLE = 0.045                                          # delay between neighbours falling


def sq_pos(i):
    """day i (0..59), right-to-left rows"""
    row, col = divmod(i, NCOL)
    return X_RIGHT - col * (SQ + GAP), Y_TOP + row * (SQ + GAP + 14)


@functools.lru_cache(None)
def square(mark, seed):
    s = SQ + 16
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    d.rectangle((4 + r.normal(0, 1), 4 + r.normal(0, 1), s - 4, s - 4), fill=E.CREAM + (255,), outline=(70, 70, 70, 255), width=3)
    if mark == "tick":
        col = (46, 104, 70, 255)
        d.line([(16, 34), (27, 46), (s - 14, 16)], fill=col, width=7, joint="curve")
    elif mark == "cross":
        d.line([(12, 12), (s - 12, s - 12)], fill=E.BRICK + (255,), width=9)
        d.line([(s - 12, 12), (12, s - 12)], fill=E.BRICK + (255,), width=9)
    return im


def chain(c, t, f):
    if t < CHAIN0: return
    for i in range(60):
        t_in = CHAIN0 + i * 0.022
        if t < t_in: break
        mark = "cross" if i == 59 and t >= SLIP else ("tick" if i < 59 else None)
        x, y = sq_pos(i)
        rot, dy, dx = 0.0, 0.0, 0.0
        tf = T["faukmil"] + (59 - i) * TOPPLE           # the fall starts at the red cross and runs back to day 1
        if t >= tf:
            u = t - tf
            rot = -min(90, 600 * u) - 120 * max(0, u - 0.15)
            dy = 1500 * max(0, u - 0.12) ** 2; dx = 60 * u
            if y + dy > E.H + 100: continue
        im = square(mark, i)
        if i == 59 and 0 <= t - SLIP < 0.17: im = im.resize((int(im.width * 1.25), int(im.height * 1.25)))
        E.paste(c, im, x + dx, y + dy, rot=rot, shadow=True, seed=100 + i, f=f, boil=(f // 2 + i) % 5 == 0)


def scene_board(t, f, c):
    c.alpha_composite(grid_bg(f))
    E.paste(c, E.scaled("head_silhouette", HEAD_H), HEAD[0], HEAD[1] + 400 * (1 - E.step(t, CUT1, CUT1 + 0.6)), seed=51, f=f)
    draw_bubble(c, t, f)
    chain(c, t, f)
    if FLASH1 <= t and int((t - FLASH1) * E.FPS) == 0:
        g = E.glitch(c, f); c.alpha_composite(g)


# ------------------------------------------------------------------ 3. «انهيار كامل»: Sisyphus opens his hands, the rock rolls away
SIS_FIG = 645                                           # crown-to-feet in cut-out px
SIS_H = int(E.load("sis_letgo").height * 700 / SIS_FIG)


def scene_letgo(t, f, c):
    bg = E.image_bg("hill", f, pan=0.62, sat=0.95)
    E.paste(bg, E.scaled("sis_letgo", SIS_H), 1300, 470, seed=61, f=f)
    u = E.step(t, FLASH0 + 0.25, FLASH1) ** 1.3
    u = round(u * 18) / 18
    E.paste(bg, E.scaled("rock", 230), 1030 - 1250 * u, 760 + 260 * u, rot=-700 * u, seed=8, f=f)
    c.alpha_composite(E.glitch(bg, f) if int((t - FLASH0) * E.FPS) == 0 else bg)


SCENES = [
    E.Scene(0, CUT1, scene_typewriter, bg=None),
    E.Scene(CUT1, FLASH0, scene_board, bg=None, rip=True),
    E.Scene(FLASH0, FLASH1, scene_letgo, bg=None, rip=False),
    E.Scene(FLASH1, DUR, scene_board, bg=None, rip=False),
]

LABELS = [
    E.Label("آلان مارلات", (), KEYS, hide=CUT1, y=150),
    E.Label("أثر خرق الامتناع", ("أثر", "خرق", "الامتناع"), [T["athar"], T["khark"], T["imtina"]], hide=FLASH0, y=150, size=92),
]


def post(arr, t, f, idx):
    end = T["faukmil"] + 60 * TOPPLE + 0.3              # the last square hits: one crash jolt
    k = int(math.floor((t - end) * E.FPS + 1e-6))
    if k in (0, 1): arr = np.roll(arr, (12 if k == 0 else -7), axis=0)
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys10"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
