"""بصيرة · فيديو سيزيف · الجزء ١: «ملكٌ قيّد الموت» (0:00–0:30)."""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))

# ------------------------------------------------------------------ timing (video seconds)
# Estimates from the brief. When the voice arrives, proj/times_1.json (written by sound_1.py
# from the real word timings) replaces them.
T = dict(qabl=0.5, korintha=2.5, aash=4.0, sisyphus=5.5, makran=8.0, wahina=8.6, mawt=9.0,
         lam_yahrub=11.5, ibtasam=12.5, arini=14.0, famadda=17.0, faaghlaqaha=19.0,
         lakin=21.0, fasakhra=24.0, ilal_yawm=25.5, warubbama=27.0, dahrajtaha=28.4,
         anta=29.0, ams=29.5)
_tj = os.path.join(HERE, "proj", "times_1.json")
if os.path.exists(_tj):
    T.update(json.load(open(_tj)))
DUR = T["ams"] + 1.9
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice

FEET = 1000                       # ground line for both characters
SIS_X, DEATH_X = 1250, 620


def h_of(name, ref, ref_h):
    """Same scale for two poses of one character (same source size) -> same height and feet."""
    return int(round(E.load(name).height * ref_h / E.load(ref).height))

SIS_H = 700
GEST_H = h_of("sis_gesture", "sis_walk", SIS_H)
DEATH_H = 760
CHAINED_H = h_of("death_chained", "death_fly", DEATH_H)


def alpha_box(im):
    a = np.asarray(im.getchannel("A")) > 0
    ys, xs = np.where(a)
    return xs.min(), ys.min(), xs.max(), ys.max()


def hand_point():
    """Tip of Sisyphus' open hand (leftmost opaque pixel in the arm band) in screen space."""
    im = E.scaled("sis_gesture", GEST_H)
    a = np.asarray(im.getchannel("A"))[int(im.height * .18):int(im.height * .45)] > 0
    ys, xs = np.where(a); i = xs.argmin()
    return SIS_X - im.width / 2 + xs[i] + 30, FEET - im.height + int(im.height * .18) + ys[i]

HAND = hand_point()
DEATH_HANDS = (DEATH_X + 5, FEET - CHAINED_H * 0.57)       # crossed wrists of death_chained


def bottom_paste(c, name, h, x, feet, seed, f, extra=0.0, rot=0.0):
    im = E.scaled(name, h)
    if extra:
        r = np.random.default_rng(f * 13 + seed)
        x += r.normal(0, extra); feet += r.normal(0, extra)
    E.paste(c, im, x, feet - im.height / 2, rot=rot, seed=seed, f=f)


def darken(img, k):
    if k <= 0: return img
    a = np.asarray(img.convert("RGB")).astype(float) * (1 - k)
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")


def zoom_on(img, z, cx, cy):
    if z <= 1.0001: return img
    cw, ch = E.W / z, E.H / z
    x = float(np.clip(cx - cw / 2, 0, E.W - cw)); y = float(np.clip(cy - ch / 2, 0, E.H - ch))
    return img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((E.W, E.H), Image.BICUBIC)


# ------------------------------------------------------------------ the world (Corinth at night)
def world(t, f):
    pan = 0.7 - 0.3 * min(1, t / T["lakin"])
    c = E.image_bg("corinth", f, pan=pan, blur=1.5, sat=0.8)
    c = darken(c, 0.15 * E.step(t, T["mawt"], T["mawt"] + 0.7))        # Death darkens the night

    # Sisyphus: walks in during his introduction, stops on «مكرًا», turns on «ابتسم»
    if t < T["ibtasam"]:
        k = E.step(t, T["aash"], T["makran"])
        bob = 0 if k >= 1 else (8 if f % 2 else 0)
        bottom_paste(c, "sis_walk", SIS_H, -300 + (SIS_X + 300) * k, FEET - bob, 3, f)
    else:
        turn = int((t - T["ibtasam"]) * E.FPS) == 0                    # one harder jolt on the turn
        bottom_paste(c, "sis_gesture", GEST_H, SIS_X, FEET, 3, f, extra=7 if turn else 0)

    # Death: drops in on «الموت», looms on «لم يهرب», settles on «فمدّ», chained on «فأغلقها»
    if t >= T["mawt"]:
        if t < T["faaghlaqaha"]:
            k = E.step(t, T["mawt"], T["mawt"] + 0.6)
            hover = 40 * (1 - E.step(t, T["famadda"], T["famadda"] + 1.2))
            feet = (FEET - hover) * k
            lunge = 6 if T["lam_yahrub"] <= t < T["lam_yahrub"] + 0.5 else 0
            bottom_paste(c, "death_fly", DEATH_H, DEATH_X, feet, 4, f, extra=lunge)
        else:
            bottom_paste(c, "death_chained", CHAINED_H, DEATH_X, FEET, 4, f)

    # the chain leaps from Sisyphus' hand to Death's wrists: 3 frames, the lock shuts on «فأغلقها»
    t0 = T["faaghlaqaha"] - 3 / E.FPS
    if t0 <= t < T["faaghlaqaha"]:
        u = (int((t - t0) * E.FPS) + 1) / 3
        x = HAND[0] + (DEATH_HANDS[0] - HAND[0]) * u
        y = HAND[1] + (DEATH_HANDS[1] - HAND[1]) * u - 120 * np.sin(np.pi * u)
        E.paste(c, E.scaled("chain", 150), x, y, rot=-25 + 40 * u, seed=9, f=f)
    return c


