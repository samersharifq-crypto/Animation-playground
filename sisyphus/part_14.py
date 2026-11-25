"""بصيرة · فيديو سيزيف · الجزء ١٤: «الرجل الذي سأل» (6:30–7:00). The hadith of the man who killed a hundred,
told only with places and light: a night desert, the man from behind, numbers the wind erases, a hermitage whose
light goes out, a scholar's house whose light grows, a lit village ahead and a dark one behind."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from scipy import ndimage
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "frames14"); os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(hadha=0.0, hadith=1.0, qabl=3.0, qarnan=4.2, rajul=5.0, qatala=6.8, tisa=7.5, tisin=8.0, nafsan=8.6,
         rahiban=10.0, hal=10.8, tawba=11.6, la=13.0, faatamma=13.6, mia=14.0, thumma=15.2, alim=16.0,
         naam=18.0, waman=18.6, yahul=19.0, baynahu=19.4, wabayn=19.8, tawba2=20.3,
         intaliq=21.2, ard=22.0, kadha=22.5, unasan=24.0, latarji=25.6, ardik=26.3, ardu=27.2, su=27.7)
_tj = os.path.join(HERE, "proj", "times_14.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["su"] + 2.6
TURN = T["ardu"] - 0.35                                 # the camera turns round to the dark village behind him


def zoom_on(img, z, cx, cy):
    if z <= 1.0001: return img
    cw, ch = E.W / z, E.H / z
    x = float(np.clip(cx - cw / 2, 0, E.W - cw)); y = float(np.clip(cy - ch / 2, 0, E.H - ch))
    return img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((E.W, E.H), Image.BICUBIC)


# ------------------------------------------------------------------ numbers written in the sand, erased by the wind
SAND = (34, 40, 58)                                     # dark groove colour in the moonlit sand


@functools.lru_cache(None)
def sand_number(text):
    font = ImageFont.truetype(E.FONT, 420)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = int(tmp.textlength(text, font=font)) + 60
    im = Image.new("L", (tw, 580), 0)
    ImageDraw.Draw(im).text((30, 0), text, font=font, fill=255)
    im = im.resize((tw, 270), Image.LANCZOS)            # lying flat on the sand: squashed in perspective
    return im


@functools.lru_cache(None)
def _erode_noise(w, h, seed):
    r = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(r.random((h, w)), 6)
    n = (n - n.min()) / (n.max() - n.min())
    xs = np.linspace(0, 1, w)[None, :]
    return 0.55 * n + 0.45 * (1 - xs)                   # the wind comes from the right: the right side goes first


def draw_number(c, text, t, t_write, t_erase, cx, cy, seed):
    if t < t_write or t > t_erase + 1.3: return
    m = sand_number(text)
    a = np.asarray(m).astype(float) / 255
    w = E.step(t, t_write, t_write + 0.9)               # written right to left with a finger
    cut = int(m.width * (1 - w))
    a[:, :cut] = 0
    if t > t_erase:
        e = (t - t_erase) / 1.1
        a = a * (_erode_noise(m.width, m.height, seed) > e)
        a = ndimage.shift(a, (0, -40 * e), order=0)
    lay = np.zeros((m.height, m.width, 4), np.uint8)
    lay[..., :3] = SAND; lay[..., 3] = (a * 245).astype(np.uint8)
    hl = np.zeros_like(lay); hl[..., :3] = (210, 214, 220); hl[..., 3] = (np.roll(a, 4, axis=0) * 90).astype(np.uint8)
    im = Image.fromarray(hl, "RGBA"); im.alpha_composite(Image.fromarray(lay, "RGBA"))   # moonlit lip under each groove
    E.safe(c, im, int(cx - m.width / 2), int(cy - m.height / 2))
    if t > t_erase - 0.1:
        wind(c, t, t_erase, cy)


def wind(c, t, t0, cy):
    """sand blown off to the left"""
    d = ImageDraw.Draw(c); r = np.random.default_rng(int(t0 * 10))
    u = t - t0
    if u > 1.6: return
    for i in range(90):
        x0 = r.uniform(900, 2100); y0 = cy + r.normal(0, 70); sp = r.uniform(700, 1300)
        x = x0 - sp * u; L = r.uniform(14, 40)
        if -40 < x < E.W:
            d.line([(x, y0 - 10 * u), (x + L, y0 - 10 * u)], fill=(214, 210, 196, int(200 * max(0, 1 - u / 1.6))), width=2)


# ------------------------------------------------------------------ the places and their light
TRAV_H = 560; TRAV = (700, 1000)                         # bottom-centre of the traveler
HERM = (1480, 600, 300); SCHOLAR = (320, 650, 300); VGOOD = (1470, 560, 240)
HERM_WIN = (376, 210)                                   # the glowing window in hermitage cut-out px


def place(c, name, x, y, h, t, t0, f, seed, bright=1.0):
    if t < t0 - 0.1: return None
    k = E.step(t, t0 - 0.1, t0 + 0.5)
    im = E.scaled(name, h)
    if bright != 1.0: im = ImageEnhance.Brightness(im).enhance(round(bright * 20) / 20)
    E.paste(c, im, x, y + 90 * (1 - k), alpha=min(1.0, k * 1.6), seed=seed, f=f)
    return im


def hermitage(c, t, f):
    t_off = T["la"]
    gone = E.step(t, T["thumma"], T["thumma"] + 0.6)
    if gone >= 1: return
    dark = 1 - 0.4 * E.step(t, t_off, t_off + 0.25)
    x, y, h = HERM
    y += 120 * gone
    im = place(c, "hermitage", x, y, h, t, T["rahiban"], f, 61, bright=dark)
    if im is None: return
    s = h / E.load("hermitage").height
    wx, wy = x - im.width / 2 + HERM_WIN[0] * s, y - im.height / 2 + HERM_WIN[1] * s
    if t < t_off:                                       # the window glows, then goes out on «لا»
        c.alpha_composite(E.glow_spot((wx - 90, wy - 90, wx + 90, wy + 90), color=(255, 205, 120), alpha=150, blur=30))
    else:
        d = ImageDraw.Draw(c); d.rectangle((wx - 15, wy - 21, wx + 15, wy + 21), fill=(26, 22, 20, 255))


def scholar(c, t, f):
    x, y, h = SCHOLAR
    fade = E.step(t, T["ard"] - 0.2, T["ard"] + 0.8)
    if fade >= 1: return
    im = place(c, "scholar_house", x, y, h, t, T["alim"], f, 62)
    if im is None: return
    grow = E.step(t, T["alim"] + 0.3, T["naam"] + 0.6)
    door = (x - 20, y + 60)
    a = int((60 + 120 * grow) * (1 - fade))
    c.alpha_composite(E.glow_spot((door[0] - 160 - 120 * grow, door[1] - 140 - 80 * grow, door[0] + 160 + 120 * grow, door[1] + 160 + 80 * grow),
                                  color=(255, 210, 140), alpha=a, blur=80))


def village_good(c, t, f):
    x, y, h = VGOOD
    im = place(c, "village_good", x, y, h, t, T["ard"], f, 63)
    if im is None: return
    k = E.step(t, T["ard"], T["unasan"] + 0.4)
    c.alpha_composite(E.glow_spot((x - 420, y - 200, x + 420, y + 160), color=(255, 214, 150), alpha=int(130 * k), blur=120))
    c.alpha_composite(E.glow_spot((x - 900, y - 40, x + 900, y + 60), color=(255, 226, 170), alpha=int(70 * k), blur=60))   # horizon line lights up


def traveler(c, t, f):
    if t < T["rajul"] - 0.6: return
    k = E.step(t, T["rajul"] - 0.6, T["rajul"] + 0.8)
    bob = 0 if k >= 1 else (6 if f % 2 else 0)
    im = E.scaled("traveler_back", TRAV_H)
    im = ImageEnhance.Brightness(im).enhance(0.9)
    E.paste(c, im, TRAV[0] - 260 * (1 - k), TRAV[1] - im.height / 2 - bob, seed=71, f=f)


def scene_desert(t, f, c):
    pan = 0.35 + 0.25 * E.step(t, T["intaliq"], T["kadha"] + 0.6)
    img = E.image_bg("desert_night", f, pan=pan, sat=0.85)
    hermitage(img, t, f)
    village_good(img, t, f)
    scholar(img, t, f)
    draw_number(img, "٩٩", t, T["tisa"], T["nafsan"] + 0.6, 1300, 900, 1)
    draw_number(img, "١٠٠", t, T["mia"] - 0.1, T["mia"] + 1.0, 1300, 900, 2)
    traveler(img, t, f)
    z = 1 + 0.12 * E.step(t, T["ard"], T["unasan"] + 0.6)   # a slow stepped push toward the lit village
    c.alpha_composite(zoom_on(img, round(z * 40) / 40, 1300, 600))


def scene_behind(t, f, c):
    """«أرضُ سوء»: turned round - the village he came from, dark and cold"""
    img = E.image_bg("desert_night", f, pan=0.05, sat=0.6, blur=1.0)
    arr = np.asarray(img.convert("RGB")).astype(float)
    arr = E.drain(arr, 0.55) * 0.8
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    k = E.step(t, TURN, TURN + 0.6)
    vb = E.scaled("village_bad", 430)
    vb = ImageEnhance.Brightness(vb).enhance(0.72)
    E.paste(img, vb, 1000 + 140 * (1 - k), 600, seed=64, f=f)
    z = 1 + 0.08 * E.step(t, TURN + 0.4, DUR)
    c.alpha_composite(zoom_on(img, round(z * 40) / 40, 1000, 600))


SCENES = [
    E.Scene(0, TURN, scene_desert, bg=None),
    E.Scene(TURN, DUR, scene_behind, bg=None, rip=True),
]

LABELS = [
    E.Label("نعم، ومَن يحول بينه وبين التوبة؟", ("نعم،",),
            [T["naam"], T["waman"], T["yahul"], T["baynahu"], T["wabayn"], T["tawba2"]], hide=T["intaliq"] + 0.6, y=150, size=76),
    E.Label("أرضُ سوء", ("أرضُ", "سوء"), [T["ardu"], T["su"]], hide=DUR, y=150, size=96),
]


def post(arr, t, f, idx):
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys14"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
