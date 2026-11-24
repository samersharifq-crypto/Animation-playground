"""بصيرة · فيديو سيزيف · الجزء ١٢: «لا تجعل الذنب يهزم توبتك» (5:30–6:00). Back in the myth world:
the screen tears in two - guilt pushes the rock up the slope, shame sits in the pit - then the shame half falls away."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "frames12"); os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(farq=0.0, daqiq=0.6, yughayyir=1.6, shuur=3.0, bidhanb=3.5, faalt=4.6, falusliha=6.0,
         amma=8.4, khizy=9.0, ana=10.2, sayyi=10.6, amal=11.6, awwal=13.6, yuiduk=14.4, sakhra=15.0,
         thani=16.4, yujlisuk=17.0, qaa=17.6, lihadha=18.8,
         la=20.0, tajal=20.4, dhanb=20.9, yahzim=21.4, tawbatak=22.0,
         saqta=24.6, fil=25.4, hadath=25.9, laysat=27.0, haqiqatuk=27.6)
_tj = os.path.join(HERE, "proj", "times_12.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["haqiqatuk"] + 2.8
SPLIT0, SPLIT1 = 0.35, 0.95                             # the vertical tear runs top -> bottom
FALL0 = T["la"] - 0.15                                  # «لا تجعل»: the shame half tears off and drops
STILL = T["laysat"]                                     # from «وليست» everything holds still


# ------------------------------------------------------------------ the seam
SEAM_X = 960


@functools.lru_cache(None)
def seam_pts():
    r = np.random.default_rng(12)
    return [(SEAM_X + r.normal(0, 10) + 18 * math.sin(y / 140), y) for y in range(-30, E.H + 60, 22)]


@functools.lru_cache(None)
def left_mask():
    m = Image.new("L", (E.W, E.H), 0)
    ImageDraw.Draw(m).polygon([(-40, -30)] + seam_pts() + [(-40, E.H + 60)], fill=255)
    return m


def draw_seam(c, upto_y, dx=0, dy=0):
    pts = [(x + dx, y + dy) for x, y in seam_pts() if y <= upto_y]
    if len(pts) < 2: return
    d = ImageDraw.Draw(c)
    d.line([(x + 9, y) for x, y in pts], fill=(5, 8, 16, 255), width=8)     # shadow of the torn edge
    d.line(pts, fill=E.CREAM + (255,), width=14)                           # cream paper fibre


# ------------------------------------------------------------------ right half: guilt - a hand puts the rock back on the slope
ROCK_H = 320
STEP_T = T["sakhra"]
ROCK_A = (1440, 560); ROCK_B = (1540, 498)              # one step up the slope on «الصخرة»
SLOPE = 14                                              # degrees, the hill rises to the right


def rock_pos(t):
    u = E.step(t, STEP_T, STEP_T + 0.5)
    return ROCK_A[0] + (ROCK_B[0] - ROCK_A[0]) * u, ROCK_A[1] + (ROCK_B[1] - ROCK_A[1]) * u, u


HAND_H = 620
PALM = (1135, 290)                                      # palm edge in hand cut-out px


def hand_center(rx, ry):
    im = E.load("hand_push"); s = HAND_H / im.height; r = math.radians(SLOPE)
    x = (PALM[0] - im.width / 2) * s; y = (PALM[1] - im.height / 2) * s
    px, py = x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)
    return rx - ROCK_H * 0.12 - px, ry + 25 - py


def right_world(t, f, boil=True):
    c = E.image_bg("hill", f if boil else 0, pan=0.5, sat=0.95)
    rx, ry, u = rock_pos(t)
    k = E.step(t, T["shuur"] - 0.2, T["shuur"] + 0.6)      # the hand slides in along the slope and sets the rock down
    drop = 0 if t >= T["shuur"] + 0.6 else -260 * (1 - k)
    E.paste(c, E.scaled("rock", ROCK_H), rx, ry + drop * 0.5, rot=-40 * u, seed=8, f=f, boil=boil)
    shove = 18 if 0 < t - STEP_T < 0.25 else 0
    hx, hy = hand_center(rx, ry)                        # palm on the rock's lower-left; the cut end of the arm stays off-screen
    hx += -420 * (1 - k) + shove; hy += 200 * (1 - k)
    if k > 0:
        E.paste(c, E.scaled("hand_push", HAND_H), hx, hy, rot=SLOPE, seed=33, f=f, boil=boil)
    return c


# ------------------------------------------------------------------ left half: shame - a man in the pit, head in his hands
def left_world(t, f, boil=True):
    c = E.image_bg("hill", f if boil else 0, pan=0.1, zoom=1.35, blur=2.5, sat=0.7, center=(700, 1060))
    if t >= T["khizy"] - 0.1:
        k = E.step(t, T["khizy"] - 0.1, T["khizy"] + 0.5)
        E.paste(c, E.scaled("man_head_hands", 520), 470, 1460 - 640 * k, seed=41, f=f, boil=boil)
    dark = 0.18 + 0.27 * E.step(t, T["khizy"], T["khizy"] + 0.6) + 0.22 * E.step(t, T["yujlisuk"], T["qaa"] + 0.5)
    c.alpha_composite(Image.new("RGBA", c.size, (6, 9, 18, int(255 * dark))))
    return c


def scene_split(t, f, c):
    boil = t < STILL
    right = right_world(t, f, boil)
    if t >= FALL0:                                      # the slope alone, lit up
        b = 1 + 0.12 * E.step(t, FALL0 + 0.6, FALL0 + 1.6)
        if b != 1: right = ImageEnhance.Brightness(right).enhance(round(b * 40) / 40)
        rx, ry, _ = rock_pos(t)
        right.alpha_composite(E.glow_spot((rx - 420, ry - 300, rx + 300, ry + 260), alpha=int(70 * E.step(t, FALL0 + 0.6, FALL0 + 1.6)), blur=110))
    c.alpha_composite(right)
    if t < SPLIT0: return
    tear_y = -30 + (E.H + 90) * E.step(t, SPLIT0, SPLIT1) ** 0.8
    m = left_mask()
    if t < SPLIT1 + 0.05:                               # the tear runs down the picture; then the left half becomes the pit
        draw_seam(c, tear_y)
        return
    left = left_world(t, f, boil)
    if t < FALL0:
        c.paste(left, (0, 0), m)
        draw_seam(c, tear_y)
        return
    u = t - FALL0                                       # the left half drops away, tilting from its torn edge
    if u > 1.3: return
    piece = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); piece.paste(left, (0, 0), m)
    draw_seam(piece, E.H + 60)
    rot = 9 * min(1, u / 0.3) + 14 * max(0, u - 0.3)
    piece = piece.rotate(rot, resample=Image.BICUBIC, center=(SEAM_X, 0))
    dy = int(1700 * max(0, u - 0.12) ** 2); dx = int(-140 * u)
    E.safe(c, piece, dx, dy)


SCENES = [E.Scene(0, DUR, scene_split, bg=None)]

LABELS = [
    E.Label("الشعور بالذنب", (), [T["shuur"], T["bidhanb"]], hide=FALL0, x=1440, y=150, size=80),
    E.Label("الخزي", ("الخزي",), [T["khizy"]], hide=FALL0, x=480, y=150, size=110),
    E.Label("لا تجعل الذنبَ يهزم توبتك", ("توبتك",),
            [T["la"], T["tajal"], T["dhanb"], T["yahzim"], T["tawbatak"]], hide=DUR, y=165, size=104),
]


def post(arr, t, f, idx):
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys12"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
