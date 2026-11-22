"""«سمّوه البطل» - vertical Short (1080x1920, 12 fps stop-motion), 4th in the «أمة الدوبامين» series.
Documentary torn-paper collage: every background is a torn photo taped onto the paper board, cut-out
characters and props on top, slow documentary camera moves (push-in / pull-back / pan), torn-paper rips
right-to-left and a page turn into 1880. Ends on the channel logo (the logo images, not typed text).

  python3 prepare.py                 # cut-outs/backgrounds/logo from assets/
  python3 hero.py sheet 1.0 3.5 ...  # render a few frames + sheet.png to check the look
  python3 hero.py 0 390 & python3 hero.py 390 780 & wait   # render every frame
  python3 tools/sound.py             # foley (+ narration/P1, P2 when they exist) -> mix.wav
  python3 hero.py encode basira_hero_v3.mp4
"""
import os, sys, math, json, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import basira_engine as E
import props as P
import noir as N            # camera, props and paper transitions (the noir lighting is no longer used)
from cues import C, DUR

E.setup(HERE, os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
try:
    STATUS = json.load(open(os.path.join(HERE, "cut", "status.json")))
except FileNotFoundError:
    sys.exit("run `python3 prepare.py` first")
REAL = lambda k: STATUS.get(k) == "real"
W, H, CX = E.W, E.H, E.W / 2
step, paste, ramp, ease = E.step, E.paste, N.ramp, N.ease
NAVYD = (20, 28, 46)
LOGO_CREAM = (241, 234, 223)


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


# ------------------------------------------------------------------ documentary collage pieces
@functools.lru_cache(None)
def torn_photo(name, w=1010, h=1560, blur=0.0, seed=3, sat=0.9):
    """A background image as a torn print: cream fibre rim, slightly faded, ready to tape on the board."""
    im = Image.open(os.path.join(HERE, "bg", name + ".png")).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x0, y0 = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((x0, y0, x0 + w, y0 + h))
    from PIL import ImageEnhance
    im = ImageEnhance.Color(im).enhance(sat)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im).astype(float)
    a = a * 0.9 + np.array((236, 224, 200)) * 0.1                      # aged print
    pad = 30
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    rim = Image.new("L", out.size, 0); face = Image.new("L", out.size, 0)
    box = [(pad, pad), (pad + w, pad), (pad + w, pad + h), (pad, pad + h), (pad, pad)]
    ImageDraw.Draw(rim).polygon(E.torn_poly(box, 0, seed, 9), fill=255)
    inner = [(pad + 10, pad + 10), (pad + w - 10, pad + 10), (pad + w - 10, pad + h - 10), (pad + 10, pad + h - 10), (pad + 10, pad + 10)]
    ImageDraw.Draw(face).polygon(E.torn_poly(inner, 0, seed + 1, 7), fill=255)
    cream = Image.new("RGBA", out.size, E.CREAM + (255,)); cream.putalpha(rim)
    out.alpha_composite(cream)
    photo = Image.new("RGBA", out.size, (0, 0, 0, 0))
    photo.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (pad, pad))
    photo.putalpha(face)
    out.alpha_composite(photo)
    return out


