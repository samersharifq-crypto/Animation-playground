"""«حين مُنع، قلّ» - full Short (both parts), 1080x1920, classic-film transitions, push-ins only.
Timings are estimates until the voice is recorded (see BEATS / LABELS).
Usage: python3 film.py <first_frame> <last_frame>"""
import sys, os, math, functools
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import basira_engine as E

E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi.ttf"))
W, H, FPS = E.W, E.H, E.FPS
OUT = os.path.join(E.ROOT, "film"); os.makedirs(OUT, exist_ok=True)
DUR = 59.5
T_TODAY = 44.0                     # old-film look before this, clean modern look after


def font(size):
    f = ImageFont.truetype(E.FONT, size); f.set_variation_by_name("Bold"); return f


# ------------------------------------------------------------------ world (backgrounds placed in a big canvas)
WS = 1240 / 756                    # source px -> world px

@functools.lru_cache(None)
def world(name):
    im = Image.open(os.path.join(E.ROOT, "bg", name.split("_")[0] + ".png")).convert("RGB")
    im = im.resize((1240, int(im.height * WS)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    a = np.asarray(im).astype(float)
    if name == "street_lit":       # warm light inside the saloon doorway
        sub = a[840:1300, 560:790]; lum = sub.mean(2)
        rows = np.zeros(lum.shape, bool); rows[:125] = True; rows[405:] = True
        m = ((lum < 48) & rows)[..., None]
        sub[:] = np.where(m, sub * 0.35 + np.array([222, 160, 80]) * 0.65, sub)
    if name == "street_nolamp":    # lamp flickers off
        sub = a[560:700, 190:310]; m = (sub.mean(2) > 150)[..., None]
        sub[:] = np.where(m, np.array([46, 52, 66]), sub)
        a = a * 0.86
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    if name == "street_lit":
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse((470, 820, 880, 1420), fill=(255, 196, 110, 70))
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(70)))
    return im


