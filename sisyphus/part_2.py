"""بصيرة · فيديو سيزيف · الجزء ٢: «عالمٌ بلا موت» (0:30–1:00)."""
import sys, os, json, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageOps
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "frames2")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates)
T = dict(quyyid=0.4, fatawaqqaf=1.5, almawt=2.1, ashaykh=3.5, wala_jarih=4.7, ghadibat=6.0,
         ilah_alharb=7.5, qaydahu=9.5, waakhadh=11.0, marratan=14.0, ukhra=14.5, yawman=17.0,
         faad=19.5, walam=22.0, yadhak=25.5, ala=26.0, almawt2=26.4)
_tj = os.path.join(HERE, "proj", "times_2.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["almawt2"] + 2.6
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice

FEET = 1000
SIS_H = 700                                           # same Sisyphus as part 1
GEST_H = int(round(E.load("sis_gesture").height * SIS_H / E.load("sis_walk").height))
CHAINED_H = int(round(E.load("death_chained").height * 760 / E.load("death_fly").height))


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


# ------------------------------------------------------------------ 1. Corinth: Death chained to a column
DEATH_X = 1080
COLUMN = (640, 600)                                  # a temple column in the background
HANDS = (DEATH_X + 5, FEET - CHAINED_H * 0.57)


def chain_link(c, f, u_break=0.0):
    """Chain from Death's wrists to the column; on «قيده» it snaps into three pieces that fly apart."""
    ch = E.load("chain")
    L = math.hypot(HANDS[0] - COLUMN[0], HANDS[1] - COLUMN[1])
    im = ImageOps.mirror(ch).resize((int(L + 60), int((L + 60) * ch.height / ch.width)), Image.LANCZOS)
    ang = -math.degrees(math.atan2(HANDS[1] - COLUMN[1], HANDS[0] - COLUMN[0]))
    mx, my = (HANDS[0] + COLUMN[0]) / 2, (HANDS[1] + COLUMN[1]) / 2
    if u_break <= 0:
        E.paste(c, im, mx, my, rot=ang, seed=21, f=f); return
    n = 3; w = im.width // n
    for i in range(n):
        part = im.crop((i * w, 0, (i + 1) * w, im.height))
        off = (i - 1) * w
        vx, vy, spin = (-520, -260, -160), (-300, -420, -240), (-90, 140, 220)
        x = mx + off * math.cos(math.radians(ang)) + vx[i] * u_break
        y = my - off * math.sin(math.radians(ang)) + vy[i] * u_break + 900 * u_break ** 2
        E.paste(c, part, x, y, rot=ang + spin[i] * u_break, seed=22 + i, f=f)


def corinth_bg(t, f, red=0.0):
    c = E.image_bg("corinth", f, pan=0.62 + 0.1 * min(1, t / 11), blur=1.5, sat=0.8)
    return darken(c, 0.12)


def scene_chained(t, f, c):
    c.alpha_composite(corinth_bg(t, f))
    if t < T["qaydahu"]:
        bottom_paste(c, "death_chained", CHAINED_H, DEATH_X, FEET, 4, f)
        chain_link(c, f)
    else:
        # Death is free: wings out, rising out of the frame
        k = E.step(t, T["qaydahu"] + 0.35, T["qaydahu"] + 1.4)
        bottom_paste(c, "death_fly", 760, DEATH_X, FEET - 1900 * k, 4, f)
        u = min(1.0, (t - T["qaydahu"]) / 0.9)
        if u < 1: chain_link(c, f, u_break=max(0.05, u))
    # the hourglass drops into the corner on «فتوقّف» and its sand stays frozen
    if t >= T["fatawaqqaf"]:
        E.drop_in(c, "hourglass", 420, t, T["fatawaqqaf"], T["fatawaqqaf"] + 0.5, 250, 330, f, seed=31)
    # Ares on «إله الحرب»: drops in from the right, sword raised, facing Death
    if t >= T["ilah_alharb"]:
        k = E.step(t, T["ilah_alharb"], T["ilah_alharb"] + 0.6)
        lunge = 10 if T["qaydahu"] - 0.15 <= t < T["qaydahu"] + 0.25 else 0
        bottom_paste(c, "ares_l", 820, 1560 - 120 * E.step(t, T["qaydahu"] - 0.2, T["qaydahu"]),
                     -820 + (FEET - 40 + 820) * k, 6, f, extra=lunge)


# ------------------------------------------------------------------ 2. flashes: nobody can die
def scene_undying(t, f, c):
    if t < T["wala_jarih"]:
        z = 1 + 0.06 * (t - T["ashaykh"])
        im = E.scaled("old_man", int(560 * z))
        E.paste(c, im, 960, 560, seed=41, f=f)
    else:
        k = E.step(t, T["wala_jarih"], T["wala_jarih"] + 0.7)          # the wounded soldier rises
        bottom_paste(c, "wounded", 640, 960, FEET + 30 + 160 * (1 - k), 42, f)


# ------------------------------------------------------------------ 3. the underworld
HADES_X, SIS_X = 520, 1400
SHAFT_FLOOR, SHAFT_TOP = (1010, 900), (1180, -60)     # the light shaft on screen


def underworld(t, f):
    c = E.image_bg("underworld", f, pan=0.5, blur=1.0, sat=0.9)
    c = darken(c, 0.18)
    up = E.step(t, T["faad"], T["faad"] + 1.0)
    c.alpha_composite(E.glow_spot((SHAFT_FLOOR[0] - 260, 120, SHAFT_FLOOR[0] + 340, 1000),
                                  color=(255, 236, 190), alpha=int(28 + 50 * up), blur=110))
    bottom_paste(c, "hades", 720, HADES_X, FEET + 20, 51, f)
    return c


def scene_under(t, f, c):
    c.alpha_composite(underworld(t, f))
    if t < T["marratan"]:
        bottom_paste(c, "sis_kneel", 560, SIS_X, FEET + 10, 3, f)
    elif t < T["faad"]:
        turn = int((t - T["marratan"]) * E.FPS) == 0
        bottom_paste(c, "sis_gesture", GEST_H, SIS_X, FEET, 3, f, extra=7 if turn else 0)
    else:
        # «فعاد»: he steps into the light, then climbs it out of the cave, getting smaller
        k1 = E.step(t, T["faad"], T["faad"] + 0.7)
        k2 = E.step(t, T["faad"] + 0.7, T["faad"] + 2.3)
        x = SIS_X + (SHAFT_FLOOR[0] - SIS_X) * k1 + (SHAFT_TOP[0] - SHAFT_FLOOR[0]) * k2
        feet = FEET + (SHAFT_TOP[1] + 200 - FEET) * k2
        h = SIS_H * (1 - 0.45 * k2)
        if k2 < 1:
            bob = 0 if k1 >= 1 and k2 <= 0 else (8 if f % 2 else 0)
            bottom_paste(c, "sis_walk_l" if k2 <= 0 else "sis_walk", h, x, feet - bob, 3, f)


# ------------------------------------------------------------------ 4. years pass: the calendar
CAL = E.pieces("calendar")


def scene_calendar(t, f, c):
    c.alpha_composite(darken(E.image_bg("corinth", f, pan=0.5, blur=2.5, sat=0.7), 0.3))
    blk = CAL[0].resize((int(CAL[0].width * 1.35), int(CAL[0].height * 1.35)), Image.LANCZOS)
    E.paste(c, blk, 860, 520, seed=61, f=f)
    page = CAL[1]
    t0 = T["walam"]
    r = np.random.default_rng(5)
    for i in range(40):                              # a page tears off every ~0.08 s, faster and faster
        s = t0 + 0.25 + 0.11 * i * (1 - i / 90)
        u = t - s
        if u < 0 or u > 1.4: continue
        dx, sp, rot0 = r.uniform(250, 700), r.uniform(0.8, 1.2), r.uniform(-30, 30)
        x = 1020 + dx * u * sp; y = 520 + 900 * u * u * sp - 120 * u
        E.paste(c, page.rotate(rot0 + 260 * u * sp, expand=True, resample=Image.BICUBIC), x, y, seed=70 + i, f=f)


# ------------------------------------------------------------------ 5. the laughing king
FACE = None


def scene_throne(t, f, c):
    global FACE
    base = darken(E.image_bg("corinth", f, pan=0.4, blur=2.5, sat=0.85), 0.2)
    im = E.scaled("sis_throne", 860)
    if FACE is None: FACE = (960 - im.width / 2 + im.width * 0.6, FEET + 20 - im.height + im.height * 0.2)
    bottom_paste(base, "sis_throne", 860, 960, FEET + 20, 3, f)
    E.confetti(base, t - T["yadhak"], f)
    z = 1 + 0.45 * E.step(t, T["yadhak"] + 0.3, T["almawt2"] + 1.2)
    c.alpha_composite(zoom_on(base, round(z * 40) / 40, FACE[0], FACE[1] + 120))


SCENES = [
    E.Scene(0, T["ashaykh"], scene_chained, bg=None),
    E.Scene(T["ashaykh"], T["ghadibat"], scene_undying, rip=False),
    E.Scene(T["ghadibat"], T["waakhadh"], scene_chained, bg=None, rip=False),
    E.Scene(T["waakhadh"], T["walam"], scene_under, bg=None, rip=True),
    E.Scene(T["walam"], T["yadhak"], scene_calendar, bg=None, rip=True),
    E.Scene(T["yadhak"], DUR, scene_throne, bg=None, rip=True),
]

LABELS = [
    E.Label("توقّف الموت", ("توقّف", "الموت"), [T["fatawaqqaf"], T["almawt"]], hide=T["ashaykh"]),
    E.Label("مرةً أخرى", ("مرةً", "أخرى"), [T["marratan"], T["ukhra"]], hide=T["yawman"], x=1000),
    E.Label("١", ("١",), [T["yawman"]], hide=T["faad"], x=HADES_X - 170, y=300, size=96),
    E.Label("يضحك على الموت", ("يضحك",), [T["yadhak"], T["ala"], T["almawt2"]], hide=DUR, x=1420, y=150),
]


def post(arr, t, f, idx):
    # hard cuts into / out of the flashes: one bright frame
    for tc in (T["ashaykh"], T["wala_jarih"], T["ghadibat"]):
        if int(math.floor((t - tc) * E.FPS + 1e-6)) == 0: arr = arr * 0.6 + 250 * 0.4
    # «غضبت»: a distant strike in the sky, then the sky stays a little red
    if T["ghadibat"] <= t < T["waakhadh"]:
        g = np.linspace(1, 0, E.H)[:, None, None] ** 1.5
        red = 0.18 * E.step(t, T["ghadibat"], T["ghadibat"] + 1.0)
        arr = arr * (1 + red * g * np.array([0.6, -0.35, -0.45])[None, None, :])
        k = int(math.floor((t - T["ghadibat"]) * E.FPS + 1e-6))
        if k in (0, 1, 3):
            im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
            bolt = E.bolt_layer(3 if k < 3 else 4, 640, 200)
            im.alpha_composite(bolt)
            arr = np.asarray(im.convert("RGB")).astype(float)
            if k == 1: arr = arr * 0.75 + 250 * 0.25
    # Ares' sword breaks the chain: a hard jolt
    k = int(math.floor((t - T["qaydahu"]) * E.FPS + 1e-6))
    if k in (0, 1):
        arr = np.roll(arr, (12 if k == 0 else -12, -10 if k == 0 else 8), axis=(1, 0))
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys2"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