@functools.lru_cache(None)
def tape(w=190, h=56, seed=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pts = E.torn_poly([(0, 6), (w, 0), (w, h - 4), (0, h), (0, 6)], 0, seed, 3)
    ImageDraw.Draw(im).polygon(pts, fill=(238, 226, 196, 175))
    return im


def pin_photo(c, name, f, cy=1000, rot=-0.8, seed=3, **kw):
    """Tape a torn photo onto the board; it boils very slightly like everything else."""
    ph = torn_photo(name, seed=seed, **kw)
    paste(c, ph, CX, cy, rot=rot, seed=seed + 90, f=f)
    top = cy - ph.height / 2 + 18
    paste(c, tape(seed=seed), CX - ph.width / 2 + 90, top, rot=-28, shadow=False, seed=seed + 91, f=f)
    paste(c, tape(seed=seed + 1), CX + ph.width / 2 - 90, top, rot=24, shadow=False, seed=seed + 92, f=f)


@functools.lru_cache(None)
def graph_paper():
    """Cream graph paper for the 'diagram' beats (the scale)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for x in range(0, W, 54): d.line((x, 0, x, H), fill=(120, 150, 160, 40 if x % 270 else 80), width=2)
    for y in range(0, H, 54): d.line((0, y, W, y), fill=(120, 150, 160, 40 if y % 270 else 80), width=2)
    return im


def glow(c, cx, cy, rx, ry, alpha, color=(255, 226, 160)):
    c.alpha_composite(E.glow_spot((cx - rx, cy - ry, cx + rx, cy + ry), color, int(alpha), 90))


# ====================================================================== part 1: البطل
BOT1 = (CX, 1060, 860)


def s_hook(t, f, c):
    cracked = t >= C["akhtar"]
    k = step(t, C["akhtar"], C["akhtar"] + 0.3)
    glow(c, CX, 1020, 440, 560, 120 * (1 - 0.65 * k))
    x, y, h = BOT1
    paste(c, N.bottle(h, "bottle_cracked" if cracked else "bottle", letters=0), x, y, seed=12, f=f)
    px, py = N.neck_point(h, x, y)
    N.hang_medal(c, px, py, int(h * 0.26), swing(t), f)


def cam_hook(t, f):
    dx, dy = N.shake(f, t, C["akhtar"], 0.3, 14)
    return dict(z=ramp(t, 0, C["awakhir"], 1.0, 1.1), fx=CX, fy=1050, dx=dx, dy=dy)


def s_lab(t, f, c):
    pin_photo(c, "lab", f, seed=3)
    x = ramp(t, C["awakhir"], C["awakhir"] + 1.3, -260, 480)
    bob = 0 if t > C["awakhir"] + 1.3 else (10 if f % 2 else 0)
    paste(c, fig("chemist_k1", 1180), x, 1200 - bob, seed=3, f=f)


def cam_lab(t, f):
    hx, hy = fig_pt("chemist_k1", 1180, 480, 1200, 0.8, 0.2)
    k = ease((t - C["almania"] + 0.3) / (C["waadu"] - C["almania"] + 0.3))
    return dict(z=1.0 + 0.3 * k, fx=CX + (hx - CX) * k, fy=1000 + (hy - 1000) * k)


SCALE = (CX, 760, 1.05)


def diagram(c):
    c.alpha_composite(graph_paper())


def s_scale(t, f, c):
    diagram(c)
    k = step(t, C["akhaf"], C["akhaf"] + 0.5)
    over = 1 + 0.3 * math.sin(math.pi * min(1, (t - C["akhaf"]) / 0.55)) if t > C["akhaf"] else 1
    N.draw_scale(c, SCALE[0], SCALE[1], SCALE[2], -13 * k * over,
                 N.bottle(380, "bottle_morphine", "MORPHIN", 7), N.bottle(380, "bottle", letters=0), f)


def cam_scale(t, f):
    return dict(z=ramp(t, C["waadu"], C["waadu"] + 1.4, 1.2, 1.0), fx=CX, fy=ramp(t, C["waadu"], C["waadu"] + 1.4, 1100, 1000))


BOT4 = (CX, 1140, 1240)


def s_name(t, f, c):
    glow(c, CX, 1100, 520, 680, 80)
    x, y, h = BOT4
    letters = sum(1 for i in range(6) if t >= C["heroin"] + i * 0.12)
    red = 4 if t >= C["shuja"] else 0
    paste(c, N.bottle(h, "bottle", "HEROIN", letters, red), x, y, seed=14, f=f)
    if t >= C["shuja"] - 0.08:
        lx, ly = N.label_point(h, x, y, fx=0.36, fy=0.0)
        P.paste_pop(c, P.card("شجاع", 104, seed=5), lx, ly - 70, t, C["shuja"] - 0.08, f, seed=41, rot=-4)


def cam_name(t, f):
    lx, ly = N.label_point(BOT4[2], BOT4[0], BOT4[1])
    z = ramp(t, C["ikhtaru"], C["heroin"], 1.0, 1.15)
    if t >= C["shuja"]: z += 0.08 * min(1, (t - C["shuja"]) / 0.25)
    return dict(z=z, fx=lx, fy=ramp(t, C["ikhtaru"], C["heroin"], 1080, ly - 40))


def s_slam(t, f, c):
    diagram(c)
    k = step(t, C["akhaf2"], C["akhaf2"] + 0.2)
    N.draw_scale(c, SCALE[0], SCALE[1], SCALE[2], -13 + 38 * k,
                 N.bottle(380, "bottle_morphine", "MORPHIN", 7), N.bottle(380, "bottle", "HEROIN", 6, 4), f)


def cam_slam(t, f):
    dx, dy = N.shake(f, t, C["akhaf2"], 0.45, 28)
    return dict(z=1.04, fx=CX, fy=1000, dx=dx, dy=dy)


BOT6 = (830, 1250, 560)
MEDAL_FLOOR = 1450


def medal_pos(t):
    x, y, h = BOT6
    px, py = N.neck_point(h, x, y)
    dt = t - C["medal"]
    if dt < 0: return px, py, None
    fall = 0.5 * 3200 * dt * dt
    landed = py + fall >= MEDAL_FLOOR - 60
    return px + min(dt, 0.45) * 120, min(py + fall, MEDAL_FLOOR - 60), (-160 * min(dt, 0.45)) if not landed else -72


def s_chem2(t, f, c):
    pin_photo(c, "lab", f, seed=7, rot=0.9, blur=1.2)
    paste(c, fig("chemist_k2", 1120), 350, 1170, seed=8, f=f)
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


def cam_chem2(t, f):
    z = 1.0
    for key in ("x2", "x5"):
        if t >= C[key]: z += 0.06 * max(0, 1 - (t - C[key]) / 0.5)
    if t >= C["medal"] + 0.6:
        mx, my, _ = medal_pos(t)
        k = ease((t - C["medal"] - 0.6) / 2.0)
        return dict(z=1.0 + 0.35 * k, fx=CX + (mx - CX) * k, fy=1000 + (my - 1000) * k)
    return dict(z=z, fx=CX, fy=1000)


# ====================================================================== part 2: الجرعة
CIG_ROW = (230, 400, 570, 740)
COUNT_STEPS = ["4", "12", "85", "640", "2,900", "8,400", "14,700", "20,000"]
WORKER = (560, 1310, 820)
CLOCK = (840, 560, 250)


def machine_geom():
    m = E.scaled("machine", 760); return m, 760, 1200


def s_factory(t, f, c):
    pin_photo(c, "factory", f, seed=11, rot=0.7)
    ws = step(t, C["machine"], C["machine"] + 0.6)
    wx, wy, wh = WORKER
    paste(c, fig("worker", wh), wx - 250 * ws, wy, seed=5, f=f)
    if C["arba"] - 0.2 <= t < C["machine"] + 0.2:      # the slow minute, only for the hand-rolled four
        turn = min(1, (t - C["arba"]) / (C["machine"] - C["arba"]))
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


def cam_factory(t, f):
    if t < C["arba"]:                                     # start on the window, pull back to the worker
        k = ease((t - C["qabl"]) / 3.0)
        return dict(z=1.35 - 0.35 * k, fx=640 + (CX - 640) * k, fy=650 + (1000 - 650) * k)
    if t < C["machine"]:
        return dict(z=ramp(t, C["arba"], C["machine"], 1.0, 1.12), fx=CX, fy=800)
    dx, dy = N.shake(f, t, C["machine"] + 0.45, 0.4, 22)
    if t < C["ishrin"]:
        return dict(z=ramp(t, C["machine"], C["machine"] + 0.5, 1.12, 1.0), fx=CX, fy=960, dx=dx, dy=dy)
    return dict(z=ramp(t, C["ishrin"], C["insan"], 1.0, 1.12), fx=CX, fy=900)


STAMPS = (("أقوى", "aqwa", 1010, -4), ("أسرع", "asra", 1200, 3), ("أكثر", "akthar", 1390, -2))


def s_cream(t, f, c):
    for word, key, y, rot in STAMPS:
        t0 = C[key]
        if t < t0: continue
        k = int((t - t0) * E.FPS)
        s = {0: 1.7, 1: 0.9, 2: 1.04}.get(k, 1.0)
        im = P.card(word, 140, seed=len(word) * 7)
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        paste(c, im, CX, y, rot=rot, seed=50 + len(word), f=f)


def cam_cream(t, f):
    z = ramp(t, C["insan"], C["yawm"], 1.0, 1.06); dx = dy = 0
    for _, key, _, _ in STAMPS:
        if t >= C[key]:
            z += 0.05 * max(0, 1 - (t - C[key]) / 0.35)
            a, b = N.shake(f, t, C[key], 0.2, 12); dx += a; dy += b
    return dict(z=z, dx=dx, dy=dy)


YOUNG = (560, 1240, 860)


def phone_xy():
    return fig_pt("young", YOUNG[2], YOUNG[0], YOUNG[1], 0.68, 0.32)


def young_room(t, f, c, freeze=None):
    pin_photo(c, "room", f, seed=17, rot=-0.6)
    ph = phone_xy()
    beat = 1 + (0.4 if (t > C["daqiqa"] and int((t - C["daqiqa"]) * 1.6) % 2 == 0) else 0)
    glow(c, ph[0], ph[1], 300, 300, 70 * beat, (220, 236, 255))
    tt = min(t, freeze or 1e9)
    args = (C["daqiqa"], C["fahal"] - 0.3, ph, 300, N.note_sprite)
    P.pour(c, tt, *args, seed=8, top=1050, f=f, only="landed")
    paste(c, fig("young", YOUNG[2]), YOUNG[0], YOUNG[1], seed=9, f=f)
    if freeze is None: P.pour(c, tt, *args, seed=8, top=1050, f=f, only="flying")


def s_room(t, f, c):
    young_room(t, f, c)


def cam_room(t, f):
    ph = phone_xy()
    k = ease((t - C["yawm"]) / 2.6)
    return dict(z=1.5 - 0.5 * k, fx=ph[0] + (CX - ph[0]) * k, fy=ph[1] + (1050 - ph[1]) * k)


def s_question(t, f, c):
    young_room(t, f, c, freeze=C["fahal"])
    k = step(t, C["fahal"], C["fahal"] + 1.2)
    a = np.asarray(c.convert("RGB")).astype(float)
    a = E.drain(a, 0.45 * k) * (1 - 0.1 * k)
    c.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA"))


def cam_question(t, f):
    fx, fy = fig_pt("young", YOUNG[2], YOUNG[0], YOUNG[1], 0.48, 0.25)
    return dict(z=ramp(t, C["fahal"], C["logo"], 1.0, 1.3), fx=fx, fy=fy)


# ---------------------------------------------------------------- the logo (images, not typed text)
@functools.lru_cache(None)
def logo_img(name, w):
    im = E.load(name); return im.resize((int(w), int(im.height * w / im.width)), Image.LANCZOS)


def s_logo(t, f, c):
    t0 = C["logo"]
    mark = logo_img("logo_eye", 520)
    full = logo_img("logo", 960)
    if t < t0 + 1.4:                       # the ب with the eye drops in, the eye "opens"
        k = step(t, t0 + 0.15, t0 + 0.55)
        y = -300 + (900 + 300) * k
        paste(c, mark, CX, y, seed=45, f=f, shadow=False)
    else:                                  # then the full logo with the name and the line
        P.paste_pop(c, full, CX, 940, t, t0 + 1.4, f, seed=46)


def cam_logo(t, f):
    return dict(z=ramp(t, C["logo"], DUR, 1.0, 1.04))


# ====================================================================== timeline
class S:
    def __init__(self, t0, t1, draw, cam, bg=NAVYD, tin="rip", dur=0.5, dark=0.0):
        self.t0, self.t1, self.draw, self.cam, self.bg = t0, t1, draw, cam, bg
        self.tin, self.dur, self.dark = tin, dur, dark


SCENES = [
    S(0.0, C["awakhir"], s_hook, cam_hook, tin="cut"),
    S(C["awakhir"], C["waadu"], s_lab, cam_lab),
    S(C["waadu"], C["ikhtaru"], s_scale, cam_scale, bg=E.CREAM),
    S(C["ikhtaru"], C["lakin"], s_name, cam_name),
    S(C["lakin"], C["chem2"], s_slam, cam_slam, bg=E.CREAM),
    S(C["chem2"], C["qabl"], s_chem2, cam_chem2),
    S(C["qabl"], C["insan"], s_factory, cam_factory, tin="page", dur=0.7),
    S(C["insan"], C["yawm"], s_cream, cam_cream, bg=E.CREAM),
    S(C["yawm"], C["fahal"], s_room, cam_room),
    S(C["fahal"], C["logo"], s_question, cam_question, tin="cut"),
    S(C["logo"], DUR + 1, s_logo, cam_logo, bg=LOGO_CREAM),
]

Y = 360


def _load_words():
    f = os.path.join(HERE, "narration", "cues.json")
    return json.load(open(f))["words"] if os.path.exists(f) else None


WORDS = _load_words()


def wt(part, word, n=1, default=0.0):
    """Video time of the n-th spoken word starting with `word` (from the recorded voice)."""
    if not WORDS: return default
    k = 0
    for t, w in WORDS[part]:
        if w.startswith(word):
            k += 1
            if k == n: return t
    return default

L = E.Label
LABELS = [
    L("سمّوه البطل", ("البطل",), [wt("P1", "سم", 1, 0.3), C["batal"]], hide=C["awakhir"], y=Y, size=96),
    L("أواخر القرن التاسع عشر", (), [wt("P1", "أواخر", 1, C["awakhir"] + .15), wt("P1", "القرن", 1, C["awakhir"] + .5), wt("P1", "التاسع", 1, C["awakhir"] + .85), wt("P1", "عشر", 1, C["awakhir"] + 1.2)], hide=C["waadu"], y=Y, size=70),
    L("أخفّ من المورفين", ("أخفّ", "من", "المورفين"), [C["akhaf"], C["min"], C["morphin"]], hide=C["ikhtaru"], y=Y, size=86),
    L("اسمًا يليق بالأبطال", (), [C["ismen"], wt("P1", "يليق", 1, C["ismen"] + .5), wt("P1", "بالأبطال", 1, C["ismen"] + 1.0)], hide=C["heroin"], y=Y, size=74),
    L("لم يكن أخفّ", ("أخفّ",), [wt("P1", "لم", 1, C["lakin"] + .5), wt("P1", "يكن", 1, C["lakin"] + .9), C["akhaf2"]], hide=C["chem2"], y=Y, size=86),
    L("أقوى من المورفين", ("أقوى",), [C["aqwa1"], C["aqwa1b"], C["aqwa1c"]], hide=C["medal"] + 0.5, y=Y, size=80),
    L("1880", ("1880",), [C["y1880"]], hide=C["ishrin"] - 0.1, y=Y, size=110),
    L("أربع سجائر", ("أربع", "سجائر"), [C["arba"], C["sajaer"]], hide=C["machine"], y=Y, size=88),
    L("عشرين ألفًا", ("عشرين", "ألفًا"), [C["ishrin"], C["alfan"]], hide=C["insan"], y=Y, size=96),
    L("الإنسان لم يتغيّر", (), [C["insan"], C["lam"], C["yataghayar"]], hide=C["alladhi"], y=560, size=86),
    L("الذي تغيّر هو الجرعة", ("الجرعة",), [C["alladhi"], C["taghayar"], C["huwa"], C["jura"]], hide=C["yawm"], y=560, size=80),
    L("«فلقد خلق العرض طلبًا دائمًا»", (), [C["jura"] + .3] * 5, hide=C["yawm"], y=700, size=54),
    L("آنا لمبكي · أمة الدوبامين", (), [C["jura"] + .3] * 5, hide=C["yawm"], y=805, size=34),
    L("اليوم", (), [C["yawm"]], hide=C["daqiqa"] - 0.2, y=Y, size=96),
    L("في دقيقة", (), [C["daqiqa"] - 0.25, C["daqiqa"]], hide=C["fahal"], y=Y, size=86),
    L("ما لم يحصل عليه جدّك في عام", ("عام",), [wt("P2", "ما", 1, C["daqiqa"] + .6), wt("P2", "لم", 2, C["daqiqa"] + 1.0), wt("P2", "يحصل", 1, C["daqiqa"] + 1.4), wt("P2", "عليه", 1, C["daqiqa"] + 1.9), wt("P2", "جدك", 1, C["daqiqa"] + 2.3), C["am"] - .25, C["am"]], hide=C["fahal"], y=Y + 130, size=60),
    L("فهل صرنا أضعف؟", ("أضعف؟",), [C["fahal"], C["sirna"], C["adaf"]], hide=C["logo"], y=Y, size=96),
    L("أم أنّ الجرعة صارت أقوى؟", ("الجرعة", "أقوى؟"), [C["am2"], C["anna"], C["jura2"], C["sarat"], C["aqwa2"]], hide=C["logo"], y=Y + 150, size=80),
]

NF = int(round(DUR * E.FPS))


def doc_grade(arr):
    """Archive print: a touch desaturated and warm, soft vignette."""
    lum = arr.mean(axis=2, keepdims=True)
    a = arr * 0.85 + lum * 0.15
    a = a * np.array((1.02, 1.0, 0.95), np.float32)
    return a * N._vig(0.32)


def shot(i, t, f):
    s = SCENES[i]
    c = E.paper_bg(f, s.bg, s.dark)
    s.draw(t, f, c)
    img = N.camera(c, **s.cam(t, f))
    return doc_grade(np.asarray(img.convert("RGB")).astype(np.float32))


def page_turn(prev, cur, u):
    """Book page turning (Arabic books turn left -> right): the new page slides in under a curling edge."""
    x = int(ease(u) * (W + 120)) - 60
    out = prev.copy()
    if x > 0: out[:, :x] = cur[:, :x]
    sh = np.clip(1 - np.abs(np.arange(W) - x) / 90, 0, 1)[None, :, None]
    out = out * (1 - 0.45 * sh * (np.arange(W)[None, :, None] < x))
    fold = (np.abs(np.arange(W) - x) < 14)[None, :, None]
    return np.where(fold, np.array(E.CREAM, np.float32) * 0.92, out)


def frame(f, out_dir=None):
    t = f / E.FPS
    i = max(k for k, s in enumerate(SCENES) if s.t0 <= t)
    s = SCENES[i]
    if i > 0 and t - s.t0 < s.dur and s.tin != "cut":
        u = (t - s.t0) / s.dur
        if s.tin == "page":
            arr = page_turn(shot(i - 1, t, f), shot(i, t, f), u)
        else:
            arr = N.rip(shot(i - 1, t, f), shot(i, t, f), u, f)
    else:
        arr = shot(i, t, f)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    E.draw_labels(img, LABELS, t, f)
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    a = a + np.random.default_rng(1000 + f).normal(0, 6, (H, W, 1))          # paper/film grain
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
        import subprocess
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "12", "-i", os.path.join(HERE, "frames", "%05d.png"),
                        "-i", os.path.join(HERE, "mix.wav"), "-r", "24", "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
                        "-preset", "slow", "-crf", "31", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                        "-ar", "44100", "-t", f"{DUR}", "-movflags", "+faststart", os.path.join(HERE, sys.argv[2])], check=True)
    else:
        a, b = int(sys.argv[1]), min(NF, int(sys.argv[2]))
        for k in range(a, b): frame(k)