class View:
    def __init__(self, w, f, zoom, cx, cy, shake=0):
        zoom = round(zoom * 60) / 60
        cw, ch = W / zoom, H / zoom
        dx, dy, _ = E.jit(f // 2, 31, 1.2, 0)
        if shake:
            r = np.random.default_rng(f); dx += r.normal(0, shake); dy += r.normal(0, shake)
        self.x0 = float(np.clip(cx - cw / 2 + dx, 0, w.width - cw)); self.y0 = float(np.clip(cy - ch / 2 + dy, 0, w.height - ch))
        self.z = zoom
        self.img = w.crop((int(self.x0), int(self.y0), int(self.x0 + cw), int(self.y0 + ch))).resize((W, H), Image.BILINEAR)

    def pt(self, x, y):
        return ((x - self.x0) * self.z, (y - self.y0) * self.z)


def push(t, t0, t1, z0, z1, steps=14):
    """Stepped push-in (never out)."""
    u = min(max((t - t0) / (t1 - t0), 0), 1)
    return z0 + (z1 - z0) * round(u * steps) / steps


FOCUS = {}                          # screen point per scene (for iris transitions)


# ------------------------------------------------------------------ props drawn in code
@functools.lru_cache(None)
def stamp_img(text, size=120, color=E.BRICK):
    fnt = font(size)
    tw = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(text, font=fnt, direction="rtl", language="ar")
    im = Image.new("RGBA", (int(tw + 110), int(size * 1.9)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, im.width - 10, im.height - 10), 18, outline=color + (230,), width=12)
    d.text((55, size * 0.22), text, font=fnt, fill=color + (230,), direction="rtl", language="ar")
    a = np.asarray(im).copy()
    holes = np.random.default_rng(4).random(a.shape[:2]) < 0.14
    a[holes, 3] = (a[holes, 3] * 0.3).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def slam_scale(t, t0):
    k = int((t - t0) * FPS); return {0: 1.5, 1: 0.93}.get(k, 1.0)


def paste_stamp(c, text, t, t0, x, y, rot, f, size=120):
    if t < t0: return
    im = stamp_img(text, size); s = slam_scale(t, t0)
    if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    E.paste(c, im, x, y, rot=rot, shadow=False, seed=17, f=f)


@functools.lru_cache(None)
def glass_img(h=170):
    w = int(h * 0.75); im = Image.new("RGBA", (w + 200, h + 200), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((40, 40, w + 160, h + 160), fill=(255, 214, 140, 120))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(im); x0, y0 = 100, 100
    d.polygon([(x0 - 8, y0 - 8), (x0 + w + 8, y0 - 8), (x0 + w - 6, y0 + h + 8), (x0 + 6, y0 + h + 8)], fill=E.CREAM + (255,))
    d.polygon([(x0, y0), (x0 + w, y0), (x0 + w - 12, y0 + h), (x0 + 12, y0 + h)], fill=(214, 226, 230, 255), outline=E.INK + (255,))
    d.polygon([(x0 + 6, y0 + h * 0.45), (x0 + w - 6, y0 + h * 0.45), (x0 + w - 12, y0 + h - 4), (x0 + 12, y0 + h - 4)], fill=(196, 120, 48, 255))
    d.line([(x0 + 20, y0 + 14), (x0 + 28, y0 + h - 20)], fill=(255, 255, 255, 200), width=6)
    return im


def ruler(c, p0, p1, k, f, seed=40, label=None):
    """Paper ruler from p0 toward p1, grown to fraction k."""
    if k <= 0: return
    x1, y1 = p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k
    L = math.hypot(x1 - p0[0], y1 - p0[1]); ang = math.degrees(math.atan2(y1 - p0[1], x1 - p0[0]))
    if L < 4: return
    im = Image.new("RGBA", (int(L) + 20, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((10, 18, int(L) + 10, 72), fill=(236, 214, 160, 255), outline=E.INK + (255,), width=4)
    for i, x in enumerate(range(14, int(L) + 8, 14)):
        d.line([(x, 18), (x, 18 + (24 if i % 5 == 0 else 13))], fill=E.INK + (255,), width=3)
    if label:
        fnt = font(32); tw = d.textlength(label, font=fnt, direction="rtl", language="ar")
        if L > tw + 30: d.text(((L + 20 - tw) / 2, 36), label, font=fnt, fill=E.BRICK + (255,), direction="rtl", language="ar")
    rot = im.rotate(-ang, resample=Image.BICUBIC, expand=True)
    cx, cy = (p0[0] + x1) / 2, (p0[1] + y1) / 2
    E.paste(c, rot, cx, cy, seed=seed, f=f, boil=True)


def red_line(c, pts, f, seed=7, w=24):
    poly = E.torn_poly(pts, f, seed, 4); d = ImageDraw.Draw(c)
    d.line(poly, fill=E.CREAM + (255,), width=w + 20); d.line(poly, fill=E.BRICK + (255,), width=w)


def arrow_head(c, p, ang, f, size=52):
    d = ImageDraw.Draw(c); a = math.radians(ang)
    pts = [(p[0] + size * math.cos(a), p[1] + size * math.sin(a)),
           (p[0] + size * 0.8 * math.cos(a + 2.4), p[1] + size * 0.8 * math.sin(a + 2.4)),
           (p[0] + size * 0.8 * math.cos(a - 2.4), p[1] + size * 0.8 * math.sin(a - 2.4))]
    d.polygon(pts, fill=E.BRICK + (255,), outline=E.CREAM + (255,))


@functools.lru_cache(None)
def shadow_from(name, h):
    a = np.asarray(E.scaled(name, h))[..., 3] > 0
    im = Image.new("RGBA", (a.shape[1], a.shape[0]), (0, 0, 0, 0))
    arr = np.zeros(a.shape + (4,), np.uint8); arr[a] = (4, 6, 12, 215)
    im = Image.fromarray(arr, "RGBA").transform((a.shape[1] + 200, a.shape[0]), Image.AFFINE, (1, 0.35, -200 * 0, 0, 1, 0))
    return im.filter(ImageFilter.GaussianBlur(4))


@functools.lru_cache(None)
def newspaper():
    w, h = 900, 1240
    im = Image.new("RGB", (w, h), (233, 222, 196)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(9)
    d.rectangle((30, 30, w - 30, 46), fill=E.INK); d.rectangle((30, 54, w - 30, 58), fill=E.INK)
    f1 = font(64); txt = "عدد خاص"
    tw = d.textlength(txt, font=f1, direction="rtl", language="ar"); d.text(((w - tw) / 2, 70), txt, font=f1, fill=E.INK, direction="rtl", language="ar")
    d.rectangle((30, 170, w - 30, 176), fill=E.INK)
    f2 = font(150); txt = "أمريكا تمنع الخمر"
    for size in (150, 130, 112, 100):
        f2 = font(size); tw = d.textlength(txt, font=f2, direction="rtl", language="ar")
        if tw < w - 80: break
    d.text(((w - tw) / 2, 200), txt, font=f2, fill=E.INK, direction="rtl", language="ar")
    d.rectangle((30, 440, w - 30, 444), fill=E.INK)
    ch = E.load("chain").convert("RGBA"); ch = ch.resize((340, int(340 * ch.height / ch.width)))
    g = ImageEnhance.Color(ch).enhance(0.1)
    d.rectangle((470, 480, 870, 860), fill=(205, 196, 176), outline=E.INK, width=4)
    im.paste(g, (500, 500), g)
    for col, (x0, x1) in enumerate(((40, 440), (470, 870))):
        y = 480 if col == 0 else 890
        while y < h - 60:
            ww = (x1 - x0) * (0.55 if r.random() < 0.12 else 1.0)
            d.rectangle((x1 - ww, y, x1, y + 12), fill=(150, 140, 122)); y += 28
    a = np.asarray(im).astype(float)
    a *= (1 - 0.2 * ndimage_noise(a.shape[:2]))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def ndimage_noise(shape, s=40):
    from scipy import ndimage
    n = ndimage.gaussian_filter(np.random.default_rng(2).standard_normal(shape), s); return (n - n.min()) / (n.max() - n.min())


# ------------------------------------------------------------------ scenes
def sc_night(t, f):                                     # A 0-4.2: saloon closes
    lit = t < 2.15
    w = world("street_lit" if lit else "street").copy()
    if t >= 1.9:
        k = slam_scale(t, 1.9)
        E.paste(w, E.scaled("chain", int(360 * k)), 672, 1110, seed=9, f=f)
    v = View(w, f, push(t, 0, 4.2, 1.0, 1.22), 672, 1060, 16 if 0 <= t - 1.9 < 0.25 else 0)
    FOCUS["night"] = v.pt(672, 1150)
    return v.img


def sc_card(t, f, words=(("سنة", 5.0), ("1920", 5.6))):   # B: silent-film intertitle
    c = Image.new("RGBA", (W, H), (10, 10, 12, 255)); d = ImageDraw.Draw(c)
    gold = (226, 196, 120)
    for m, wd in ((90, 6), (112, 2)):
        d.rectangle((m, 560 + m - 90, W - m, H - 560 - m + 90), outline=E.CREAM + (255,), width=wd)
    for (x, y) in ((90, 560), (W - 90, 560), (90, H - 560), (W - 90, H - 560)):
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=gold + (255,))
    d.line([(380, 1240), (700, 1240)], fill=gold + (255,), width=4)
    d.ellipse((530, 1230, 550, 1250), fill=gold + (255,))
    shown = [w_ for w_, tt in words if t >= tt]
    if "سنة" in shown:
        fn = font(110); tw = d.textlength("سنة", font=fn, direction="rtl", language="ar")
        d.text(((W - tw) / 2, 740), "سنة", font=fn, fill=E.CREAM + (255,), direction="rtl", language="ar")
    yr = words[1][0]
    if yr in shown:
        k = slam_scale(t, words[1][1]); fn = font(int(230 * k)); tw = d.textlength(yr, font=fn)
        d.text(((W - tw) / 2, 900 - 115 * (k - 1)), yr, font=fn, fill=gold + (255,))
    FOCUS["card"] = (W / 2, 960)
    return c


def sc_paper(t, f):                                     # C 7.0-10.0: spinning newspaper
    c = Image.new("RGBA", (W, H), (8, 8, 10, 255))
    c.alpha_composite(spot((W // 2, H // 2), 900))
    u = E.step(t, 7.0, 8.2)
    u = round(u * 14) / 14
    ang = 720 * (1 - u); s = 0.06 + 0.94 * u
    s *= 1 + 0.1 * round(min(max(t - 8.2, 0), 1.8) / 1.8 * 8) / 8          # slow push after landing
    p = newspaper()
    im = p.resize((max(1, int(p.width * s)), max(1, int(p.height * s))), Image.BILINEAR)
    sh = 10 if 0 <= t - 8.6 < 0.25 else 0
    E.paste(c, im, W / 2 + (np.random.default_rng(f).normal(0, sh) if sh else 0), H / 2, rot=ang, seed=3, f=f)
    if t >= 8.6:
        st = stamp_img("جريمة", 150); k = slam_scale(t, 8.6) * s
        st = st.resize((int(st.width * k), int(st.height * k)), Image.LANCZOS)
        E.paste(c, st, W / 2, H / 2 + 230 * s, rot=-14, shadow=False, seed=18, f=f)
    FOCUS["paper"] = (W / 2, H / 2)
    return c


@functools.lru_cache(None)
def spot(c, r):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=(120, 104, 80, 110))
    return lay.filter(ImageFilter.GaussianBlur(160))


FLICK = [(12.05, 12.13), (12.3, 12.38), (13.95, 14.05), (14.6, 14.66)]

def sc_angry(t, f):                                     # D 10.0-15.5: angry man, gang shadows
    w = world("street_nolamp" if E.in_any(t, FLICK) else "street").copy()
    E.paste(w, E.scaled("chain", 360), 672, 1110, seed=9, f=f)
    for i, (dl, hh) in enumerate(((0.0, 560), (0.5, 520), (1.05, 600))):
        k = (t - 12.0 - dl) / 2.4
        if 0 < k < 1:
            sh = shadow_from("man", hh); x = 1150 - 1100 * round(k * 26) / 26
            E.safe(w, sh, int(x - sh.width / 2), int(1200 - hh))
    E.walk_in(w, "man_angry", 430, t, 10.0, 10.9, -150, 420, 1335 - 215, f)
    v = View(w, f, push(t, 10, 15.5, 1.38, 1.55), 600, 1080)
    FOCUS["angry"] = v.pt(450, 960)
    return v.img


def sc_cop(t, f):                                       # E 15.5-19.5: police pour the barrel
    w = world("street").copy()
    E.paste(w, E.scaled("chain", 360), 672, 1110, seed=9, f=f)
    rock = 1.6 * math.sin(f // 3 * 1.3)
    E.paste(w, E.scaled("cop", 470), 820, 1350 - 235, rot=rock, seed=5, f=f)
    v = View(w, f, push(t, 15.5, 19.5, 1.5, 1.68), 780, 1120)
    FOCUS["cop"] = v.pt(820, 1150)
    return v.img


def sc_chart(t, f):                                     # F 19.5-28: liver disease halves
    c = E.paper_bg(f, (236, 226, 204)); d = ImageDraw.Draw(c)
    x0, x1, base, top = 150, 930, 1420, 820; half = (base + top) / 2
    d.line(E.torn_poly([(x0, base), (x1, base)], f, 3, 3), fill=E.INK + (255,), width=10)
    d.line(E.torn_poly([(x0, base), (x0, 700)], f, 4, 3), fill=E.INK + (255,), width=10)
    d.text((x0 + 10, base + 30), "1920", font=font(54), fill=E.INK + (255,))
    if t >= 23.2:
        for x in range(x0 + 20, x1, 60): d.line([(x, half), (x + 30, half)], fill=(150, 140, 120, 255), width=6)
    xa = x0 + (560 - x0) * E.step(t, 20.0, 22.0)
    pts = [(x0, top), (xa, top)]
    if t >= 23.2:
        k = E.step(t, 23.2, 24.3); pts.append((560 + 140 * k, top + (half - top) * k))
        k2 = E.step(t, 24.3, 25.2)
        if k2 > 0: pts.append((700 + (x1 - 700) * k2, half))
    if t >= 20.0 and pts[-1][0] > x0 + 5: red_line(c, pts, f)
    if t >= 25.0:
        im = half_badge(); s = slam_scale(t, 25.0)
        if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        E.paste(c, im, 800, 900, rot=-10, shadow=False, seed=18, f=f)
    FOCUS["chart"] = (800, 1100)
    return c


@functools.lru_cache(None)
def half_badge():
    im = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 290, 290), outline=E.BRICK + (240,), width=14)
    fnt = font(150); tw = d.textlength("½", font=fnt); d.text(((300 - tw) / 2, 40), "½", font=fnt, fill=E.BRICK + (240,))
    return im


def sc_distance(t, f):                                  # G 28-33: people didn't change, the distance did
    c = E.paper_bg(f, E.NAVY)
    c.alpha_composite(glow_at(880, 620, 260))
    E.paste(c, glass_img(170), 880, 620, seed=41, f=f)
    E.paste(c, E.scaled("man", 860), 330, 1600 - 430, seed=3, f=f)
    ruler(c, (470, 900), (830, 700), E.step(t, 31.6, 32.3), f, label="المسافة")
    FOCUS["distance"] = (540, 900)
    return c


@functools.lru_cache(None)
def glow_at(x, y, r, col=(255, 214, 140), a=70):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((x - r, y - r, x + r, y + r), fill=col + (a,)); return lay.filter(ImageFilter.GaussianBlur(r / 2))


def sc_repeal(t, f):                                    # H1 33-36: chain falls, lights back on
    lit = t >= 34.0
    w = world("street_lit" if lit else "street").copy()
    if t < 33.9:
        E.paste(w, E.scaled("chain", 360), 672, 1110, seed=9, f=f)
    else:
        k = E.step(t, 33.9, 34.4)
        if k < 1: E.paste(w, E.scaled("chain", 360), 672, 1110 + 700 * k, rot=40 * k, seed=9, f=f)
    v = View(w, f, push(t, 33, 36, 1.12, 1.3), 672, 1060)
    img = v.img
    if t >= 34.6:
        k = E.step(t, 34.6, 35.1); E.paste(img, E.scaled("cal1933", 420), 540, -300 + 1060 * k, rot=-6 + 4 * k, seed=21, f=f)
    FOCUS["repeal"] = v.pt(672, 1100)
    return img


def sc_saloon(t, f):                                    # H2 36-38.6: back at the counter, numbers rise
    w = world("saloon").copy()
    E.paste(w, E.scaled("man_sit", 640), 360, 1440 - 320, seed=3, f=f)
    v = View(w, f, push(t, 36, 38.6, 1.25, 1.36), 560, 1180)
    img = v.img
    k = E.step(t, 37.5, 38.3)
    if k > 0:
        p0, p1 = (130, 1560), (960, 1240)
        pe = (p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k)
        red_line(img, [p0, ((p0[0] + pe[0]) / 2, (p0[1] + pe[1]) / 2 + 30), pe], f, w=28)
        arrow_head(img, pe, -21, f)
    FOCUS["saloon"] = (540, 1000)
    return img


def sc_rule(t, f):                                      # I 38.6-44: the closer it is, the more we use
    c = E.paper_bg(f, (236, 226, 204))
    k = E.step(t, 40.6, 42.0); k = round(k * 10) / 10
    gx = 900 - 380 * k
    E.paste(c, E.scaled("man", 620), 220, 1380 - 310, seed=3, f=f)
    c.alpha_composite(glow_at(int(gx), 1000, 160))
    E.paste(c, glass_img(150), gx, 1010, seed=41, f=f)
    ruler(c, (340, 1180), (gx - 40, 1180), 1.0, f, seed=44)
    if t >= 42.6:
        u = E.step(t, 42.6, 43.4)
        x = 880; y0 = 1480; y1 = 1480 - 380 * u
        d = ImageDraw.Draw(c)
        d.rectangle((x - 50, y1, x + 50, y0), fill=E.BRICK + (255,), outline=E.CREAM + (255,), width=8)
        arrow_head(c, (x, y1 - 10), -90, f, 70)
    FOCUS["rule"] = (540, 1000)
    return c


def sc_today(t, f):                                     # J 44-51: today, it's in your pocket
    c = E.paper_bg(f, (16, 24, 44))
    c.alpha_composite(glow_at(680, 1080, 380, (150, 200, 255), 60))
    yh = 1000; sc = E.scaled("youth", yh); cx, cy = 400, 1600 - yh / 2
    E.paste(c, sc, cx, cy, seed=3, f=f)
    left, top = cx - sc.width / 2, cy - yh / 2
    hx, hy = left + 0.90 * sc.width, top + 0.50 * yh
    pulse = 0 <= t - 50.2 < 0.6
    ph = make_phone_cached(220)
    jx = np.random.default_rng(f).normal(0, 6) if pulse else 0
    E.paste(c, ph, hx + 10 + jx, hy - 40, rot=-12, shadow=False, seed=42, f=f)
    if pulse and (f % 2 == 0): c.alpha_composite(glow_at(int(hx), int(hy - 40), 300, (255, 240, 200), 90))
    eye = (left + 0.66 * sc.width, top + 0.13 * yh)
    ruler(c, (eye[0] + 20, eye[1] + 30), (hx - 10, hy - 110), E.step(t, 48.0, 48.5), f, seed=45, label="شبر")
    FOCUS["today"] = (hx, hy)
    return c


@functools.lru_cache(None)
def make_phone_cached(h): return E.make_phone(h)


DRAWER_TOP = None

def sc_drawer(t, f):                                    # K 51-59.5: put it away, start with distance
    c = E.paper_bg(f, (16, 24, 44))
    yh = 1000; sc = E.scaled("youth_drawer", yh); cx, cy = 540, 1600 - yh / 2
    left, top = cx - sc.width / 2, cy - yh / 2
    E.paste(c, sc, cx, cy, seed=3, f=None)
    hx, hy = left + 0.47 * sc.width, top + 0.47 * yh
    k = E.step(t, 52.4, 53.2)
    if k < 1:
        E.paste(c, make_phone_cached(200), hx, hy - 30 + 110 * k, rot=-80 * k, shadow=False)
    # drawer front back on top so the phone sinks behind it
    a = np.asarray(sc); x0, x1 = int(0.33 * sc.width), int(0.54 * sc.width); y0, y1 = int(0.535 * yh), int(0.61 * yh)
    front = Image.fromarray(a[y0:y1, x0:x1].copy(), "RGBA")
    c.alpha_composite(front, (int(left + x0), int(top + y0)))
    eye = (left + 0.40 * sc.width, top + 0.13 * yh)
    ruler(c, (eye[0] - 20, eye[1] + 60), (left + 0.40 * sc.width, top + 0.52 * yh), E.step(t, 55.4, 56.0), f, seed=46, label="المسافة")
    FOCUS["drawer"] = (left + 0.43 * sc.width, top + 0.56 * yh)
    return c


# scene list: (t0, t1, draw, transition into it, transition length)
SCENES = [
    (0.0, 4.2, sc_night, None, 0),
    (4.2, 7.0, sc_card, "iris", 1.0),
    (7.0, 10.0, sc_paper, "flicker", 0.35),
    (10.0, 15.5, sc_angry, "rip", 0.5),
    (15.5, 19.5, sc_cop, "wipe", 0.5),
    (19.5, 28.0, sc_chart, "burn", 0.8),
    (28.0, 33.0, sc_distance, "rip", 0.5),
    (33.0, 36.0, sc_repeal, "clock", 0.9),
    (36.0, 38.6, sc_saloon, "barn", 0.6),
    (38.6, 44.0, sc_rule, "rip", 0.5),
    (44.0, 51.0, sc_today, "glitch", 0.4),
    (51.0, DUR, sc_drawer, "rip", 0.5),
]
IRIS_END = (57.4, 58.6)             # closing iris on the drawer, then black

L = E.Label
LABELS = [
    L("في ليلة واحدة أُغلقت", ("أُغلقت",), [0.4, 0.8, 1.2, 1.9], hide=3.8),
    L("غضب الناس", (), [10.3, 10.7], hide=11.8),
    L("وظهر المهربون والعصابات", ("العصابات",), [12.0, 12.5, 13.3], hide=15.3),
    L("لكن حدث شيء", (), [15.8, 16.2, 16.7], hide=17.6),
    L("لم يتوقعه كثيرون", (), [17.8, 18.3, 18.8], hide=19.4),
    L("أمراض الكبد", (), [20.0, 20.5], hide=22.9),
    L("انخفضت إلى النصف", ("إلى", "النصف"), [23.2, 23.9, 24.3], hide=27.8),
    L("الناس لم يتغيروا", (), [28.3, 28.8, 29.3], hide=30.2),
    L("الذي تغيّر هو المسافة", ("المسافة",), [30.4, 30.8, 31.1, 31.6], hide=32.9),
    L("رُفع الحظر", (), [33.4, 33.9], hide=34.5),
    L("سنة 1933", ("1933",), [34.6, 35.2], hide=35.9),
    L("عادت الأرقام ترتفع", ("ترتفع",), [36.4, 36.9, 37.6], hide=38.5),
    L("القاعدة بسيطة", (), [38.8, 39.4], hide=40.3),
    L("كلما قرب الشيء زاد", ("قرب", "زاد"), [40.6, 41.0, 41.5, 42.6], hide=43.9),
    L("واليوم", (), [44.2], hide=44.9),
    L("أقرب ما يدمنه الناس", (), [45.0, 45.4, 45.8, 46.2], hide=46.7),
    L("لا يبعد عنك شبرًا", ("شبرًا",), [46.8, 47.2, 47.6, 48.0], hide=48.9),
    L("إنه في جيبك", ("في", "جيبك"), [49.2, 49.7, 50.2], hide=50.9),
    L("فإن أردت أن تقلل منه", (), [51.3, 51.7, 52.1, 52.6], hide=53.8),
    L("فابدأ بالمسافة", ("بالمسافة",), [54.4, 55.4], hide=57.3),
]


# ------------------------------------------------------------------ transitions
def circle_mask(c, r):
    m = Image.new("L", (W, H), 0)
    if r > 0: ImageDraw.Draw(m).ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=255)
    return m


def iris(img, c, r):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255)); out.paste(img, (0, 0), circle_mask(c, r)); return out


def transition(kind, prev, cur, u, f, pfocus, cfocus):
    R = 2300
    if kind == "rip": return E.tear(prev, cur, u, f)
    if kind == "iris":
        return iris(prev, pfocus, R * (1 - 2 * u) ** 1.5 * 0.6) if u < 0.5 else iris(cur, cfocus, R * (2 * u - 1) ** 1.5 * 0.6)
    if kind == "flicker":
        k = int(u * 4)
        return [Image.new("RGBA", (W, H), (0, 0, 0, 255)), cur, Image.new("RGBA", (W, H), (230, 220, 200, 255)), cur][min(k, 3)]
    if kind == "wipe":                               # hard diagonal wipe, right -> left
        m = Image.new("L", (W, H), 0); xb = W + 500 - u * (W + 1000)
        ImageDraw.Draw(m).polygon([(xb + 500, 0), (W + 600, 0), (W + 600, H), (xb, H)], fill=255)
        out = prev.copy(); out.paste(cur, (0, 0), m)
        ImageDraw.Draw(out).line([(xb + 500, 0), (xb, H)], fill=(0, 0, 0, 255), width=10)
        return out
    if kind == "burn":                               # film burn spreads from a point
        cx, cy = 760, 640
        yy, xx = np.mgrid[0:H:4, 0:W:4]
        n = ndimage_noise((H // 4 + 1, W // 4 + 1), 6)[: yy.shape[0], : yy.shape[1]]
        d = np.hypot(xx - cx, yy - cy) / 2200 + 0.25 * n
        thr = u * 1.3
        m = Image.fromarray(((d < thr - 0.04) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        edge = Image.fromarray(((np.abs(d - thr) < 0.06) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(12))
        out = prev.copy(); out.paste(cur, (0, 0), m)
        hot = Image.new("RGBA", (W, H), (255, 190, 90, 255)); out.paste(hot, (0, 0), edge)
        white = Image.new("RGBA", (W, H), (255, 246, 220, 255)); out.paste(white, (0, 0), edge.point(lambda v: max(0, v * 2 - 255)))
        return out
    if kind == "clock":                              # clock wipe = time passes
        m = Image.new("L", (W, H), 0); ctr = (W / 2, H / 2)
        ImageDraw.Draw(m).pieslice((ctr[0] - 2400, ctr[1] - 2400, ctr[0] + 2400, ctr[1] + 2400), -90, -90 + 360 * u, fill=255)
        out = prev.copy(); out.paste(cur, (0, 0), m)
        a = math.radians(-90 + 360 * u); d = ImageDraw.Draw(out)
        d.line([ctr, (ctr[0] + 2400 * math.cos(a), ctr[1] + 2400 * math.sin(a))], fill=E.CREAM + (255,), width=14)
        d.ellipse((ctr[0] - 22, ctr[1] - 22, ctr[0] + 22, ctr[1] + 22), fill=E.CREAM + (255,))
        return out
    if kind == "barn":                               # saloon doors swing open from the centre
        m = Image.new("L", (W, H), 0); hw = u * W / 2
        ImageDraw.Draw(m).rectangle((W / 2 - hw, 0, W / 2 + hw, H), fill=255)
        out = prev.copy(); out.paste(cur, (0, 0), m); d = ImageDraw.Draw(out)
        for x in (W / 2 - hw, W / 2 + hw): d.line([(x, 0), (x, H)], fill=(60, 36, 20, 255), width=16)
        return out
    if kind == "glitch":
        k = int(u * FPS * 0.4)
        base = prev if k == 0 else cur
        g = E.glitch(base, f, band=60, every=120, amount=90)
        a = np.asarray(g.convert("RGB")).copy(); a[..., 0] = np.roll(a[..., 0], 14, axis=1); a[..., 2] = np.roll(a[..., 2], -14, axis=1)
        return Image.fromarray(a).convert("RGBA")
    return cur


# ------------------------------------------------------------------ old film look
def old_film(arr, f, strength=1.0):
    r = np.random.default_rng(7000 + f)
    g = arr.mean(2, keepdims=True)
    sep = g * np.array([1.07, 0.97, 0.80])[None, None]
    arr = arr * (1 - 0.22 * strength) + sep * 0.22 * strength
    arr = arr * (1 + r.normal(0, 0.035) * strength)
    for _ in range(r.integers(0, 3)):                 # vertical scratches
        x = int(r.integers(40, W - 40)); y0 = int(r.integers(0, H // 2)); ln = int(r.integers(H // 3, H))
        arr[y0:y0 + ln, x:x + 2] = arr[y0:y0 + ln, x:x + 2] * 0.5 + 230 * 0.5
    for _ in range(r.integers(4, 12)):                # dust
        x, y, s = int(r.integers(0, W)), int(r.integers(0, H)), int(r.integers(2, 7))
        arr[y:y + s, x:x + s] = 20 if r.random() < 0.6 else 235
    return arr * CORNER


def _corner():
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle((26, 26, W - 26, H - 26), 90, fill=255)
    return (np.asarray(m.filter(ImageFilter.GaussianBlur(22))).astype(float) / 255 * 0.85 + 0.15)[..., None]
CORNER = _corner()


def scene_at(t):
    return max(i for i, s in enumerate(SCENES) if s[0] <= t)


def draw_scene(i, t, f):
    return SCENES[i][2](t, f).convert("RGBA")


def render_frame(f):
    t = f / FPS
    i = scene_at(t); s = SCENES[i]
    cur = draw_scene(i, t, f)
    if i > 0 and s[3] and t - s[0] < s[4]:
        prev = draw_scene(i - 1, t, f)
        pf = FOCUS.get(SCENES[i - 1][2].__name__[3:], (W / 2, H / 2)); cf = FOCUS.get(s[2].__name__[3:], (W / 2, H / 2))
        cur = transition(s[3], prev, cur, (t - s[0]) / s[4], f, pf, cf)
    if not (4.2 <= t < 10.0):                         # card + newspaper carry their own text
        E.draw_labels(cur, LABELS, t, f)
    if t >= IRIS_END[0]:
        u = min(1, (t - IRIS_END[0]) / (IRIS_END[1] - IRIS_END[0]))
        cur = iris(cur, FOCUS.get("drawer", (W / 2, H / 2)), 1500 * (1 - u) ** 1.6)
    arr = np.asarray(cur.convert("RGB")).astype(float)
    if t < T_TODAY:
        arr = old_film(arr, f, 1.4 if 4.2 <= t < 7.0 else 1.0)
    if t < 0.25: arr *= t / 0.25
    arr = arr + np.random.default_rng(1000 + f).normal(0, 7 if t < T_TODAY else 4, (H, W, 1))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(os.path.join(OUT, f"{f:05d}.png"))


NFRAMES = int(round(DUR * FPS))

if __name__ == "__main__":
    a, b = int(sys.argv[1]), min(int(sys.argv[2]), NFRAMES)
    for f in range(a, b): render_frame(f)
