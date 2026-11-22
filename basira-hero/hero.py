"""«سمّوه البطل» - vertical Short (1080x1920, 12 fps stop-motion), 4th in the «أمة الدوبامين» series.
Noir collage: hard light pools, venetian-blind shadows, push-ins / pull-backs, dutch tilts, iris and
blind transitions, torn-paper rips, film flicker. All characters, props and backgrounds are the Gemini images.

  python3 prepare.py                 # cut-outs/backgrounds from assets/
  python3 hero.py sheet 1.0 3.5 ...  # render a few frames + sheet.png to check the look
  python3 hero.py 0 390 & python3 hero.py 390 780 & wait   # render every frame
  python3 tools/sound.py             # foley (+ narration/P1, P2 when they exist) -> mix.wav
  python3 hero.py encode basira_hero_v2.mp4
"""
import os, sys, math, json, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import basira_engine as E
import props as P
import noir as N
from cues import C, DUR

E.setup(HERE, os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
try:
    STATUS = json.load(open(os.path.join(HERE, "cut", "status.json")))
except FileNotFoundError:
    sys.exit("run `python3 prepare.py` first")
REAL = lambda k: STATUS.get(k) == "real"
W, H, CX = E.W, E.H, E.W / 2
step, paste, ramp, ease = E.step, E.paste, N.ramp, N.ease


@functools.lru_cache(None)
def fig(name, h):
    """Character cut-out scaled up with a little sharpening (the Gemini images are small)."""
    im = E.scaled(name, h)
    rgb = im.convert("RGB").filter(ImageFilter.UnsharpMask(2, 60, 2)); rgb.putalpha(im.getchannel("A"))
    return rgb


def fig_pt(name, h, cx, cy, fx, fy):
    im = fig(name, h); return cx + (fx - 0.5) * im.width, cy + (fy - 0.5) * im.height


def swing(t, amp=9, speed=2.4):
    return amp * math.sin(round(t * E.FPS / 2) * 2 / E.FPS * speed)


def flicker(f, seed=3, p=0.12, depth=0.35):
    """Bulb flicker: mostly 1, sometimes a dip."""
    r = np.random.default_rng(seed * 977 + f // 2)
    return 1 - depth * r.uniform() if r.uniform() < p else 1.0


# ====================================================================== part 1: البطل
BOT1 = (CX, 1080, 860)          # hook bottle: x, y, height


def s_hook(t, f, c):
    cracked = t >= C["akhtar"]
    x, y, h = BOT1
    paste(c, N.bottle(h, "bottle_cracked" if cracked else "bottle", letters=0), x, y, seed=12, f=f)
    px, py = N.neck_point(h, x, y)
    N.hang_medal(c, px, py, int(h * 0.26), swing(t), f)
    lit = 1.0 if not cracked else (0.15 if f % 3 == 0 and t < C["akhtar"] + 0.6 else 0.7)
    N.light(c, N.cone((CX, -40), (CX, 1500), 160, 820) * lit, dark=0.32, glow=0.18)


def cam_hook(t, f):
    z = ramp(t, 0, C["awakhir"], 1.0, 1.14)
    dx, dy = N.shake(f, t, C["akhtar"], 0.4, 26)
    return dict(z=z, fx=CX, fy=1060, dx=dx, dy=dy)


def s_lab(t, f, c):
    c.alpha_composite(E.image_bg("lab", f, pan=0.55, blur=0.6, sat=0.95))
    x = ramp(t, C["awakhir"], C["awakhir"] + 1.3, -260, 470)
    bob = 0 if t > C["awakhir"] + 1.3 else (10 if f % 2 else 0)
    paste(c, fig("chemist_k1", 1180), x, 1190 - bob, seed=3, f=f)
    m = np.maximum(N.cone((1020, 120), (300, 1700), 420, 900, 70) * 0.9, N.pool((120, 300, 1000, 1500), 160) * 0.55)
    N.light(c, m * N.blinds(-26, 74, 0.42, 0, 4) * 0.85 + m * 0.15, dark=0.4, glow=0.2)


def cam_lab(t, f):
    hx, hy = fig_pt("chemist_k1", 1180, 470, 1190, 0.8, 0.2)
    z = ramp(t, C["almania"] - 0.3, C["waadu"], 1.0, 1.45)
    return dict(z=z, fx=ramp(t, C["almania"] - 0.3, C["waadu"], CX, hx), fy=ramp(t, C["almania"] - 0.3, C["waadu"], 980, hy))


SCALE = (CX, 760, 1.05)          # post fork x, y, sheet scale


def balance_bg(t, f, c):
    c.alpha_composite(E.image_bg("lab", f, pan=0.5, zoom=1.35, blur=3.5, center=(470, 1150)))


def s_scale(t, f, c):
    balance_bg(t, f, c)
    k = step(t, C["akhaf"], C["akhaf"] + 0.5)
    over = 1 + 0.3 * math.sin(math.pi * min(1, (t - C["akhaf"]) / 0.55)) if t > C["akhaf"] else 1
    left = N.bottle(380, "bottle_morphine", "MORPHIN", 7)
    right = N.bottle(380, "bottle", letters=0)
    N.draw_scale(c, SCALE[0], SCALE[1], SCALE[2], -13 * k * over, left, right, f)
    N.light(c, N.cone((CX, -60), (CX, 1500), 260, 1100), dark=0.3, glow=0.16)


def cam_scale(t, f):
    z = ramp(t, C["waadu"], C["waadu"] + 1.2, 1.3, 1.0) + ramp(t, C["akhaf"], C["akhaf"] + 0.6, 0, 0.06)
    return dict(z=z, fx=CX, fy=ramp(t, C["waadu"], C["waadu"] + 1.2, 1150, 1000))


BOT4 = (CX, 1140, 1240)


def s_name(t, f, c):
    x, y, h = BOT4
    letters = sum(1 for i in range(6) if t >= C["heroin"] + i * 0.12)
    red = 4 if t >= C["shuja"] else 0
    paste(c, N.bottle(h, "bottle", "HEROIN", letters, red), x, y, seed=14, f=f)
    if t >= C["shuja"] - 0.08:
        lx, ly = N.label_point(h, x, y, fx=0.36, fy=0.0)
        P.paste_pop(c, P.card("الشجاع", 96, seed=5), lx, ly - 70, t, C["shuja"] - 0.08, f, seed=41, rot=-4)
    N.light(c, N.cone((CX + 120, -60), (CX, 1700), 200, 1100), dark=0.28, glow=0.15)


def cam_name(t, f):
    lx, ly = N.label_point(BOT4[2], BOT4[0], BOT4[1])
    z = ramp(t, C["ikhtaru"], C["heroin"], 1.0, 1.22)
    if t >= C["shuja"]: z += 0.14 * (1 - 0.3 * min(1, (t - C["shuja"]) / 1.0))
    rot = ramp(t, C["shuja"], C["shuja"] + 0.3, 0, -3)
    return dict(z=z, fx=lx, fy=ramp(t, C["ikhtaru"], C["heroin"], 1080, ly - 40), rot=rot)


def s_slam(t, f, c):
    balance_bg(t, f, c)
    k = step(t, C["akhaf2"], C["akhaf2"] + 0.2)
    left = N.bottle(380, "bottle_morphine", "MORPHIN", 7)
    right = N.bottle(380, "bottle", "HEROIN", 6, 4)
    N.draw_scale(c, SCALE[0], SCALE[1], SCALE[2], -13 + 38 * k, left, right, f)
    N.light(c, N.cone((CX, -60), (CX, 1500), 260, 1100), dark=0.3, glow=0.16)


def cam_slam(t, f):
    dx, dy = N.shake(f, t, C["akhaf2"], 0.5, 34)
    rot = ramp(t, C["akhaf2"], C["akhaf2"] + 0.2, 0, 5)
    return dict(z=1.06, fx=CX, fy=1000, dx=dx, dy=dy, rot=rot)


BOT6 = (830, 1250, 560)
MEDAL_FLOOR = 1450


def medal_pos(t):
    x, y, h = BOT6
    px, py = N.neck_point(h, x, y)
    dt = t - C["medal"]
    if dt < 0: return px, py, None
    fall = 0.5 * 3200 * dt * dt
    yy = min(py + fall, MEDAL_FLOOR - 60)
    landed = py + fall >= MEDAL_FLOOR - 60
    return px + min(dt, 0.45) * 120, yy, (-160 * min(dt, 0.45)) if not landed else -72


def s_chem2(t, f, c):
    c.alpha_composite(E.image_bg("lab", f, pan=0.7, blur=1.4, sat=0.9))
    paste(c, fig("chemist_k2", 1120), 350, 1160, seed=8, f=f)
    x, y, h = BOT6
    cracked = t >= C["medal"]
    paste(c, N.bottle(h, "bottle_cracked" if cracked else "bottle", "HEROIN", 6, 4), x, y, seed=16, f=f)
    mx, my, rot = medal_pos(t)
    mh = int(h * 0.26)
    if rot is None: N.hang_medal(c, mx, my, mh, swing(t, 6), f)
    else: paste(c, N.medal(mh).rotate(rot, resample=Image.BICUBIC, expand=True), mx, my + mh * 0.4, seed=64, f=f)
    if t >= C["x2"] - 0.08:
        big = t >= C["x5"]
        P.paste_pop(c, P.card("×5" if big else "×2", 190 if big else 160, seed=6), 820, 760, t, (C["x5"] if big else C["x2"]) - 0.08, f, seed=42, rot=4)
    lamp = 540 + 260 * math.sin(round(t * 6) / 6 * 1.6)              # a bare bulb swinging overhead
    m = N.cone((int(lamp / 20) * 20, -60), (int(lamp / 20) * 20, 1700), 140, 1000, 60)
    N.light(c, np.maximum(m, N.pool((100, 500, 1000, 1600), 200) * 0.35) * flicker(f, 7), dark=0.25, glow=0.2)


def cam_chem2(t, f):
    z = 1.0
    for key in ("x2", "x5"):
        if t >= C[key]: z += 0.09 * max(0, 1 - (t - C[key]) / 0.5)
    dx, dy = N.shake(f, t, C["x5"], 0.4, 22)
    if t >= C["medal"] + 0.6:
        mx, my, _ = medal_pos(t)
        k = ease((t - C["medal"] - 0.6) / 1.8)
        return dict(z=1.0 + 0.55 * k, fx=CX + (mx - CX) * k, fy=1000 + (my - 1000) * k)
    return dict(z=z, fx=CX, fy=1000, dx=dx, dy=dy, rot=ramp(t, C["chem2"], C["chem2"] + 3, 3, 0))


# ====================================================================== part 2: الجرعة
CIG_ROW = (230, 400, 570, 740)
COUNT_STEPS = ["4", "12", "85", "640", "2,900", "8,400", "14,700", "20,000"]
WORKER = (560, 1300, 820)
CLOCK = (840, 560, 250)


def machine_geom():
    m = E.scaled("machine", 760); return m, 760, 1190


def s_factory(t, f, c):
    c.alpha_composite(E.image_bg("factory", f, pan=0.45, blur=0.5, sat=0.95))
    ws = step(t, C["machine"], C["machine"] + 0.6)
    wx, wy, wh = WORKER
    paste(c, fig("worker", wh), wx - 250 * ws, wy, seed=5, f=f)
    if t >= C["arba"] - 0.2:
        turn = min(1, (t - C["arba"]) / (C["alfan"] + 1.4 - C["arba"]))
        N.draw_clock(c, CLOCK[0], CLOCK[1], CLOCK[2], turn, f)
    n = sum(1 for i in range(4) if t >= C["arba"] + i * 0.4)
    for i in range(n):
        paste(c, N.cig(i, 150, 0), CIG_ROW[i], 830, seed=80 + i, f=f)
    if t >= C["machine"]:
        m, mx, my = machine_geom()
        k = step(t, C["machine"], C["machine"] + 0.45)
        y = -m.height + (my + m.height) * k
        hum = (E.jit(f, 99, 4, 0.8) if t > C["machine"] + 0.6 else (0, 0, 0))
        paste(c, m, mx + hum[0], y + hum[1], rot=hum[2], seed=7, f=f)
        if not REAL("machine"):
            sc = m.height / P.machine_body().height
            spin = int(t * (420 if t > C["ishrin"] else 240)) // 15 * 15 % 360 if t > C["machine"] + 0.6 else 0
            paste(c, P.machine_wheel(int(170 * sc), spin), mx + P.MACHINE_WHEEL[0] * m.width + hum[0], y + P.MACHINE_WHEEL[1] * m.height + hum[1], seed=7, f=f)
    if t >= C["ishrin"]:
        m, mx, my = machine_geom()
        chute = (mx + P.MACHINE_CHUTE[0] * m.width, my + P.MACHINE_CHUTE[1] * m.height)
        P.pour(c, t, C["ishrin"], C["insan"] - 0.25, chute, 1100, N.cig_sprite, seed=5, top=-160, f=f)
    if t >= C["sajaer"] + 0.2:
        if t < C["ishrin"]:
            txt, t0, pos = "4", C["sajaer"] + 0.2, (250, 560)
        else:
            i = min(len(COUNT_STEPS) - 1, int((t - C["ishrin"]) / 0.18))
            txt, t0, pos = COUNT_STEPS[i], C["ishrin"] + i * 0.18, (CX, 820)
        P.paste_pop(c, P.card(txt, 170 if len(txt) < 5 else 140, seed=7), pos[0], pos[1], t, t0, f, seed=43, rot=-3)
    shafts = np.maximum(N.cone((640, 380), (200, 1800), 300, 900, 60), N.cone((960, 380), (700, 1800), 260, 800, 60))
    N.light(c, shafts * N.blinds(-14, 95, 0.18, 0, 3) * 0.8 + N.pool((60, 500, 1020, 1700), 180) * 0.45, dark=0.38, glow=0.16)


def cam_factory(t, f):
    if t < C["arba"]:                                     # open on the window, pull back to the worker
        z = ramp(t, C["qabl"], C["qabl"] + 2.6, 1.7, 1.0)
        return dict(z=z, fx=ramp(t, C["qabl"], C["qabl"] + 2.6, 640, CX), fy=ramp(t, C["qabl"], C["qabl"] + 2.6, 600, 1000))
    if t < C["machine"]:                                  # lean in on the slow minute
        return dict(z=ramp(t, C["arba"], C["machine"], 1.0, 1.18), fx=CX, fy=800)
    dx, dy = N.shake(f, t, C["machine"] + 0.45, 0.5, 30)
    if t < C["ishrin"]:
        return dict(z=ramp(t, C["machine"], C["machine"] + 0.5, 1.18, 1.0), fx=CX, fy=960, dx=dx, dy=dy)
    return dict(z=ramp(t, C["ishrin"], C["insan"], 1.0, 1.2), fx=CX, fy=900, rot=ramp(t, C["ishrin"], C["insan"], 0, -3))


STAMPS = (("أقوى", "aqwa", 900, -4), ("أسرع", "asra", 1120, 3), ("أكثر", "akthar", 1340, -2))


def s_cream(t, f, c):
    for word, key, y, rot in STAMPS:
        t0 = C[key]
        if t < t0: continue
        k = int((t - t0) * E.FPS)
        s = {0: 1.7, 1: 0.9, 2: 1.04}.get(k, 1.0)
        im = P.card(word, 160, seed=len(word) * 7)
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        paste(c, im, CX, y, rot=rot, seed=50 + len(word), f=f)
    N.light(c, N.blinds(-22, 120, 0.35, int(t * 20) % 120, 6) * 0.75 + 0.25, dark=0.55, glow=0.05)


def cam_cream(t, f):
    z = ramp(t, C["insan"], C["yawm"], 1.0, 1.08); dx = dy = 0
    for _, key, _, _ in STAMPS:
        if t >= C[key]:
            z += 0.07 * max(0, 1 - (t - C[key]) / 0.35)
            a, b = N.shake(f, t, C[key], 0.25, 20); dx += a; dy += b
    return dict(z=z, dx=dx, dy=dy)


YOUNG = (560, 1230, 860)


def phone_xy():
    return fig_pt("young", YOUNG[2], YOUNG[0], YOUNG[1], 0.68, 0.32)


def young_room(t, f, c, freeze=None):
    c.alpha_composite(E.image_bg("room", f, pan=0.5, blur=1.0))
    ph = phone_xy()
    tt = min(t, freeze or 1e9)
    args = (C["daqiqa"], C["fahal"] - 0.3, ph, 300, N.note_sprite)
    P.pour(c, tt, *args, seed=8, top=1050, f=f, only="landed")
    paste(c, fig("young", YOUNG[2]), YOUNG[0], YOUNG[1], seed=9, f=f)
    P.pour(c, tt, *args, seed=8, top=1050, f=f, only="flying")
    beat = 1 + (0.35 if (t > C["daqiqa"] and int((t - C["daqiqa"]) * 1.6) % 2 == 0) else 0)
    m = N.pool((ph[0] - 330, ph[1] - 330, ph[0] + 330, ph[1] + 330), 110)
    N.light(c, np.clip(m * beat, 0, 1), dark=0.3, warm=(210, 230, 255), glow=0.22)


def s_room(t, f, c):
    young_room(t, f, c)


def cam_room(t, f):
    ph = phone_xy()
    z = ramp(t, C["yawm"], C["yawm"] + 2.6, 1.9, 1.0)
    if t > C["daqiqa"] and int((t - C["daqiqa"]) * 1.6 * 2) % 4 == 0: z += 0.015
    return dict(z=z, fx=ramp(t, C["yawm"], C["yawm"] + 2.6, ph[0], CX), fy=ramp(t, C["yawm"], C["yawm"] + 2.6, ph[1], 1050))


def s_question(t, f, c):
    young_room(t, f, c, freeze=C["fahal"])
    k = step(t, C["fahal"], C["fahal"] + 1.2)
    a = np.asarray(c.convert("RGB")).astype(float)
    a = E.drain(a, 0.5 * k) * (1 - 0.12 * k)
    sh = N.blinds(-20, 110, 0.4, int((t - C["fahal"]) * 30), 5)[..., None]
    a = a * (1 - 0.3 * k * (1 - sh))
    c.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA"))


def cam_question(t, f):
    fx, fy = fig_pt("young", YOUNG[2], YOUNG[0], YOUNG[1], 0.48, 0.2)
    return dict(z=ramp(t, C["fahal"], C["logo"], 1.0, 1.4), fx=fx, fy=fy, rot=ramp(t, C["fahal"], C["logo"], 0, 2))


def s_logo(t, f, c):
    t0 = C["logo"]
    if REAL("logo"):
        name = "logo_eye" if REAL("logo_eye") and t < t0 + 1.2 else "logo"
        im = E.load(name); s = 820 / max(im.width, im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        P.paste_pop(c, im, CX, 900, t, t0 if name == "logo_eye" else t0 + 1.2, f, seed=44)
        return
    o = min(1.0, round(step(t, t0 + 0.4, t0 + 0.9) * 4) / 4)
    paste(c, P.eye(300, max(0.05, o)), CX, 820, seed=45, f=f)
    if t >= t0 + 1.2:
        P.paste_pop(c, P.logo_placeholder(220), CX, 1120, t, t0 + 1.2, f, seed=46)
    N.light(c, N.pool((140, 420, 940, 1420), 140), dark=0.45, glow=0.06)


def cam_logo(t, f):
    return dict(z=ramp(t, C["logo"], DUR, 1.0, 1.08))


# ====================================================================== timeline
class S:
    def __init__(self, t0, t1, draw, cam, bg=None, grade=0.5, tin="rip", dur=0.5, dark=0.0):
        self.t0, self.t1, self.draw, self.cam, self.bg, self.grade = t0, t1, draw, cam, bg, grade
        self.tin, self.dur, self.dark = tin, dur, dark


NAVYD = (16, 22, 38)
SCENES = [
    S(0.0, C["awakhir"], s_hook, cam_hook, bg=NAVYD, grade=0.25, tin="cut"),
    S(C["awakhir"], C["waadu"], s_lab, cam_lab, grade=0.5, tin="zoom", dur=0.45),
    S(C["waadu"], C["ikhtaru"], s_scale, cam_scale, grade=0.55, tin="blinds", dur=0.55),
    S(C["ikhtaru"], C["lakin"], s_name, cam_name, bg=NAVYD, grade=0.25, tin="zoom", dur=0.4),
    S(C["lakin"], C["chem2"], s_slam, cam_slam, grade=0.6, tin="rip"),
    S(C["chem2"], C["qabl"], s_chem2, cam_chem2, grade=0.62, tin="flash", dur=0.25),
    S(C["qabl"], C["insan"], s_factory, cam_factory, grade=0.45, tin="iris", dur=0.6),
    S(C["insan"], C["yawm"], s_cream, cam_cream, bg=E.CREAM, grade=0.15, tin="rip"),
    S(C["yawm"], C["fahal"], s_room, cam_room, grade=0.45, tin="blinds", dur=0.6),
    S(C["fahal"], C["logo"], s_question, cam_question, grade=0.5, tin="cut"),
    S(C["logo"], DUR + 1, s_logo, cam_logo, bg=NAVYD, grade=0.2, tin="iris", dur=0.6),
]

Y = 360
L = E.Label
LABELS = [
    L("سمّوه البطل", ("البطل",), [0.3, C["batal"]], hide=C["awakhir"] - 0.45, y=Y, size=96),
    L("أواخر القرن التاسع عشر", (), [C["awakhir"] + .15, C["awakhir"] + .5, C["awakhir"] + .85, C["awakhir"] + 1.2], hide=C["waadu"], y=Y, size=70),
    L("ألمانيا", (), [C["almania"]], hide=C["waadu"], y=Y + 130, size=64),
    L("أخفّ من المورفين", ("أخفّ", "من", "المورفين"), [C["akhaf"], C["min"], C["morphin"]], hide=C["ikhtaru"] - 0.4, y=Y, size=86),
    L("اسمًا يليق بالأبطال", (), [C["ikhtaru"] + .6, C["ikhtaru"] + 1.0, C["ikhtaru"] + 1.5], hide=C["heroin"], y=Y, size=74),
    L("لم يكن أخفّ", ("أخفّ",), [C["lakin"] + .5, C["lakin"] + .9, C["akhaf2"]], hide=C["chem2"], y=Y, size=86),
    L("أقوى من المورفين", ("أقوى",), [C["aqwa1"], C["aqwa1b"], C["aqwa1c"]], hide=C["medal"] + 0.5, y=Y, size=80),
    L("1880", ("1880",), [C["y1880"]], hide=C["arba"] - 0.1, y=Y, size=110),
    L("أربع سجائر", ("أربع", "سجائر"), [C["arba"], C["sajaer"]], hide=C["machine"], y=Y, size=88),
    L("عشرين ألفًا", ("عشرين", "ألفًا"), [C["ishrin"], C["alfan"]], hide=C["insan"], y=Y, size=96),
    L("الإنسان لم يتغيّر", (), [C["insan"], C["lam"], C["yataghayar"]], hide=C["alladhi"], y=560, size=86),
    L("الذي تغيّر هو الجرعة", ("الجرعة",), [C["alladhi"], C["taghayar"], C["huwa"], C["jura"]], hide=C["yawm"], y=560, size=80),
    L("اليوم", (), [C["yawm"]], hide=C["daqiqa"] - 0.2, y=Y, size=96),
    L("في دقيقة", (), [C["daqiqa"] - 0.3, C["daqiqa"]], hide=C["fahal"], y=Y, size=86),
    L("ما لم يحصل عليه جدّك في عام", ("عام",), [C["daqiqa"] + .6, C["daqiqa"] + 1.0, C["daqiqa"] + 1.4, C["daqiqa"] + 1.9, C["daqiqa"] + 2.3, C["am"] - .3, C["am"]], hide=C["fahal"], y=Y + 130, size=60),
    L("فهل صرنا أضعف؟", ("أضعف؟",), [C["fahal"], C["sirna"], C["adaf"]], hide=C["logo"] - 0.6, y=760, size=96),
    L("أم أنّ الجرعة صارت أقوى؟", ("الجرعة", "أقوى؟"), [C["am2"], C["anna"], C["jura2"], C["sarat"], C["aqwa2"]], hide=C["logo"] - 0.6, y=960, size=80),
]

NF = int(round(DUR * E.FPS))


def shot(i, t, f, extra_z=1.0):
    """One scene at time t through its camera, noir-graded: float HxWx3."""
    s = SCENES[i]
    c = E.paper_bg(f, s.bg, s.dark) if s.bg is not None else Image.new("RGBA", (W, H), (0, 0, 0, 255))
    s.draw(t, f, c)
    cam = dict(s.cam(t, f)); cam["z"] = cam.get("z", 1.0) * extra_z
    img = N.camera(c, **cam)
    return N.grade(np.asarray(img.convert("RGB")).astype(np.float32), s.grade)


def frame(f, out_dir=None):
    t = f / E.FPS
    i = max(k for k, s in enumerate(SCENES) if s.t0 <= t)
    s = SCENES[i]
    nxt = SCENES[i + 1] if i + 1 < len(SCENES) else None
    pre = nxt is not None and nxt.tin in ("zoom", "iris") and t >= nxt.t0 - nxt.dur
    if pre:                                               # the outgoing half of a zoom-through / iris
        u = (t - (nxt.t0 - nxt.dur)) / nxt.dur
        if nxt.tin == "zoom":
            arr = shot(i, t, f, 1 + 2.6 * u * u); arr = arr * (1 - 0.6 * u) + 255 * 0.6 * u ** 3
        else:
            arr = N.iris(shot(i, t, f), 1 - u)
    elif i > 0 and t - s.t0 < s.dur and s.tin != "cut":
        u = (t - s.t0) / s.dur
        if s.tin == "zoom":
            arr = shot(i, t, f, 1 + 0.6 * (1 - u) ** 2); arr = arr * (0.4 + 0.6 * u) + 255 * 0.6 * (1 - u) ** 2
        elif s.tin == "iris":
            arr = N.iris(shot(i, t, f), u)
        elif s.tin == "flash":
            arr = shot(i, t, f); arr = arr * u + 250 * (1 - u)
        elif s.tin == "blinds":
            arr = N.blinds_wipe(shot(i - 1, t, f), shot(i, t, f), u)
        else:
            arr = N.rip(shot(i - 1, t, f), shot(i, t, f), u, f)
    else:
        arr = shot(i, t, f)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    E.draw_labels(img, LABELS, t, f)
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    r = np.random.default_rng(1000 + f)
    a = a * (1 + r.normal(0, 0.025)) + r.normal(0, 8, (H, W, 1))            # projector flicker + grain
    if r.uniform() < 0.25:                                                   # a dust scratch now and then
        x = int(r.uniform(40, W - 40)); a[:, x:x + 2] = a[:, x:x + 2] * 0.5 + 120
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(out_dir or os.path.join(HERE, "frames"), f"{f:05d}.png"))


def sheet(times, out="sheet.png", cols=4):
    fr = [int(round(t * E.FPS)) for t in times]
    for k in fr: frame(k)
    ims = [Image.open(os.path.join(HERE, "frames", f"{k:05d}.png")).resize((270, 480)) for k in fr]
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (270 * cols, 480 * rows), (0, 0, 0))
    for i, im in enumerate(ims):
        sh.paste(im, ((i % cols) * 270, (i // cols) * 480))
        ImageDraw.Draw(sh).text(((i % cols) * 270 + 6, (i // cols) * 480 + 4), f"{times[i]:.1f}s", fill=(255, 255, 0))
    sh.save(os.path.join(HERE, out))


if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        sheet([float(x) for x in sys.argv[2:]])
    elif sys.argv[1] == "encode":
        E.encode(os.path.join(HERE, "mix.wav"), os.path.join(HERE, sys.argv[2]), DUR)
    else:
        a, b = int(sys.argv[1]), min(NF, int(sys.argv[2]))
        for k in range(a, b): frame(k)
