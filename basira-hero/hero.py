"""«سمّوه البطل» - vertical Short (1080x1920, 12 fps stop-motion), the 4th in the «أمة الدوبامين» series.

  python3 prepare.py                 # cut-outs/backgrounds from assets/ (placeholders for anything missing)
  python3 hero.py sheet 1.0 3.5 ...  # render a few frames + sheet.png to check the look
  python3 hero.py 0 390 & python3 hero.py 390 780 & wait   # render every frame
  python3 tools/sound.py             # foley (+ narration/P1.wav, P2.wav when they exist) -> mix.wav
  python3 hero.py encode basira_hero_v1.mp4
"""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import basira_engine as E
import props as P
from cues import C, DUR

E.setup(HERE, os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
E.VIG = E.VIG  # engine already builds the vignette for 1080x1920
try:
    STATUS = json.load(open(os.path.join(HERE, "cut", "status.json")))
except FileNotFoundError:
    sys.exit("run `python3 prepare.py` first")
REAL = lambda k: STATUS.get(k) == "real"
step, paste = E.step, E.paste
CX = E.W / 2


def stepped(u, n=None):
    return u


def glow(c, cx, cy, rx, ry, alpha, color=(255, 226, 160)):
    c.alpha_composite(E.glow_spot((cx - rx, cy - ry, cx + rx, cy + ry), color, int(alpha), 90))


def hanging_medal(c, px, py, size, angle, f):
    m = P.medal(size)
    E.pivot_paste(c, m, (m.width / 2, 22), (px, py), angle, f, seed=63, pad=120)


def bottle_at(c, cx, cy, h, f, seed=12, medal_size=None, swing=0.0, medal_drop=None, **kw):
    im = P.bottle(h, **kw)
    paste(c, im, cx, cy, seed=seed, f=f)
    if medal_size:
        g = P.bottle_geom(h)
        px = cx - im.width / 2 + g["neck_pt"][0]; py = cy - im.height / 2 + g["neck_pt"][1] + 10
        if medal_drop is None:
            hanging_medal(c, px, py, medal_size, swing, f)
        else:                                   # medal_drop = seconds since it broke loose
            dt = medal_drop
            y = py + 0.5 * 2600 * dt * dt; x = px + 160 * dt
            m = P.medal(medal_size).rotate(-140 * dt, resample=Image.BICUBIC, expand=True)
            paste(c, m, x, y + m.height / 2, seed=64, f=f)


def swing_angle(t, amp=10, speed=2.4):
    return amp * math.sin(round(t * E.FPS / 2) * 2 / E.FPS * speed)


# ================================================================== part 1: البطل
def s_hook(t, f, c):
    k = step(t, C["akhtar"], C["akhtar"] + 0.25)
    glow(c, CX, 1020, 430, 520, 120 * (1 - 0.7 * k))
    crack = round(k * 4) / 4
    bottle_at(c, CX, 1030, 760, f, medal_size=230, swing=swing_angle(t), text="HEROIN", letters=0,
              crack=crack, dim=round(k * 4) / 4 * 0.7)


def s_lab(t, f, c):
    c.alpha_composite(E.image_bg("lab", f, pan=0.35 + (t - C["awakhir"]) / 30, blur=1.2))
    x = -300 + (560 + 300) * step(t, C["awakhir"], C["awakhir"] + 1.0)
    bob = 0 if t > C["awakhir"] + 1.0 else (8 if f % 2 else 0)
    paste(c, E.scaled("chemist_k1", 1120), x, 1110 - bob, seed=3, f=f)


def balance(t, f, c, slam=False):
    c.alpha_composite(E.image_bg("lab", f, pan=0.55, blur=3.0, zoom=1.1))
    dark = Image.new("RGBA", c.size, (24, 34, 54, 90)); c.alpha_composite(dark)
    left = P.bottle(270, text="MORPHIN", letters=7)
    if not slam:
        k = step(t, C["akhaf"], C["akhaf"] + 0.5)
        over = 1 + 0.25 * math.sin(math.pi * min(1, (t - C["akhaf"]) / 0.5)) if t > C["akhaf"] else 1
        tilt = -15 * k * over
        right = P.bottle(270, text="HEROIN", letters=0)
    else:
        k = step(t, C["akhaf2"], C["akhaf2"] + 0.25)
        tilt = -15 + 40 * k
        right = P.bottle(270, text="HEROIN", letters=6, red=4)
    dx = (14 if (f % 2) else -14) if slam and 0 <= t - C["akhaf2"] < 0.4 else 0
    P.draw_scale(c, CX + dx, 1420, 540, tilt, left, right, f)


def s_scale(t, f, c):
    balance(t, f, c)


def s_name(t, f, c):
    glow(c, CX, 1000, 520, 640, 90)
    letters = sum(1 for i in range(6) if t >= C["heroin"] + i * 0.12)
    red = 4 if t >= C["shuja"] else 0
    h = int(1000 + 80 * round(step(t, C["ikhtaru"], C["lakin"]) * 8) / 8)
    bottle_at(c, CX, 1090, h, f, seed=14, text="HEROIN", letters=letters, red=red)
    if t >= C["shuja"] - 0.08:
        g = P.bottle_geom(h)
        top = 1090 - g["H"] / 2 + g["label"][1]
        P.paste_pop(c, P.card("الشجاع", 96, seed=5), CX - h * 0.07, top - 70, t, C["shuja"] - 0.08, f, seed=41, rot=-3)


def s_slam(t, f, c):
    balance(t, f, c, slam=True)


def s_chem2(t, f, c):
    c.alpha_composite(E.image_bg("lab", f, pan=0.62, blur=2.0))
    paste(c, E.scaled("chemist_k2", 1020), 350, 1120, seed=8, f=f)
    drop = None if t < C["medal"] else t - C["medal"]
    k = step(t, C["medal"], C["medal"] + 0.25)
    bottle_at(c, 820, 1250, 480, f, seed=16, medal_size=150, swing=swing_angle(t, 6), medal_drop=drop,
              text="HEROIN", letters=6, red=4, crack=round(k * 4) / 4, dim=0.4 * k)
    if t >= C["x2"] - 0.08:
        txt = "×5" if t >= C["x5"] else "×2"
        t0 = (C["x5"] if t >= C["x5"] else C["x2"]) - 0.08
        P.paste_pop(c, P.card(txt, 170, seed=6), 810, 800, t, t0, f, seed=42, rot=3)


# ================================================================== part 2: الجرعة
CIG_X = (300, 460, 620, 780)
COUNT_STEPS = ["4", "12", "85", "640", "2,900", "8,400", "14,700", "20,000"]


def machine_geom():
    m = E.scaled("machine", 780)
    return m, 700, 1080            # image, centre x, resting centre y


def s_factory(t, f, c):
    c.alpha_composite(E.image_bg("factory", f, pan=0.5 + (t - C["qabl"]) / 40, blur=1.0))
    ws = step(t, C["machine"], C["machine"] + 0.6)
    paste(c, E.scaled("worker", 960), 540 - 260 * ws, 1150, seed=5, f=f)
    # clock: one slow minute from «أربع سجائر» to the end of the flood
    if t >= C["arba"] - 0.2:
        turn = min(1, (t - C["arba"]) / (C["alfan"] + 1.4 - C["arba"]))
        P.draw_clock(c, 840, 660, 120, turn, f)
    # four cigarettes rolled by hand, one at a time
    n = sum(1 for i in range(4) if t >= C["arba"] + i * 0.4)
    for i in range(n):
        paste(c, P.cigarette(140, 0), CIG_X[i] - 140 * ws, 1395, seed=80 + i, f=f)
    # the machine drops onto the table
    if t >= C["machine"]:
        m, mx, my = machine_geom()
        k = step(t, C["machine"], C["machine"] + 0.45)
        y = -m.height + (my + m.height) * k
        hum = (E.jit(f, 99, 4, 0.8) if t > C["machine"] + 0.6 else (0, 0, 0))
        if not REAL("machine"):
            P_wheel = P.flywheel(150, (t * 300 if t > C["machine"] + 0.6 else 0) // 15 * 15)
            paste(c, P_wheel, mx - m.width * 0.36 + hum[0], y + 40 + hum[1], shadow=True)
        paste(c, m, mx + hum[0], y + hum[1], rot=hum[2], seed=7, f=f)
        if k >= 1 and t < C["ishrin"] + 0.05:
            pass
    # the flood: twenty thousand in the same minute
    if t >= C["ishrin"]:
        m, mx, my = machine_geom()
        chute = (mx + m.width * 0.46, my + m.height * 0.17)
        P.pour(c, t, C["ishrin"], C["insan"] - 0.25, chute, 1300, P.cig_sprite, seed=5, top=-160, f=f)
    # counter 4 -> 20,000
    if t >= C["sajaer"] + 0.2:
        if t < C["ishrin"]:
            txt, t0 = "4", C["sajaer"] + 0.2
        else:
            i = min(len(COUNT_STEPS) - 1, int((t - C["ishrin"]) / 0.18))
            txt, t0 = COUNT_STEPS[i], C["ishrin"] + i * 0.18
        P.paste_pop(c, P.card(txt, 150 if len(txt) < 5 else 130, seed=7), 230 if t < C["ishrin"] else CX, 540 if t < C["ishrin"] else 900, t, t0, f, seed=43, rot=-2)


STAMPS = (("أقوى", "aqwa", 860, -4), ("أسرع", "asra", 1080, 3), ("أكثر", "akthar", 1300, -2))


def s_cream(t, f, c):
    for word, key, y, rot in STAMPS:
        t0 = C[key]
        if t < t0: continue
        k = int((t - t0) * E.FPS)
        s = {0: 1.6, 1: 0.9, 2: 1.04}.get(k, 1.0)
        im = P.card(word, 150, seed=hash(word) % 50)
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        paste(c, im, CX, y, rot=rot, seed=50 + len(word), f=f)


def young_room(t, f, c, freeze=None):
    c.alpha_composite(E.image_bg("room", f, pan=0.5, blur=1.0))
    beat = 1 + 0.35 * (1 if (int((t - C["daqiqa"]) * 1.6) % 2 == 0 and t > C["daqiqa"]) else 0)
    glow(c, 640, 960, 300, 300, 85 * beat, (255, 240, 205))
    phone = (600, 930)
    tt = min(t, freeze or 1e9)
    args = (C["daqiqa"], C["fahal"] - 0.3, phone, 300, P.notif_sprite)
    P.pour(c, tt, *args, seed=8, top=1000, f=f, only="landed")      # the pile rises behind him
    paste(c, E.scaled("young", 940), CX, 1180, seed=9, f=f)
    P.pour(c, tt, *args, seed=8, top=1000, f=f, only="flying")      # ...while new ones fly past him


def s_room(t, f, c):
    young_room(t, f, c)


def s_question(t, f, c):
    young_room(t, f, c, freeze=C["fahal"])
    k = step(t, C["fahal"], C["fahal"] + 0.9)
    a = np.asarray(c.convert("RGB")).astype(float)
    a = E.drain(a, 0.8 * k) * (1 - 0.45 * k)
    c.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA"))


def s_logo(t, f, c):
    t0 = C["logo"]
    if REAL("logo"):
        name = "logo_eye" if REAL("logo_eye") and t < t0 + 1.2 else "logo"
        im = E.load(name); s = 820 / max(im.width, im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        P.paste_pop(c, im, CX, 900, t, t0 if name == "logo_eye" else t0 + 1.2, f, seed=44)
        return
    o = min(1.0, round(step(t, t0, t0 + 0.5) * 4) / 4)
    paste(c, P.eye(300, max(0.05, o)), CX, 820, seed=45, f=f)
    if t >= t0 + 1.0:
        P.paste_pop(c, P.logo_placeholder(220), CX, 1120, t, t0 + 1.0, f, seed=46)


# ================================================================== timeline
SCENES = [
    E.Scene(0.0, C["awakhir"], s_hook),
    E.Scene(C["awakhir"], C["waadu"], s_lab, bg=None),
    E.Scene(C["waadu"], C["ikhtaru"], s_scale, bg=None),
    E.Scene(C["ikhtaru"], C["lakin"], s_name, dark=0.15),
    E.Scene(C["lakin"], C["chem2"], s_slam, bg=None),
    E.Scene(C["chem2"], C["qabl"], s_chem2, bg=None),
    E.Scene(C["qabl"], C["insan"], s_factory, bg=None),
    E.Scene(C["insan"], C["yawm"], s_cream, bg=E.CREAM),
    E.Scene(C["yawm"], C["fahal"], s_room, bg=None),
    E.Scene(C["fahal"], C["logo"], s_question, bg=None, rip=False),
    E.Scene(C["logo"], DUR + 1, s_logo),
]

Y = 360
L = E.Label
LABELS = [
    L("سمّوه البطل", ("البطل",), [0.3, C["batal"]], hide=C["awakhir"], y=Y, size=96),
    L("أواخر القرن التاسع عشر", (), [C["awakhir"] + .15, C["awakhir"] + .5, C["awakhir"] + .85, C["awakhir"] + 1.2], hide=C["waadu"], y=Y, size=70),
    L("ألمانيا", (), [C["almania"]], hide=C["waadu"], y=Y + 130, size=64),
    L("أخفّ من المورفين", ("أخفّ", "من", "المورفين"), [C["akhaf"], C["min"], C["morphin"]], hide=C["ikhtaru"], y=Y, size=86),
    L("اسمًا يليق بالأبطال", (), [C["ikhtaru"] + .6, C["ikhtaru"] + 1.0, C["ikhtaru"] + 1.5], hide=C["heroin"], y=Y, size=74),
    L("لم يكن أخفّ", ("أخفّ",), [C["lakin"] + .5, C["lakin"] + .9, C["akhaf2"]], hide=C["chem2"], y=Y, size=86),
    L("أقوى من المورفين", ("أقوى",), [C["aqwa1"], C["aqwa1b"], C["aqwa1c"]], hide=C["qabl"], y=Y, size=80),
    L("1880", ("1880",), [C["y1880"]], hide=C["arba"] - 0.1, y=Y, size=110),
    L("أربع سجائر", ("أربع", "سجائر"), [C["arba"], C["sajaer"]], hide=C["machine"], y=Y, size=88),
    L("عشرين ألفًا", ("عشرين", "ألفًا"), [C["ishrin"], C["alfan"]], hide=C["insan"], y=Y, size=96),
    L("الإنسان لم يتغيّر", (), [C["insan"], C["lam"], C["yataghayar"]], hide=C["alladhi"], y=520, size=86),
    L("الذي تغيّر هو الجرعة", ("الجرعة",), [C["alladhi"], C["taghayar"], C["huwa"], C["jura"]], hide=C["yawm"], y=520, size=80),
    L("اليوم", (), [C["yawm"]], hide=C["daqiqa"] - 0.2, y=Y, size=96),
    L("في دقيقة", (), [C["daqiqa"] - 0.3, C["daqiqa"]], hide=C["fahal"], y=Y, size=86),
    L("ما لم يحصل عليه جدّك في عام", ("عام",), [C["daqiqa"] + .6, C["daqiqa"] + 1.0, C["daqiqa"] + 1.4, C["daqiqa"] + 1.9, C["daqiqa"] + 2.3, C["am"] - .3, C["am"]], hide=C["fahal"], y=Y + 130, size=60),
    L("فهل صرنا أضعف؟", ("أضعف؟",), [C["fahal"], C["sirna"], C["adaf"]], hide=C["logo"], y=760, size=96),
    L("أم أنّ الجرعة صارت أقوى؟", ("الجرعة", "أقوى؟"), [C["am2"], C["anna"], C["jura2"], C["sarat"], C["aqwa2"]], hide=C["logo"], y=960, size=80),
]

NF = int(round(DUR * E.FPS))


def sheet(times, out="sheet.png", cols=4):
    fr = [int(round(t * E.FPS)) for t in times]
    E.render(SCENES, LABELS, DUR, frames=fr)
    ims = [Image.open(os.path.join(HERE, "frames", f"{k:05d}.png")).resize((270, 480)) for k in fr]
    rows = (len(ims) + cols - 1) // cols
    s = Image.new("RGB", (270 * cols, 480 * rows), (0, 0, 0))
    for i, im in enumerate(ims):
        s.paste(im, ((i % cols) * 270, (i // cols) * 480))
        ImageDraw.Draw(s).text(((i % cols) * 270 + 6, (i // cols) * 480 + 4), f"{times[i]:.1f}s", fill=(255, 255, 0))
    s.save(os.path.join(HERE, out))


if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        sheet([float(x) for x in sys.argv[2:]])
    elif sys.argv[1] == "encode":
        E.encode(os.path.join(HERE, "mix.wav"), os.path.join(HERE, sys.argv[2]), DUR)
    else:
        a, b = int(sys.argv[1]), min(NF, int(sys.argv[2]))
        E.render(SCENES, LABELS, DUR, frames=range(a, b))
