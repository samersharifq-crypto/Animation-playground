"""Part 1 draft: "the night the saloons were closed" (0:00-0:28), vertical 1080x1920.
Placeholders: shapes drawn by make_assets.py; timings estimated until the voice is recorded.
Usage: python3 part_1.py <first_frame> <last_frame>"""
import sys, os, math, functools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import basira_engine as E

E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi.ttf"))
W, H = E.W, E.H

# ---- beats (seconds) - estimated narration, to be replaced by tl.v() after recording
T_SLAM, T_CHAIN, T_OFF = 1.9, 2.5, 3.4          # «أُغلقت»
T_CAL, T_CAL_OUT, T_STAMP = 5.4, 7.2, 8.6       # «سنة 1920» / «جريمة»
S3, S4, S5 = 10.0, 15.5, 19.5                   # scene starts
T_MAN, T_GANG = 10.0, 12.2                      # «غضب الناس» / «العصابات»
T_TIP, T_POUR = 15.9, 16.5                      # «لكن حدث شيء»
T_LINE, T_DROP, T_HALF = 19.9, 23.4, 25.0       # «أمراض الكبد» / «إلى النصف»
DUR = 28.0


def font(size):
    f = ImageFont.truetype(E.FONT, size); f.set_variation_by_name("Bold"); return f


@functools.lru_cache(None)
def world_bg(name):
    return Image.open(os.path.join(E.ROOT, "bg", name + ".png")).convert("RGBA")


