"""بصيرة · فيديو سيزيف · الجزء ١٥: «أقرب بشبر» (7:00–7:30). The last part. Seen from above, between the dark village and the
good one: footprints that stop halfway, a shadow that falls, two lights (no angels drawn), the measuring rope, one span closer."""
import sys, os, json, math, functools; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "frames15"); os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ timing (video seconds, estimates until the voice arrives)
T = dict(fakharaj=0.4, muntasaf=3.6, tariq=4.0, atahu=4.6, mawt=5.1, lam=6.0, yasil=6.4,
         ikhtasamat=7.4, malaika=8.0, rahma=8.6, adhab=9.8, faqila=12.4, qisu=13.0, ardayn=14.2,
         fawajaduh=15.4, salih=16.4, aqrab=17.0, shibr=17.5, faghufir=19.8, lahu=20.3,
         lam2=21.0, yutlab=21.4, yasil2=22.2, bal=23.4, an=23.7, yattajih=24.0, yatruk=25.4, ard3=26.0,
         tasna=27.0, suqut=27.8)
_tj = os.path.join(HERE, "proj", "times_15.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["suqut"] + 3.6                                  # the film's last seconds: hold on the warm light, then fade


def zoom_on(img, z, cx, cy):
    if z <= 1.0001: return img
    cw, ch = E.W / z, E.H / z
    x = float(np.clip(cx - cw / 2, 0, E.W - cw)); y = float(np.clip(cy - ch / 2, 0, E.H - ch))
    return img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((E.W, E.H), Image.BICUBIC)


# ------------------------------------------------------------------ layout, seen from above
BAD = (270, 520, 300); GOOD = (1690, 520, 230)          # villages (x, y, h)
TRAIL_K = 0.78                                          # scale of the footprint patch
TRAIL_X0, TRAIL_Y = 470, 540                            # left edge and centre line of the trail
PRINTS = [119, 214, 299, 369, 434, 494, 549, 599, 644, 684]   # print positions along the rotated patch (px)
END_X = TRAIL_X0 + 722 * TRAIL_K                        # where the trail stops (≈ halfway, a span nearer the good land)
ROPE_Y = 790; ROPE_H = 46
BAD_EDGE, GOOD_EDGE = 500, 1500                          # where each rope starts
SPAN = (BAD_EDGE, BAD_EDGE + (END_X - BAD_EDGE) - (GOOD_EDGE - END_X))   # the extra length on the bad side


@functools.lru_cache(None)
def trail_img():
    im = E.load("footprints").rotate(-90, expand=True)   # walking left -> right
    im = im.resize((int(im.width * TRAIL_K), int(im.height * TRAIL_K)), Image.LANCZOS)
    return ImageEnhance.Brightness(im).enhance(0.82)


@functools.lru_cache(None)
def trail_blank():
    im = trail_img()
    rgb = im.convert("RGB").filter(ImageFilter.GaussianBlur(9))
    out = rgb.convert("RGBA"); out.putalpha(im.getchannel("A"))
    a = np.asarray(out).copy(); edge = np.asarray(im)                  # keep the cream paper rim crisp
    rim = (edge[..., :3].min(2) > 225); a[rim] = edge[rim]
    return Image.fromarray(a, "RGBA")


def footprints(c, t, f):
    if t < T["fakharaj"] - 0.1: return
    im = trail_img()
    n = sum(1 for i in range(len(PRINTS)) if t >= T["fakharaj"] + i * (T["muntasaf"] - T["fakharaj"]) / len(PRINTS))
    show = int((PRINTS[n - 1] + 45) * TRAIL_K) if n else int(30 * TRAIL_K)
    vis = trail_blank().copy()                          # smooth sand; each print is pressed in as he walks
    sharp = im.copy(); a = np.asarray(sharp.getchannel("A")).copy(); a[:, show:] = 0
    sharp.putalpha(Image.fromarray(a)); vis.alpha_composite(sharp)
    k = E.step(t, T["fakharaj"] - 0.1, T["fakharaj"] + 0.4)
    E.paste(c, vis, TRAIL_X0 + im.width / 2, TRAIL_Y + 60 * (1 - k), seed=81, f=f)


def shadow_man(c, t, f):
    """the traveler as a shadow at the end of the trail: he falls on «الموت» and fades"""
    t0 = T["muntasaf"] - 0.3
    if t < t0: return
    fall = E.step(t, T["mawt"] - 0.1, T["mawt"] + 0.5)
    fade = E.step(t, T["lam"], T["yasil"] + 0.6)
    if fade >= 1: return
    im = E.scaled("traveler_back", 300)
    a = np.asarray(im.getchannel("A")).astype(float)
    sh = np.zeros(a.shape + (4,), np.uint8); sh[..., :3] = (10, 12, 20)
    sh[..., 3] = (a * 0.78 * (1 - fade) * min(1, (t - t0) / 0.4)).astype(np.uint8)
    sh = Image.fromarray(sh, "RGBA").filter(ImageFilter.GaussianBlur(2))
    rot = -82 * fall
    big = Image.new("RGBA", (sh.width + 600, sh.height + 600), (0, 0, 0, 0)); big.paste(sh, (300, 300))
    big = big.rotate(rot, resample=Image.BICUBIC, center=(300 + sh.width / 2, 300 + sh.height))   # tips over at the feet
    E.safe(c, big, int(END_X + 40 - 300 - sh.width / 2), int(TRAIL_Y + 40 - 300 - sh.height))


def villages(c, t, f):
    x, y, h = BAD
    torn = t >= T["suqut"]
    if not torn:
        E.paste(c, ImageEnhance.Brightness(E.scaled("village_bad", h)).enhance(0.62), x, y, seed=82, f=f)
    else:
        u = t - T["suqut"]
        if u < 1.4:
            for side, half in bad_halves(h):
                E.paste(c, half, x + side * (40 * min(1, u / 0.2) + 90 * u), y + 1300 * max(0, u - 0.15) ** 2,
                        rot=-side * (8 * min(1, u / 0.2) + 45 * u), seed=83 + side, f=f)
    x, y, h = GOOD
    E.paste(c, E.scaled("village_good", h), x, y, seed=84, f=f)


@functools.lru_cache(None)
def bad_halves(h):
    im = ImageEnhance.Brightness(E.scaled("village_bad", h)).enhance(0.62)
    r = np.random.default_rng(15)
    xs = [im.width * 0.5 + r.normal(0, 16) for _ in range(12)]; ys = np.linspace(-5, im.height + 5, 12)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).polygon([(im.width + 5, -5)] + list(zip(xs, ys)) + [(im.width + 5, im.height + 5)], fill=255)
    out = []
    for side, mask in ((1, m), (-1, m.point(lambda v: 255 - v))):
        hh = Image.new("RGBA", im.size, (0, 0, 0, 0)); hh.paste(im, (0, 0), mask)
        ImageDraw.Draw(hh).line(list(zip(xs, ys)), fill=E.CREAM + (255,), width=9)
        out.append((side, hh))
    return out


