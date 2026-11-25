"""بصيرة · فيديو سيزيف · الجزء ١٦: «لستَ سيزيف» (7:30–8:05). The last part: back on the clay hill. Sisyphus lies at the
foot; «you are not Sisyphus»; he rises, puts his hands on the rock, a new path appears, a lit village on the peak;
then the channel logo."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import basira_engine as E
import part_4 as P4                                    # same hill, same scale
import part_5 as P5                                    # same foot of the hill, same rock rest

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "proj", "frames16"); os.makedirs(OUT, exist_ok=True)
put, zoom_on = P4.put, P4.zoom_on
PUSH_H, ROCK_H, FALL_H, WALK_H = P4.PUSH_H, P4.ROCK_H, P4.FALL_H, P5.WALK_H
RISE_H = int(WALK_H * 0.64 * E.load("sis_rise").height / 748)   # kneeling: head the same size as when standing

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(sizif=0.3, khiyar=2.0, hakamat=2.8, yaud=4.2, qaa=4.8, abad=5.3, amma=6.6, anta=7.2, falasta=8.6, sizif2=9.2,
         kull=10.6, khatta=11.6, khayr=12.4, khattain=13.0, tawwabun=13.8, fain=15.2, aflata=15.8, sakhra=16.4,
         latajlis=17.4, qaa2=18.2, da=18.8, yadayk=19.2, jadid=20.0, waghayyir=20.8, tariq=21.4, tasad=22.2,
         akhbirni=23.6, taaliqat=24.8, saadak=26.2, nuhud=27.0, suqut=27.8,
         basira=29.6, nara=30.6, wara=31.4, hikaya=31.9)
_tj = os.path.join(HERE, "proj", "times_16.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["hikaya"] + 3.2
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice
LOGO0 = T["basira"] - 0.2

# ------------------------------------------------------------------ the new path up the hill (world = screen at zoom 1)
FOOT, _ = P5.on_path(P5.ROCK0)
NEW = [FOOT, (820, 880), (1110, 745), (1310, 560), (1440, 360), (1510, 225)]
NSEG = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(NEW, NEW[1:])]
GAP = (E.scaled("sis_push", PUSH_H).width * 0.5 + ROCK_H * 0.5 - 70) / sum(NSEG)
VILLAGE = (1545, 165, 150)


def on_new(s):
    d = max(-0.2, min(1.0, s)) * sum(NSEG)
    if d < 0:
        (a, b), L = (NEW[0], NEW[1]), NSEG[0]
        return (a[0] + (b[0] - a[0]) * d / L, a[1] + (b[1] - a[1]) * d / L), math.degrees(math.atan2(a[1] - b[1], b[0] - a[0]))
    for (a, b), L in zip(zip(NEW, NEW[1:]), NSEG):
        if d <= L or L == NSEG[-1]:
            u = min(1, d / L)
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), math.degrees(math.atan2(a[1] - b[1], b[0] - a[0]))
        d -= L


S0 = 0.02


def climb(t):
    """stepped heavy shoves up the new path"""
    t0, t1 = T["tariq"] + 0.3, T["basira"] - 0.4
    if t < t0: return S0
    u = min(1.0, (t - t0) / (t1 - t0)); n = 9
    k = u * n; steps = math.floor(k) + min(1, (k % 1) / 0.35)
    return S0 + (0.68 - S0) * min(n, steps) / n


def draw_path(c, t, f):
    if t < T["waghayyir"] - 0.1: return
    k = E.step(t, T["waghayyir"] - 0.1, T["tariq"] + 0.6)
    L = sum(NSEG) * k
    pts = []; d = 0.0
    for (a, b), Ls in zip(zip(NEW, NEW[1:]), NSEG):
        for i in range(0, int(Ls), 6):
            if d + i > L: break
            u = i / Ls; pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
        d += Ls
    if len(pts) < 2: return
    r = np.random.default_rng(7 + (f // 2) % 3)
    pts = [(x + r.normal(0, 1.2), y + 6 + r.normal(0, 1.2)) for x, y in pts]
    d_ = ImageDraw.Draw(c)
    d_.line(pts, fill=(60, 40, 30, 255), width=22, joint="curve")          # ink edge
    d_.line(pts, fill=(236, 214, 170, 255), width=14, joint="curve")       # a torn cream strip: the new way up


def world(t, f):
    c = E.image_bg("hill", f, pan=0.5, sat=0.95)
    warm = E.step(t, T["falasta"], T["sizif2"] + 2.0)
    if warm:                                                # warm light at the horizon behind the peak
        c.alpha_composite(E.glow_spot((1150, -250, 2150, 450), color=(255, 205, 130), alpha=int(110 * warm), blur=150))
    if t >= T["taaliqat"] - 0.1:                            # a lit village on the empty peak
        k = E.step(t, T["taaliqat"] - 0.1, T["taaliqat"] + 0.6)
        x, y, h = VILLAGE
        c.alpha_composite(E.glow_spot((x - 260, y - 160, x + 260, y + 120), color=(255, 214, 150), alpha=int(120 * k), blur=90))
        E.paste(c, E.scaled("village_good", h), x, y + 60 * (1 - k), alpha=min(1, k * 1.5), seed=63, f=f)
    draw_path(c, t, f)
    rx = FOOT
    if t < T["tawwabun"]:                                   # lying at the foot, the rock beside him
        P5.rock_at(c, f, P5.ROCK0)
        E.paste(c, E.scaled("sis_fallen", FALL_H), FOOT[0] + 360, FOOT[1] - FALL_H / 2 + 10, rot=-4, seed=3, f=f)
    elif t < T["tawwabun"] + 0.9:                           # «التوّابون»: on one knee, head lifted
        P5.rock_at(c, f, P5.ROCK0)
        E.paste(c, E.scaled("sis_rise", RISE_H), FOOT[0] + 330, FOOT[1] + 8 - RISE_H / 2, seed=3, f=f)
    elif t < T["tawwabun"] + 1.6:                           # standing, same feet
        P5.rock_at(c, f, P5.ROCK0)
        E.paste(c, E.scaled("sis_walk", WALK_H), FOOT[0] + 330, FOOT[1] + 5 - WALK_H / 2, seed=3, f=f)
    elif t < T["latajlis"]:                                 # he walks round behind the rock
        P5.rock_at(c, f, P5.ROCK0)
        k = E.step(t, T["tawwabun"] + 1.6, T["latajlis"] - 0.1)
        x = FOOT[0] + 330 - (330 + 250) * k
        bob = 0 if k in (0, 1) else (6 if f % 2 else 0)
        E.paste(c, E.scaled("sis_walk_l", WALK_H), x, FOOT[1] + 5 - WALK_H / 2 - bob, seed=3, f=f)
    else:                                                   # «ضع يديك عليها»… then up the new path
        s = climb(t)
        rp, ang = on_new(s); sp, _ = on_new(s - GAP)
        put(c, "sis_push", PUSH_H, sp, ang, f, 3)
        put(c, "rock", ROCK_H, rp, ang, f, 8, lift=-14, rot_extra=-((s * 900) % 360))
    return c


def camera(t):
    near = (FOOT[0] + 150, FOOT[1] - 170)
    wide = (1000, 540)
    if t < T["abad"]: return 1.8, near
    if t < T["tawwabun"] - 0.6:
        u = E.step(t, T["abad"], T["abad"] + 1.8); return 1.8 - 0.8 * u, (near[0] + (wide[0] - near[0]) * u, near[1] + (wide[1] - near[1]) * u)
    if t < T["waghayyir"]:
        u = E.step(t, T["tawwabun"] - 0.6, T["tawwabun"]); return 1.0 + 0.7 * u, (wide[0] + (near[0] - wide[0]) * u, wide[1] + (near[1] - wide[1]) * u)
    u = E.step(t, T["waghayyir"], T["tariq"] + 0.8)
    return 1.7 - 0.6 * u, (near[0] + (wide[0] - near[0]) * u, near[1] + (wide[1] - near[1]) * u)


def scene_hill(t, f, c):
    z, (cx, cy) = camera(t)
    c.alpha_composite(zoom_on(world(t, f), round(z * 40) / 40, cx, cy))


# ------------------------------------------------------------------ the logo: the mark, then the full logo
@functools.lru_cache(None)
def logo_parts():
    full = Image.open(os.path.join(HERE, "proj", "bg", "basira_logo_full.png")).convert("RGBA")
    bgc = full.getpixel((40, 40))
    a = np.asarray(full.convert("RGB")).astype(int)
    ink = np.abs(a - np.array(bgc[:3])).sum(2) > 60
    ink[:, :] &= True
    ys, xs = np.where(ink[380:720, 1020:1300]); mark_box = (1020 + xs.min() - 6, 380 + ys.min() - 6, 1020 + xs.max() + 7, 380 + ys.max() + 7)
    ys, xs = np.where(ink[380:720, 600:1015]); word_box = (600 + xs.min() - 6, 380 + ys.min() - 6, 600 + xs.max() + 7, 380 + ys.max() + 7)
    base = full.copy(); d = ImageDraw.Draw(base)
    d.rectangle(mark_box, fill=bgc); d.rectangle(word_box, fill=bgc)
    return full, base, full.crop(mark_box), mark_box, full.crop(word_box), word_box


def scene_logo(t, f, c):
    full, base, mark, mb, word, wb = logo_parts()
    img = base.copy()
    t0 = LOGO0 + 0.5
    if t >= t0:                                             # the mark pops in big, then settles into its place
        j = int((t - t0) * E.FPS); pop = {0: 0.6, 1: 1.08, 2: 0.97}.get(j, 1.0)
        u = E.step(t, T["nara"] - 0.1, T["nara"] + 0.6)
        s = (1.9 + (1.0 - 1.9) * u) * pop
        mx, my = (mb[0] + mb[2]) / 2, (mb[1] + mb[3]) / 2
        cx, cy = 960 + (mx - 960) * u, 540 + (my - 540) * u
        im = mark.resize((int(mark.width * s), int(mark.height * s)), Image.LANCZOS)
        img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
    if t >= T["nara"] + 0.4:                                # «نرى ما وراء الحكاية»: the words ink in right to left
        w = E.step(t, T["nara"] + 0.4, T["hikaya"] + 0.3)
        cut = int(word.width * (1 - w))
        piece = word.crop((cut, 0, word.width, word.height))
        img.alpha_composite(piece, (wb[0] + cut, wb[1]))
    c.alpha_composite(img)


SCENES = [
    E.Scene(0, LOGO0, scene_hill, bg=None),
    E.Scene(LOGO0, DUR, scene_logo, bg=None, rip=True),
]

LABELS = [
    E.Label("فلستَ سيزيف", ("فلستَ", "سيزيف"), [T["falasta"], T["sizif2"]], hide=T["kull"] - 0.2, y=150, size=124),
    E.Label("خيرُ الخطّائين التوّابون", ("التوّابون",), [T["khayr"], T["khattain"], T["tawwabun"]], hide=T["latajlis"] - 0.3, y=150, size=96),
]


def post(arr, t, f, idx):
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys16"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