def view(world, f, zoom, cx, cy, shake=0):
    """Crop the world around (cx, cy) with a stepped zoom and a slight boil; returns a frame."""
    zoom = round(zoom * 60) / 60
    cw, ch = W / zoom, H / zoom
    dx, dy, _ = E.jit(f // 2, 31, 1.2, 0)
    if shake:
        r = np.random.default_rng(f); dx += r.normal(0, shake); dy += r.normal(0, shake)
    x = float(np.clip(cx - cw / 2 + dx, 0, world.width - cw)); y = float(np.clip(cy - ch / 2 + dy, 0, world.height - ch))
    crop = world.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((W, H), Image.BILINEAR).convert("RGB")
    arr = np.asarray(crop).astype(float) * (0.55 + 0.45 * E.VIG)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def door(w, t, f, lit):
    """Saloon door in the doorway (500..740, 1170..1580): swung open until the slam, then shut."""
    d = ImageDraw.Draw(w)
    k = int((t - T_SLAM) * E.FPS) if t >= T_SLAM else -1
    width = 34 if k < 0 else {0: 120}.get(k, 240)
    wood, line = (104, 62, 36), (52, 30, 20)
    d.rectangle((500, 1170, 500 + width, 1580), fill=wood, outline=line, width=6)
    if width >= 240:
        d.line([(620, 1170), (620, 1580)], fill=line, width=6)
        for x0 in (520, 640):
            d.rectangle((x0, 1210, x0 + 80, 1330), outline=line, width=5)
            d.rectangle((x0, 1420, x0 + 80, 1540), outline=line, width=5)
    if lit:
        w.alpha_composite(glow((620, 1375), (360, 520)))


@functools.lru_cache(None)
def glow(c, size):
    lay = Image.new("RGBA", (1240, 2200), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((c[0] - size[0], c[1] - size[1], c[0] + size[0], c[1] + size[1]), fill=(255, 210, 130, 60))
    return lay.filter(ImageFilter.GaussianBlur(90))


def chain(w, t, f):
    if t < T_CHAIN: return
    k = E.step(t, T_CHAIN, T_CHAIN + 0.35)
    h = int(360 * (1.35 - 0.35 * k))
    E.paste(w, E.scaled("chain", h), 620, 1370, rot=-4 * (1 - k), seed=9, f=f)


@functools.lru_cache(None)
def stamp_img(text, size=120, color=E.BRICK):
    fnt = font(size)
    tw = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=fnt, direction="rtl", language="ar")
    im = Image.new("RGBA", (int(tw + 110), int(size * 1.9)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width, im.height), fill=E.CREAM + (255,))
    d.rounded_rectangle((18, 18, im.width - 18, im.height - 18), 18, outline=color + (235,), width=12)
    d.text((55, size * 0.22), text, font=fnt, fill=color + (235,), direction="rtl", language="ar")
    a = np.asarray(im).copy()                                         # worn ink
    ink = (a[..., 0] < 215)
    holes = (np.random.default_rng(4).random(a.shape[:2]) < 0.12) & ink
    a[holes, :3] = E.CREAM
    return Image.fromarray(a, "RGBA")


def stamp(c, text, t, t0, x, y, rot, f, size=120):
    if t < t0: return
    k = int((t - t0) * E.FPS)
    s = {0: 1.45, 1: 0.94}.get(k, 1.0)
    im = stamp_img(text, size)
    if s != 1.0: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    E.paste(c, im, x, y, rot=rot, shadow=True, seed=17, f=f)


def shadow_man(w, x, y, h, lean, alpha=200):
    """Long gangster shadow (fedora silhouette) thrown on the wall."""
    lay = Image.new("RGBA", (420, 1200), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    col = (8, 10, 20, alpha)
    d.ellipse((120, 60, 300, 100), fill=col); d.rounded_rectangle((155, 10, 265, 80), 20, fill=col)
    d.ellipse((160, 70, 260, 190), fill=col)
    d.polygon([(130, 200), (300, 200), (330, 760), (100, 760)], fill=col)
    d.polygon([(130, 740), (210, 740), (200, 1180), (140, 1180)], fill=col)
    d.polygon([(220, 740), (310, 740), (300, 1180), (240, 1180)], fill=col)
    lay = lay.rotate(lean, resample=Image.BICUBIC, expand=True).filter(ImageFilter.GaussianBlur(5))
    lay = lay.resize((int(lay.width * h / 1200), int(lay.height * h / 1200)), Image.LANCZOS)
    E.safe(w, lay, int(x - lay.width / 2), int(y - lay.height / 2))


# ------------------------------------------------------------------ scenes
def s_street(t, f, c):
    lit = t < T_OFF
    w = world_bg("street_lit" if lit else "street_dark").copy()
    door(w, t, f, lit)
    chain(w, t, f)
    stamp(w, "جريمة", t, T_STAMP, 620, 1250, 8, f, size=84)
    zoom = 1.0 + 0.14 * round(min(t, S3) / S3 * 12) / 12          # stepped push-in on the door
    shake = 14 if 0 <= t - T_SLAM < 0.25 else (6 if 0 <= t - T_STAMP < 0.17 else 0)
    c.alpha_composite(view(w, f, zoom, 620, 1180, shake))
    if T_CAL <= t:                                                  # calendar page falls over the scene
        k = E.step(t, T_CAL, T_CAL + 0.6)
        out = E.step(t, T_CAL_OUT, T_CAL_OUT + 0.5)
        y = -400 + (700 + 400) * k
        x = 540 - 1100 * out
        E.paste(c, E.scaled("calendar", 470), x, y, rot=-7 + 4 * k - 20 * out, seed=21, f=f)


def s_man(t, f, c):
    w = world_bg("street_dark").copy()
    door(w, 99, f, False); chain(w, 99, f); stamp(w, "جريمة", 99, 0, 620, 1250, 8, f, size=84)
    for i, (dl, hh, lean) in enumerate(((0.0, 820, -8), (0.45, 760, -6), (0.95, 880, -9))):
        k = E.step(t, T_GANG + dl, T_GANG + dl + 2.4)                # shadows slide right -> left on the wall
        if 0 < k < 1:
            shadow_man(w, 1400 - 1700 * round(k * 24) / 24, 1150, hh, lean)
    E.walk_in(w, "man_angry", 640, t, T_MAN, T_MAN + 0.9, -250, 360, 1262, f)
    c.alpha_composite(view(w, f, 1.3, 560, 1250))


def s_cop(t, f, c):
    w = world_bg("street_dark").copy()
    door(w, 99, f, False); chain(w, 99, f); stamp(w, "جريمة", 99, 0, 620, 1250, 8, f, size=84)
    d = ImageDraw.Draw(w)
    th = -20 - 85 * E.step(t, T_TIP, T_TIP + 0.6)                   # barrel tips over
    bc = (800, 1300)
    a = math.radians(th)
    mouth = (bc[0] + (-130) * math.sin(a), bc[1] + (-130) * math.cos(a))
    if t >= T_POUR:                                                   # amber stream + spreading puddle
        sp = E.step(t, T_POUR, T_POUR + 2.5)
        pw, ph = 80 + 260 * sp, 18 + 40 * sp
        d.ellipse((mouth[0] + 40 - pw, 1640 - ph, mouth[0] + 40 + pw, 1640 + ph), fill=(176, 116, 44, 255), outline=(120, 74, 26, 255), width=5)
        r = np.random.default_rng(f)
        pts_l, pts_r = [], []
        for i in range(12):
            u = i / 11
            x = mouth[0] + 10 + 30 * u * u + r.normal(0, 3); y = mouth[1] + (1640 - mouth[1]) * u
            wd = 22 - 8 * u
            pts_l.append((x - wd, y)); pts_r.append((x + wd, y))
        d.polygon(pts_l + pts_r[::-1], fill=(206, 146, 60, 255))
    E.paste(w, E.scaled("cop", 640), 590, 1262, rot=-10, seed=5, f=f)
    E.paste(w, E.scaled("barrel", 250), bc[0], bc[1], rot=th, seed=6, f=f)
    c.alpha_composite(view(w, f, 1.25, 720, 1250))


def s_chart(t, f, c):
    d = ImageDraw.Draw(c)
    x0, x1, base, top = 150, 930, 1400, 820
    half = (base + top) / 2
    d.line(E.torn_poly([(x0, base), (x1, base)], f, 3, 3), fill=E.INK + (255,), width=10)
    d.line(E.torn_poly([(x0, base), (x0, 700)], f, 4, 3), fill=E.INK + (255,), width=10)
    d.text((x0 + 10, base + 30), "1920", font=font(54), fill=E.INK + (255,))
    if t >= T_DROP:                                                   # dashed guide at half
        for x in range(x0 + 20, x1, 60):
            d.line([(x, half), (x + 30, half)], fill=(150, 140, 120, 255), width=6)
    pts = []
    xa = x0 + (560 - x0) * E.step(t, T_LINE, T_LINE + 2.0)
    pts = [(x0, top), (xa, top)]
    if t >= T_DROP:
        k = E.step(t, T_DROP, T_DROP + 1.2)
        pts.append((560 + 140 * k, top + (half - top) * k))
        k2 = E.step(t, T_DROP + 1.2, T_DROP + 2.2)
        if k2 > 0: pts.append((700 + (x1 - 700) * k2, half))
    if t >= T_LINE and pts[-1][0] > pts[0][0] + 5:
        poly = E.torn_poly(pts, f, 7, 4)
        d.line(poly, fill=E.CREAM + (255,), width=46)
        d.line(poly, fill=E.BRICK + (255,), width=26, joint="curve")
    if t >= T_HALF:
        k = int((t - T_HALF) * E.FPS); s = {0: 1.5, 1: 0.92}.get(k, 1.0)
        im = half_badge()
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        E.paste(c, im, 800, 900, rot=-10, shadow=False, seed=18, f=f)


@functools.lru_cache(None)
def half_badge():
    im = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 290, 290), outline=E.BRICK + (240,), width=14)
    fnt = font(150); tw = d.textlength("½", font=fnt)
    d.text(((300 - tw) / 2, 40), "½", font=fnt, fill=E.BRICK + (240,))
    return im