# ------------------------------------------------------------------ the measuring rope
@functools.lru_cache(None)
def rope_len(L, gold=False):
    r = E.scaled("measuring_rope", ROPE_H)
    L = max(2, min(int(L), r.width))
    im = r.crop((0, 0, L, r.height))
    if gold:
        a = np.asarray(im).astype(float)
        g = a[..., :3].mean(2, keepdims=True) / 255
        a[..., :3] = np.clip(g * np.array([255, 205, 90]) * 1.25, 0, 255)
        im = Image.fromarray(a.astype(np.uint8), "RGBA")
    return im


def draw_rope(c, x_from, x_to, y, f, seed, gold=False):
    L = abs(x_to - x_from)
    if L < 4: return
    im = rope_len(round(L), gold)
    E.paste(c, im, (x_from + x_to) / 2, y, seed=seed, f=f, boil=(f // 2) % 3 == 0)


def ropes(c, t, f):
    fade = E.step(t, T["bal"] - 0.2, T["bal"] + 0.4)
    if fade >= 1 or t < T["qisu"] - 0.1: return
    k = E.step(t, T["qisu"] - 0.1, T["qisu"] + 0.8)          # from the good land to the last footprint
    if t < T["fawajaduh"]:
        draw_rope(c, GOOD_EDGE, GOOD_EDGE - (GOOD_EDGE - END_X) * k, ROPE_Y + 60, f, 91)
    if t >= T["ardayn"] - 0.2:                              # then from the dark land
        k2 = E.step(t, T["ardayn"] - 0.2, T["ardayn"] + 0.8)
        draw_rope(c, BAD_EDGE, BAD_EDGE + (END_X - BAD_EDGE) * k2, ROPE_Y, f, 92)
    if t >= T["fawajaduh"]:                                 # the good rope swings over onto the bad side: one span is left
        sw = E.step(t, T["fawajaduh"], T["salih"] + 0.2)
        L = GOOD_EDGE - END_X
        ang = math.pi * sw
        x_end = END_X + L * math.cos(ang); y_end = ROPE_Y + 60 - 60 * sw - 150 * math.sin(ang)
        im = rope_len(round(L)).copy()
        im = im.rotate(math.degrees(ang) * -1 if sw < 1 else 0, resample=Image.BICUBIC, expand=True) if sw < 1 else im
        E.paste(c, im, (END_X + x_end) / 2, (ROPE_Y + 60 - 60 * sw + y_end) / 2 if sw < 1 else ROPE_Y - 52, seed=93, f=f)
    if t >= T["aqrab"] - 0.05:                              # «أقربَ بشبر»: the span left over glows gold
        draw_rope(c, SPAN[0], SPAN[1], ROPE_Y, f, 94, gold=True)
        g = E.step(t, T["aqrab"], T["aqrab"] + 0.4)
        cx = (SPAN[0] + SPAN[1]) / 2
        c.alpha_composite(E.glow_spot((cx - 120, ROPE_Y - 80, cx + 120, ROPE_Y + 80), color=(255, 210, 110), alpha=int(150 * g), blur=40))


# ------------------------------------------------------------------ two lights, no figures
def lights(c, t):
    w = E.step(t, T["rahma"] - 0.2, T["rahma"] + 0.6)
    b = E.step(t, T["adhab"] - 0.2, T["adhab"] + 0.6) * (1 - E.step(t, T["faghufir"], T["faghufir"] + 1.2))
    pulse = 0.85 + 0.15 * math.sin(t * 5) if t < T["faqila"] else 1.0     # they contend: the two lights breathe against each other
    if w > 0:
        c.alpha_composite(E.glow_spot((1250, -350, 2500, 1450), color=(255, 205, 130), alpha=int(110 * w * pulse), blur=180))
    if b > 0:
        c.alpha_composite(E.glow_spot((-600, -350, 650, 1450), color=(120, 160, 255), alpha=int(110 * b * (2 - pulse)), blur=180))
    flood = E.step(t, T["faghufir"], T["lahu"] + 1.0)
    if flood > 0:                                           # «فغُفر له»: the warm light fills everything
        c.alpha_composite(E.glow_spot((-300, -500, 2300, 1600), color=(255, 214, 150), alpha=int(95 * flood), blur=220))


# ------------------------------------------------------------------ the paper arrow toward the good land
def arrow(c, t, f):
    if t < T["yattajih"] - 0.1: return
    k = E.step(t, T["yattajih"] - 0.1, T["yattajih"] + 0.7)
    x0, x1 = END_X + 50, END_X + 50 + (GOOD[0] - 300 - END_X - 50) * k
    y = TRAIL_Y + 5
    if x1 - x0 < 20: return
    r = np.random.default_rng(31 + (f // 2) % 3)
    body = [(x0, y - 22), (x1 - 60, y - 22), (x1 - 60, y - 52), (x1, y), (x1 - 60, y + 52), (x1 - 60, y + 22), (x0, y + 22)]
    lay = Image.new("RGBA", (E.W, E.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon(E.torn_poly(body + [body[0]], f, 31, 2.5), fill=E.CREAM + (255,))
    d.polygon([(x0 + 10, y - 10), (x1 - 70, y - 10), (x1 - 70, y - 34), (x1 - 14, y), (x1 - 70, y + 34), (x1 - 70, y + 10), (x0 + 10, y + 10)],
              fill=E.BRICK + (255,))
    sh = Image.new("RGBA", lay.size, (5, 8, 16, 0)); sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * .5)))
    c.alpha_composite(sh, (8, 10)); c.alpha_composite(lay)


def scene_above(t, f, c):
    img = E.paper_bg(f, (54, 60, 82))
    d = ImageDraw.Draw(img); r = np.random.default_rng(4)
    for i in range(26):                                     # moonlit sand ripples seen from above
        y0 = r.uniform(0, E.H); amp = r.uniform(6, 14); ph = r.uniform(0, 6)
        d.line([(x, y0 + amp * math.sin(x / 120 + ph)) for x in range(-20, E.W + 40, 30)], fill=(78, 86, 110, 255), width=3)
    lights(img, t)
    villages(img, t, f)
    footprints(img, t, f)
    shadow_man(img, t, f)
    ropes(img, t, f)
    arrow(img, t, f)
    z = 1 + 0.9 * E.step(t, T["aqrab"], T["aqrab"] + 0.7) * (1 - E.step(t, T["faghufir"] - 0.3, T["faghufir"] + 0.6))
    cx = (SPAN[0] + SPAN[1]) / 2
    c.alpha_composite(zoom_on(img, round(z * 40) / 40, cx, ROPE_Y - 20))


SCENES = [E.Scene(0, DUR, scene_above, bg=None)]

LABELS = [
    E.Label("أقربَ بشبر", ("أقربَ", "بشبر"), [T["aqrab"], T["shibr"]], hide=T["faghufir"] - 0.2, y=150, size=110),
    E.Label("بل أن يتّجه", ("يتّجه",), [T["bal"], T["an"], T["yattajih"]], hide=T["suqut"] - 0.2, y=150, size=96),
]


def post(arr, t, f, idx):
    return arr


if __name__ == "__main__":
    if sys.argv[1] == "keys":
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keys15"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