def camera(t):
    """zoom 1.0 -> 1.08 toward both of them from «أرني», stepped."""
    z = 1 + 0.08 * E.step(t, T["arini"], T["famadda"] + 1.5)
    return z, (DEATH_X + SIS_X) / 2, 560


def scene_corinth(t, f, c):
    z, cx, cy = camera(t)
    c.alpha_composite(zoom_on(world(t, f), round(z * 100) / 100, cx, cy))


SIS_FACE = (SIS_X - 40, FEET - GEST_H * 0.86)


def closeup(t, f):
    """«لكنّ هذه»: the same place, darker; the frame creeps toward the smiling face."""
    tw = min(t, T["fasakhra"] + 0.05)
    u = E.step(tw, T["lakin"], T["fasakhra"] + 1.0)
    z = round((1.55 + 0.45 * u) * 40) / 40
    img = zoom_on(world(t, f), z, SIS_FACE[0], SIS_FACE[1] + 60)
    return darken(img, 0.35)


def scene_close(t, f, c):
    c.alpha_composite(closeup(t, f))


# ------------------------------------------------------------------ the rock's shadow
ROCK_H, ROLL = 1500, 1.6


def rock_shadow():
    im = E.scaled("rock", ROCK_H)
    a = np.asarray(im.getchannel("A")).astype(float) * 0.85
    out = Image.new("RGBA", im.size, (12, 15, 24, 0))
    out.putalpha(Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)))
    return out
SHADOW = None


def dark_corinth(t, f):
    c = E.image_bg("corinth", f, pan=0.4, blur=1.5, sat=0.6)
    return darken(c, 0.62)


def scene_rock(t, f, c):
    global SHADOW
    if SHADOW is None: SHADOW = rock_shadow()
    u = min(1, max(0, (t - T["fasakhra"]) / ROLL))
    u = round(u * ROLL * E.FPS) / (ROLL * E.FPS)
    sx = E.W + SHADOW.width / 2 - (E.W + SHADOW.width) * u
    if t < T["fasakhra"] + ROLL:
        old, new = closeup(t, f), dark_corinth(t, f)
        m = Image.new("L", (E.W, E.H), 0)
        m.paste(255, (int(max(0, sx)), 0, E.W, E.H))
        old.paste(new, (0, 0), m)
        c.alpha_composite(old)
        r = np.random.default_rng(f)
        E.paste(c, SHADOW, sx + r.normal(0, 6), E.H / 2 + 60 + r.normal(0, 6), rot=220 * u, shadow=False)
    else:
        c.alpha_composite(dark_corinth(t, f))


# ------------------------------------------------------------------ myth <-> modern room flicker
FLASHES = [(T["warubbama"], T["warubbama"] + 3 / E.FPS),
           (T["warubbama"] + 0.55, T["warubbama"] + 0.55 + 2 / E.FPS),
           (T["anta"], T["anta"] + 4 / E.FPS),
           (T["ams"], 1e9)]                      # «أمس»: the room stays
PHONE = None


def room(t, f):
    c = E.image_bg("room", f, pan=0.5, sat=1.0)
    # phone screen on the bedside table (oversized-bg coords -> screen)
    c.alpha_composite(E.glow_spot((1380, 690, 1620, 860), alpha=60 + (20 if f % 2 else 0), blur=70))
    return c


def scene_end(t, f, c):
    if E.in_any(t, FLASHES):
        img = room(t, f)
        start = max(a for a, b in FLASHES if a <= t)
        if int((t - start) * E.FPS) == 0: img = E.glitch(img, f)
    else:
        img = dark_corinth(t, f)
        if any(int((t - b) * E.FPS) == 0 for a, b in FLASHES): img = E.glitch(img, f)
    c.alpha_composite(img)


def scene_after(t, f, c):
    if t >= T["warubbama"]: scene_end(t, f, c)
    else: scene_rock(t, f, c)


SCENES = [
    E.Scene(0, T["lakin"] - 0.1, scene_corinth, bg=None),
    E.Scene(T["lakin"] - 0.1, T["fasakhra"], scene_close, bg=None, rip=True),
    E.Scene(T["fasakhra"], DUR, scene_after, bg=None, rip=False),
]

LABELS = [
    E.Label("كورنثة", (), [T["korintha"]], hide=T["aash"], x=480, y=100),
    E.Label("سيزيف", ("سيزيف",), [T["sisyphus"]], hide=T["wahina"], x=SIS_X, y=170),
    E.Label("الموت", ("الموت",), [T["mawt"]], hide=T["lam_yahrub"], x=DEATH_X + 470, y=150),
    E.Label("دحرجتَها أنت أمس", ("دحرجتَها", "أنت", "أمس"), [T["dahrajtaha"], T["anta"], T["ams"]], hide=DUR),
]


def post(arr, t, f, idx):
    # the lock shuts: the screen jolts 2 frames (±12 px)
    k = int(np.floor((t - T["faaghlaqaha"]) * E.FPS + 1e-6))
    if k in (0, 1):
        arr = np.roll(arr, (12 if k == 0 else -12, -12 if k == 0 else 9), axis=(1, 0))
    # the rock's weight: small shake while it rolls
    if T["fasakhra"] <= t < T["fasakhra"] + ROLL:
        r = np.random.default_rng(f + 5)
        arr = np.roll(arr, (int(r.integers(-6, 7)), int(r.integers(-5, 6))), axis=(1, 0))
    # darkness before part 2
    if t > T["ams"] + 0.9:
        arr = arr * max(0.0, 1 - (t - T["ams"] - 0.9) / 0.9)
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys"); os.makedirs(out, exist_ok=True)
        for tt in ts:
            E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post)