SCENES = [
    E.Scene(0, S3, s_street, bg=None),
    E.Scene(S3, S4, s_man, bg=None),
    E.Scene(S4, S5, s_cop, bg=None),
    E.Scene(S5, DUR, s_chart, bg=E.CREAM),
]
LABELS = [
    E.Label("في ليلة واحدة أُغلقت", ("أُغلقت",), [0.5, 0.9, 1.3, 1.9], hide=4.9),
    E.Label("سنة 1920", ("1920",), [5.4, 5.9], hide=6.9),
    E.Label("صار بيع الخمر جريمة", ("جريمة",), [7.0, 7.4, 7.8, 8.6], hide=9.9),
    E.Label("غضب الناس", (), [10.4, 10.8], hide=11.9),
    E.Label("وظهر المهربون والعصابات", ("العصابات",), [12.1, 12.6, 13.4], hide=15.4),
    E.Label("لكن حدث شيء", (), [15.9, 16.3, 16.8], hide=19.4),
    E.Label("أمراض الكبد", (), [20.0, 20.6], hide=22.9),
    E.Label("انخفضت إلى النصف", ("إلى", "النصف"), [23.4, 24.1, 24.5], hide=DUR + 1),
]


def post(arr, t, f, idx):
    if 0 <= t - T_OFF < 2 / E.FPS:                                    # light goes out: one dark frame
        arr = arr * 0.45
    return arr


if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 else None
    E.render(SCENES, LABELS, DUR, frames=range(a, b), post=post, out_dir=out)
