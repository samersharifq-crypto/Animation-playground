"""Code-drawn props for «سمّوه البطل», plus placeholders that stand in for the Gemini images
until the real ones are dropped into assets/.

Drawn in code on purpose (Gemini can't write letters and makes objects photographic):
bottle + label + HEROIN letters, medal, balance scale, cigarettes, counters, clock, notifications.
"""
import math, functools, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
import basira_engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
SERIF = os.path.join(HERE, "font", "DejaVuSerif-Bold.ttf")
ORANGE = (226, 110, 52)
GLASS = (74, 128, 124)
GLASS_HI = (156, 200, 188)
GLASS_DK = (44, 84, 86)
CORK = (150, 104, 68)
WOOD = (122, 80, 50)
BRASS = (196, 154, 74)
IRON = (52, 54, 60)


def paper_edge(im, border=9, seed=5, fill=True):
    """Rough cream paper border around everything opaque (same look as E.cutout)."""
    a = np.asarray(im).copy()
    fg = a[..., 3] > 20
    rng = np.random.default_rng(seed)
    dist = ndimage.distance_transform_edt(~fg)
    n1 = ndimage.gaussian_filter(rng.standard_normal(fg.shape), 5); n1 /= np.abs(n1).max() + 1e-6
    paper = dist <= border + 4 * n1
    if fill: paper = ndimage.binary_fill_holes(paper)
    out = np.zeros_like(a)
    out[paper, :3] = E.CREAM; out[paper, 3] = 255
    m = a[..., 3:4] / 255.0
    out[..., :3] = (out[..., :3] * (1 - m) + a[..., :3] * m).astype(np.uint8)
    out[..., 3] = np.maximum(out[..., 3], a[..., 3])
    return Image.fromarray(out, "RGBA")


def _font(path, size):
    return ImageFont.truetype(path, int(size))


# ------------------------------------------------------------------ bottle
def bottle_geom(h):
    w = int(h * 0.62); pad = 40
    cx = pad + w / 2
    g = dict(W=w + pad * 2, H=h + pad * 2, cx=cx, pad=pad)
    g["cork"] = (cx - h * .075, pad, cx + h * .075, pad + h * .08)
    g["neck"] = (cx - h * .1, pad + h * .07, cx + h * .1, pad + h * .22)
    g["body"] = (cx - h * .28, pad + h * .34, cx + h * .28, pad + h)
    g["label"] = (cx - h * .235, pad + h * .48, cx + h * .235, pad + h * .78)
    g["neck_pt"] = (cx, pad + h * .2)
    return g


@functools.lru_cache(None)
def bottle(h=760, text="HEROIN", letters=6, red=0, crack=0.0, dim=0.0):
    """Old medicine bottle with a paper label. letters = how many letters are printed so far;
    red = how many leading letters are brick red (4 -> HERO); crack 0..1 grows the fracture."""
    g = bottle_geom(h)
    im = Image.new("RGBA", (g["W"], g["H"]), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    glass = tuple(int(c * (1 - .45 * dim)) for c in GLASS)
    b0, b1 = g["body"], g["neck"]
    cx = g["cx"]
    d.rounded_rectangle(b0, int(h * .07), fill=glass + (255,), outline=E.INK + (255,), width=5)
    d.polygon([(b1[0], b1[3] - 4), (b1[2], b1[3] - 4), (b0[2] - h * .04, b0[1] + h * .03),
               (b0[0] + h * .04, b0[1] + h * .03)], fill=glass + (255,))
    d.line([(b1[0], b1[3] - 4), (b0[0] + h * .03, b0[1] + h * .04)], fill=E.INK + (255,), width=5)
    d.line([(b1[2], b1[3] - 4), (b0[2] - h * .03, b0[1] + h * .04)], fill=E.INK + (255,), width=5)
    d.rectangle(b1, fill=glass + (255,), outline=E.INK + (255,), width=5)
    lip = (b1[0] - h * .02, b1[1], b1[2] + h * .02, b1[1] + h * .04)
    d.rounded_rectangle(lip, 6, fill=GLASS_DK + (255,), outline=E.INK + (255,), width=4)
    d.rounded_rectangle(g["cork"], 8, fill=CORK + (255,), outline=E.INK + (255,), width=4)
    # glass highlight
    hi = tuple(int(c * (1 - .4 * dim)) for c in GLASS_HI)
    d.rounded_rectangle((b0[0] + h * .045, b0[1] + h * .06, b0[0] + h * .085, b0[3] - h * .08), 12, fill=hi + (255,))
    d.rounded_rectangle((b0[2] - h * .07, b0[1] + h * .08, b0[2] - h * .05, b0[1] + h * .2), 8, fill=hi + (200,))
    # label
    L = g["label"]
    d.rectangle(L, fill=E.CREAM + (255,), outline=E.INK + (255,), width=4)
    d.rectangle((L[0] + 10, L[1] + 10, L[2] - 10, L[3] - 10), outline=E.INK + (255,), width=2)
    lw = L[2] - L[0] - 44
    size = h * .1
    fnt = _font(SERIF, size)
    while d.textlength(text, font=fnt) > lw: size -= 2; fnt = _font(SERIF, size)
    tw = d.textlength(text, font=fnt)
    x = (L[0] + L[2]) / 2 - tw / 2; y = (L[1] + L[3]) / 2 - size * .62
    for i, ch in enumerate(text):
        if i < letters:
            d.text((x, y), ch, font=fnt, fill=(E.BRICK if i < red else E.INK) + (255,))
        x += d.textlength(ch, font=fnt)
    for yy in (L[1] + (L[3] - L[1]) * .2, L[3] - (L[3] - L[1]) * .2):
        d.line((L[0] + 40, yy, L[2] - 40, yy), fill=E.INK + (255,), width=2)
    if crack > 0:
        r = np.random.default_rng(11)
        ox, oy = cx + h * .12, b0[1] + h * .1
        for k in range(6):
            ang = -0.4 + k * 0.62 + r.normal(0, .15)
            px, py = ox, oy; pts = [(px, py)]
            for s in range(int(7 * crack) + 1):
                ang += r.normal(0, .35); L_ = r.uniform(18, 40) * h / 760
                px += math.cos(ang) * L_; py += math.sin(ang) * L_; pts.append((px, py))
            d.line(pts, fill=(250, 250, 244, 255), width=max(3, int(h / 190)))
    im = paper_edge(im, border=max(6, int(h / 85)))
    return im


# ------------------------------------------------------------------ medal
@functools.lru_cache(None)
def medal(s=230):
    """Gold medal on a striped ribbon; pivot = top centre (s*0.5, 20)."""
    pad = 20
    im = Image.new("RGBA", (s + pad * 2, int(s * 1.25) + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = pad + s / 2
    rw = s * .42
    d.polygon([(cx - rw / 2, pad), (cx + rw / 2, pad), (cx + rw / 2, pad + s * .55), (cx, pad + s * .45),
               (cx - rw / 2, pad + s * .55)], fill=E.BRICK + (255,), outline=E.INK + (255,))
    d.rectangle((cx - rw * .17, pad, cx + rw * .17, pad + s * .5), fill=E.NAVY + (255,))
    R = s * .36; cy = pad + s * .78
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=E.GOLD + (255,), outline=E.INK + (255,), width=5)
    d.ellipse((cx - R * .78, cy - R * .78, cx + R * .78, cy + R * .78), outline=(150, 108, 40, 255), width=4)
    star = []
    for k in range(10):
        rr = R * (.55 if k % 2 == 0 else .24); a = -math.pi / 2 + k * math.pi / 5
        star.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(star, fill=(250, 214, 110, 255), outline=(150, 108, 40, 255))
    return paper_edge(im, border=7)


# ------------------------------------------------------------------ balance scale
def draw_scale(c, cx, base_y, size, tilt, left_im, right_im, f, seed=21):
    """Paper balance. tilt>0 -> right pan goes DOWN. left_im/right_im sit in the pans."""
    dx, dy, _ = E.jit(f, seed, 1.6, 0); cx += dx; base_y += dy
    lay = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    post_top = base_y - size * 1.0
    def stroke(pts, w, col):
        d.line(pts, fill=E.CREAM + (255,), width=w + 12, joint="curve")
        d.line(pts, fill=col + (255,), width=w, joint="curve")
    # base + post
    d.polygon([(cx - size * .32, base_y), (cx + size * .32, base_y), (cx + size * .16, base_y - size * .09),
               (cx - size * .16, base_y - size * .09)], fill=WOOD + (255,), outline=E.CREAM + (255,), width=6)
    stroke([(cx, base_y - size * .08), (cx, post_top)], int(size * .05), BRASS)
    a = math.radians(tilt); half = size * .62
    lx, ly = cx - half * math.cos(a), post_top - half * math.sin(a)
    rx, ry = cx + half * math.cos(a), post_top + half * math.sin(a)
    stroke([(lx, ly), (rx, ry)], int(size * .035), BRASS)
    d.ellipse((cx - size * .05, post_top - size * .05, cx + size * .05, post_top + size * .05), fill=E.GOLD + (255,), outline=E.CREAM + (255,), width=5)
    pans = []
    for (ex, ey) in ((lx, ly), (rx, ry)):
        py = ey + size * .5; pw = size * .3
        for k in (-1, 0, 1):
            d.line([(ex, ey), (ex + k * pw * .8, py)], fill=E.INK + (255,), width=3)
        d.chord((ex - pw, py - size * .1, ex + pw, py + size * .1), 0, 180, fill=BRASS + (255,), outline=E.CREAM + (255,), width=6)
        pans.append((ex, py))
    sh = Image.new("RGBA", c.size, (5, 8, 16, 0))
    sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * .5)))
    c.alpha_composite(sh, (10, 14)); c.alpha_composite(lay)
    for (px, py), im in zip(pans, (left_im, right_im)):
        if im is not None:
            E.paste(c, im, px, py - im.height / 2 + 6, seed=seed + 5, f=f)
    return pans


# ------------------------------------------------------------------ counter / strips
@functools.lru_cache(None)
def card(text, size=150, seed=9, ltr=None):
    """Torn cream card with big brick-red text (×2, 20,000, أقوى). Numbers are laid out left-to-right."""
    if ltr is None: ltr = not any("\u0600" <= ch <= "\u06ff" for ch in text)
    if not ltr: return E._strip(text, (text,), 1, seed, size)
    font = ImageFont.truetype(E.FONT, size)
    tw = ImageDraw.Draw(Image.new("RGB", (5, 5))).textlength(text, font=font, direction="ltr")
    blank = E._strip(" ", (), 1, seed, size)                     # torn strip with the right height
    w = int(tw + 96)
    im = blank.resize((w, blank.height), Image.LANCZOS); d = ImageDraw.Draw(im)
    d.text((48, 34 - size * .12), text, font=font, fill=E.BRICK + (255,), direction="ltr")
    return im


def pop_scale(t, t0):
    k = int((t - t0) * E.FPS)
    return {0: 0.6, 1: 1.15, 2: 0.96}.get(k, 1.0)


def paste_pop(c, im, x, y, t, t0, f, seed=40, rot=0):
    s = pop_scale(t, t0)
    if s != 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    E.paste(c, im, x, y, rot=rot, seed=seed, f=f)


# ------------------------------------------------------------------ clock
@functools.lru_cache(None)
def clock_face(r=130):
    im = Image.new("RGBA", (r * 2 + 40, r * 2 + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = r + 20
    d.ellipse((c - r, c - r, c + r, c + r), fill=E.CREAM + (255,), outline=E.INK + (255,), width=10)
    for k in range(12):
        a = k * math.pi / 6; r0 = r * (.72 if k % 3 == 0 else .8)
        d.line((c + r0 * math.cos(a), c + r0 * math.sin(a), c + r * .9 * math.cos(a), c + r * .9 * math.sin(a)),
               fill=E.INK + (255,), width=8 if k % 3 == 0 else 4)
    return paper_edge(im, border=8)


def draw_clock(c, x, y, r, turn, f):
    """turn 0..1 = one full sweep of the (seconds) hand from 12 o'clock."""
    im = clock_face(r).copy(); d = ImageDraw.Draw(im); cc = r + 20 + 20 // 2 - 10 + 10
    cc = im.width / 2
    a = -math.pi / 2 + 2 * math.pi * (round(turn * 60) / 60)
    d.line((cc, cc, cc + r * .78 * math.cos(a), cc + r * .78 * math.sin(a)), fill=E.BRICK + (255,), width=10)
    d.line((cc, cc, cc + r * .45 * math.cos(-math.pi / 3), cc + r * .45 * math.sin(-math.pi / 3)), fill=E.INK + (255,), width=12)
    d.ellipse((cc - 14, cc - 14, cc + 14, cc + 14), fill=E.INK + (255,))
    E.paste(c, im, x, y, seed=71, f=f)


# ------------------------------------------------------------------ cigarettes & notifications
@functools.lru_cache(None)
def cigarette(length=130, angle=0):
    w = int(length * .17)
    im = Image.new("RGBA", (length + 16, w + 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 8 + length, 8 + w), 5, fill=(250, 246, 236, 255), outline=E.INK + (255,), width=3)
    d.rectangle((8 + 2, 8 + 2, 8 + length * .3, 8 + w - 2), fill=(214, 140, 70, 255))
    d.line((8 + length * .3, 8, 8 + length * .3, 8 + w), fill=E.INK + (255,), width=3)
    for k in range(3):
        d.point((8 + length * .1 + k * 9, 8 + w * .4), fill=(160, 90, 40, 255))
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return im


@functools.lru_cache(None)
def notif(w=250, angle=0, kind=0):
    h = int(w * .3)
    im = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 8 + w, 8 + h), 18, fill=(252, 247, 236, 255), outline=E.INK + (255,), width=3)
    ic = [(226, 110, 52), (74, 128, 124), (178, 62, 42), (214, 168, 72)][kind % 4]
    d.rounded_rectangle((18, 18, 18 + h - 20, 18 + h - 20), 10, fill=ic + (255,))
    d.rounded_rectangle((h + 12, 22, w - 40, 32), 4, fill=E.INK + (255,))
    d.rounded_rectangle((h + 12, 44, w - 70, 52), 4, fill=(150, 150, 150, 255))
    d.ellipse((w - 26, 16, w - 4, 38), fill=E.BRICK + (255,))
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return im


def pour(c, t, t0, t1, src, n, sprite, seed, top=-120, travel=0.42, f=0, only=None):
    """Particles shoot out of `src` and pile up from the bottom of the frame until the pile
    reaches `top` (y). sprite(angle_bucket, i) -> RGBA. Returns how many have landed."""
    if t < t0: return 0
    r = np.random.default_rng(seed)
    u = r.uniform(size=n)
    # emission accelerates: few at first, then a flood
    ts = t0 + (t1 - t0) * np.sqrt(np.arange(n) / n)
    land_y = E.H + 30 - (np.arange(n) / n) ** 0.9 * (E.H + 30 - top) + r.normal(0, 40, n)
    land_x = r.uniform(-40, E.W + 40, n)
    ang = r.integers(0, 24, n)
    spin = r.choice([-1, 1], n)
    landed = 0
    for i in range(n):
        dt = t - ts[i]
        if dt < 0: break
        k = min(1.0, dt / travel)
        if k >= 1:
            x, y, a = land_x[i], land_y[i], ang[i]; landed += 1
            if only == "flying": continue
        else:
            if only == "landed": continue
            x = src[0] + (land_x[i] - src[0]) * k
            arc = -260 * math.sin(math.pi * k) * u[i]
            y = src[1] + (land_y[i] - src[1]) * k * k + arc
            a = (ang[i] + spin[i] * int(k * 12)) % 24
        im = sprite(int(a), i)
        E.safe(c, im, int(x - im.width / 2), int(y - im.height / 2))
    return landed


def cig_sprite(a, i):
    return cigarette(130, a * 15)


def notif_sprite(a, i):
    return notif(240, (a - 12) * 3, i % 4)


# ------------------------------------------------------------------ placeholders for the Gemini images
def _fig_canvas(w=900, h=1400):
    im = Image.new("RGB", (w, h), (255, 255, 255)); return im, ImageDraw.Draw(im)


def _limb(d, pts, w, col=ORANGE):
    d.line(pts, fill=E.NAVY, width=w + 10, joint="curve")
    d.line(pts, fill=col, width=w, joint="curve")
    for p in pts:
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=col)


def _head(d, cx, cy, r=78, face=1, moustache=False, glasses=False, cap=False, hood=False):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE, outline=E.NAVY, width=6)
    d.polygon([(cx + face * r * .92, cy - 6), (cx + face * (r + 26), cy + 18), (cx + face * r * .9, cy + 28)], fill=ORANGE, outline=E.NAVY)
    d.ellipse((cx + face * r * .45 - 7, cy - 22, cx + face * r * .45 + 7, cy - 8), fill=E.NAVY)
    d.arc((cx - r, cy - r - 6, cx + r, cy + r * .4), 180, 360, fill=E.NAVY, width=18)
    if moustache: d.chord((cx + face * r * .5 - 30, cy + 22, cx + face * r * .5 + 34, cy + 52), 180, 360, fill=E.NAVY)
    if glasses:
        gx = cx + face * r * .45
        d.ellipse((gx - 20, cy - 34, gx + 20, cy + 4), outline=E.NAVY, width=5)
    if cap:
        d.chord((cx - r - 6, cy - r - 30, cx + r + 6, cy + 10), 180, 360, fill=(70, 60, 58), outline=E.NAVY, width=5)
        d.polygon([(cx + face * 20, cy - 34), (cx + face * (r + 50), cy - 26), (cx + face * 20, cy - 14)], fill=(70, 60, 58))
    if hood:
        d.arc((cx - r - 24, cy - r - 24, cx + r + 24, cy + r + 24), 100 if face > 0 else -80, 300 if face > 0 else 120, fill=(64, 72, 92), width=34)


def placeholder_figure(kind):
    """Simple red-figure stand-ins so the timing can be reviewed before the Gemini images exist."""
    im, d = _fig_canvas()
    coat = (238, 232, 218)
    if kind in ("chemist_k1", "chemist_k2"):
        cx = 430
        lean = 0 if kind == "chemist_k1" else -30
        _limb(d, [(cx - 40, 900), (cx - 60, 1330)], 70); _limb(d, [(cx + 40, 900), (cx + 60, 1330)], 70)
        d.polygon([(cx - 140 + lean, 420), (cx + 140 + lean, 420), (cx + 170, 1050), (cx - 170, 1050)], fill=coat, outline=E.NAVY, width=7)
        d.polygon([(cx - 50 + lean, 420), (cx + 50 + lean, 420), (cx + 20 + lean, 640), (cx - 20 + lean, 640)], fill=ORANGE, outline=E.NAVY, width=5)
        d.line([(cx + lean, 440), (cx + lean, 640)], fill=E.BRICK, width=14)
        hx, hy = cx + lean + 10, 320
        _head(d, hx, hy, moustache=True, glasses=True)
        if kind == "chemist_k1":
            _limb(d, [(cx - 110 + lean, 470), (cx - 140, 700), (cx - 60, 860)], 56, coat)
            _limb(d, [(cx + 110 + lean, 470), (cx + 230, 520), (cx + 260, 330)], 56, coat)
            d.rounded_rectangle((cx + 225, 220, cx + 300, 330), 12, fill=GLASS, outline=E.NAVY, width=5)
            d.chord((hx + 10, hy + 20, hx + 70, hy + 60), 0, 180, fill=E.NAVY)
        else:
            _limb(d, [(cx - 110 + lean, 470), (cx - 210, 330), (hx - 40, hy - 70)], 56, coat)
            _limb(d, [(cx + 110 + lean, 470), (cx + 200, 330), (hx + 40, hy - 74)], 56, coat)
            d.ellipse((hx + 30, hy + 30, hx + 60, hy + 62), fill=E.NAVY)
    elif kind == "worker":
        d.rectangle((520, 760, 880, 800), fill=WOOD, outline=E.NAVY, width=6)
        d.rectangle((560, 800, 590, 1250), fill=WOOD); d.rectangle((820, 800, 850, 1250), fill=WOOD)
        d.rectangle((180, 1000, 380, 1040), fill=WOOD); d.rectangle((200, 1040, 230, 1250), fill=WOOD); d.rectangle((330, 1040, 360, 1250), fill=WOOD)
        _limb(d, [(300, 980), (520, 990), (520, 1240)], 70); _limb(d, [(260, 990), (470, 1010), (480, 1250)], 70, (205, 96, 44))
        d.polygon([(200, 560), (380, 560), (390, 1000), (210, 1000)], fill=ORANGE, outline=E.NAVY, width=7)
        d.polygon([(330, 640), (400, 640), (410, 980), (330, 980)], fill=(196, 186, 168), outline=E.NAVY, width=5)
        _head(d, 300, 470, cap=True)
        _limb(d, [(330, 620), (470, 720), (600, 740)], 50); _limb(d, [(290, 640), (430, 760), (620, 760)], 50, (205, 96, 44))
        d.rounded_rectangle((590, 735, 690, 755), 5, fill=(250, 246, 236), outline=E.NAVY, width=3)
    elif kind == "young":
        d.polygon([(220, 600), (420, 560), (470, 1150), (230, 1180)], fill=(64, 72, 92), outline=E.NAVY, width=7)
        _limb(d, [(330, 1150), (600, 880), (720, 1220)], 84, (60, 64, 80))
        _limb(d, [(300, 1170), (560, 940), (660, 1250)], 84, (48, 52, 66))
        _head(d, 380, 470, hood=True)
        _limb(d, [(400, 640), (520, 800), (560, 700)], 48, (64, 72, 92))
        d.rounded_rectangle((540, 620, 590, 720), 10, fill=(255, 246, 225), outline=E.NAVY, width=5)
    return im


def placeholder_machine():
    im = Image.new("RGB", (1000, 1000), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.polygon([(320, 60), (700, 60), (620, 260), (400, 260)], fill=(96, 88, 80), outline=E.NAVY, width=8)
    d.rectangle((240, 260, 820, 760), fill=IRON, outline=E.NAVY, width=10)
    for k in range(4):
        d.ellipse((300 + k * 130, 320, 360 + k * 130, 380), fill=(120, 110, 96), outline=E.NAVY, width=5)
    d.rectangle((300, 460, 760, 520), fill=(90, 86, 82), outline=E.NAVY, width=5)
    d.polygon([(820, 600), (960, 660), (960, 720), (820, 700)], fill=(110, 100, 90), outline=E.NAVY, width=6)
    d.rectangle((270, 760, 330, 960), fill=IRON); d.rectangle((730, 760, 790, 960), fill=IRON)
    d.rectangle((220, 940, 840, 980), fill=IRON)
    return im


def flywheel(r=170, angle=0):
    im = Image.new("RGBA", (r * 2 + 30, r * 2 + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = r + 15
    d.ellipse((c - r, c - r, c + r, c + r), outline=E.CREAM + (255,), width=40)
    d.ellipse((c - r + 6, c - r + 6, c + r - 6, c + r - 6), outline=IRON + (255,), width=30)
    for k in range(6):
        a = math.radians(angle + k * 60)
        d.line((c, c, c + (r - 20) * math.cos(a), c + (r - 20) * math.sin(a)), fill=IRON + (255,), width=16)
    d.ellipse((c - 30, c - 30, c + 30, c + 30), fill=BRASS + (255,), outline=E.INK + (255,), width=4)
    return im


def _shapes_bg(kind, w=1080, h=1920, seed=3):
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    def wob(box, fill):
        x0, y0, x1, y1 = box
        pts = E.torn_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 0, int(r.integers(1, 999)), 4)
        d.polygon(pts, fill=fill)
    if kind == "lab":
        d.rectangle((0, 0, w, h), fill=(226, 212, 184))
        wob((620, 180, 960, 820), (150, 186, 184)); d.line((790, 180, 790, 820), fill=(110, 80, 56), width=14); d.line((620, 500, 960, 500), fill=(110, 80, 56), width=14)
        for sy in (330, 560, 790):
            wob((60, sy, 560, sy + 26), (128, 88, 56))
            for k in range(6):
                bh = r.integers(70, 150); bx = 90 + k * 76
                col = [(74, 128, 124), (150, 110, 60), (196, 154, 74), (120, 150, 140)][k % 4]
                wob((bx, sy - bh, bx + 50, sy), col)
        wob((0, 1080, w, 1180), (128, 88, 56)); wob((0, 1180, w, h), (200, 182, 150))
        wob((700, 900, 760, 1080), (196, 154, 74)); wob((680, 1060, 800, 1080), (128, 88, 56))
    elif kind == "factory":
        d.rectangle((0, 0, w, h), fill=(150, 70, 52))
        for y in range(0, h, 44):
            for x in range(-60 if (y // 44) % 2 else 0, w, 120):
                d.rectangle((x + 3, y + 3, x + 117, y + 41), fill=tuple(int(c * r.uniform(.86, 1.04)) for c in (160, 76, 56)))
        for x0 in (110, 610):
            d.rectangle((x0, 300, x0 + 360, 880), fill=(200, 202, 204)); d.pieslice((x0, 120, x0 + 360, 480), 180, 360, fill=(200, 202, 204))
            d.line((x0 + 180, 120, x0 + 180, 880), fill=(80, 60, 50), width=12); d.line((x0, 560, x0 + 360, 560), fill=(80, 60, 50), width=12)
        wob((0, 60, w, 120), (96, 62, 40))
        wob((0, 1180, w, h), (120, 92, 64))
        for x0 in (60, 820):
            wob((x0, 1050, x0 + 200, 1190), (150, 112, 66)); wob((x0 + 20, 1030, x0 + 180, 1060), (110, 120, 60))
    elif kind == "room":
        d.rectangle((0, 0, w, h), fill=(30, 42, 66))
        wob((640, 260, 960, 760), (14, 20, 36)); d.line((800, 260, 800, 760), fill=(46, 60, 90), width=12)
        for k in range(18):
            x, y = r.uniform(660, 940), r.uniform(280, 740); d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(220, 214, 190))
        wob((0, 1200, w, h), (22, 30, 50)); d.line((0, 1200, w, 1200), fill=(46, 60, 90), width=8)
    return im


def make_placeholder_bg(kind, path):
    _shapes_bg(kind).filter(ImageFilter.GaussianBlur(0.6)).save(path)


@functools.lru_cache(None)
def logo_placeholder(size=230):
    """Stand-in until the real logo from «الحياة المزدوجة» is supplied (assets/logo.png)."""
    fnt = ImageFont.truetype(E.FONT, size)
    tmp = ImageDraw.Draw(Image.new("RGB", (5, 5)))
    tw = int(tmp.textlength("بصيرة", font=fnt, direction="rtl", language="ar"))
    im = Image.new("RGBA", (tw + 80, int(size * 1.9)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((40, 0), "بصيرة", font=fnt, fill=E.CREAM + (255,), direction="rtl", language="ar")
    return im


def eye(size=260, open_=1.0):
    im = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = (size + 40) / 2; hh = size * .32 * open_
    d.polygon([(20, c)] + [(c + (size / 2) * math.cos(a), c - hh * math.sin(a)) for a in np.linspace(math.pi, 0, 24)] + [(size + 20, c)]
              + [(c + (size / 2) * math.cos(a), c + hh * math.sin(a)) for a in np.linspace(0, math.pi, 24)], fill=E.CREAM + (255,))
    if open_ > .2:
        d.ellipse((c - size * .14, c - size * .14, c + size * .14, c + size * .14), fill=E.BRICK + (255,))
        d.ellipse((c - size * .06, c - size * .06, c + size * .06, c + size * .06), fill=E.INK + (255,))
    return im


# ------------------------------------------------------------------ cut-paper cigarette machine
# Drawn in code in the same layered torn-paper look as the Gemini props (Gemini limit reached).
MACHINE_WHEEL = (-0.30, 0.02)    # flywheel centre, as a fraction of the body image (from its centre)
MACHINE_CHUTE = (0.47, 0.20)     # where the cigarettes come out


def _paper_tex(shape, seed, amp=14):
    r = np.random.default_rng(seed)
    low = ndimage.gaussian_filter(r.standard_normal(shape), 18); low /= np.abs(low).max() + 1e-6
    fib = ndimage.gaussian_filter(r.standard_normal(shape), 1.0); fib /= np.abs(fib).max() + 1e-6
    return low * amp + fib * amp * 0.45


def torn_piece(lay, pts, color, seed, edge=(236, 228, 210), amp=4.5, rim=5):
    """One torn paper scrap: pale fibrous rim peeking out under the coloured face."""
    d = ImageDraw.Draw(lay)
    r = np.random.default_rng(seed)
    def jag(p, a):
        base = []
        for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]):
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 4))
            for i in range(n):
                u = i / n; base.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u))
        m = len(base)
        wob = ndimage.gaussian_filter1d(r.standard_normal((m, 2)), 3, axis=0, mode="wrap")
        wob = wob / (np.abs(wob).max() + 1e-6) * a
        fine = r.standard_normal((m, 2)) * a * 0.18
        return [(x + wob[i, 0] + fine[i, 0], y + wob[i, 1] + fine[i, 1]) for i, (x, y) in enumerate(base)]
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    grow = [(x + (x - cx) / max(1, math.hypot(x - cx, y - cy)) * rim, y + (y - cy) / max(1, math.hypot(x - cx, y - cy)) * rim) for x, y in pts]
    d.polygon(jag(grow, amp * 1.4), fill=edge + (255,))
    d.polygon(jag(pts, amp), fill=tuple(color) + (255,))


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle(cx, cy, r, n=40):
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def _texture(im, seed):
    a = np.asarray(im).astype(float)
    a[..., :3] += _paper_tex(a.shape[:2], seed)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


@functools.lru_cache(None)
def machine_body():
    S = 1000
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    iron, iron2, iron3 = (50, 52, 58), (72, 74, 82), (36, 38, 44)
    brass, tob = (186, 146, 72), (128, 84, 46)
    # legs and base
    for x in (300, 690):
        torn_piece(lay, [(x - 30, 720), (x + 30, 720), (x + 44, 930), (x - 44, 930)], iron3, x)
        torn_piece(lay, rect(x - 75, 925, x + 75, 960), iron, x + 1)
    torn_piece(lay, rect(270, 840, 730, 870), iron2, 3)
    # hopper with tobacco
    torn_piece(lay, [(330, 70), (690, 70), (610, 280), (410, 280)], iron2, 4)
    torn_piece(lay, [(345, 70), (420, 30), (500, 52), (580, 22), (675, 70)], tob, 5, edge=(196, 150, 96))
    for k in range(9):
        x = 370 + k * 35
        torn_piece(lay, rect(x, 40 + (k % 3) * 8, x + 14, 78), (150, 102, 58), 50 + k, edge=(196, 150, 96), rim=2)
    torn_piece(lay, rect(320, 60, 700, 90), iron, 6)
    # main body
    torn_piece(lay, rect(230, 270, 790, 740), iron, 7)
    torn_piece(lay, rect(270, 310, 750, 470), iron2, 8)
    torn_piece(lay, rect(270, 500, 750, 700), iron2, 9)
    # rollers / drum and gears
    torn_piece(lay, circle(600, 390, 62), iron3, 10)
    torn_piece(lay, circle(600, 390, 26), brass, 11, edge=(230, 200, 140))
    for gx, gy, gr in ((420, 600, 48), (500, 640, 30)):
        teeth = []
        for k in range(28):
            a = k * math.pi * 2 / 28; rr = gr + (8 if k % 2 else 0)
            teeth.append((gx + rr * math.cos(a), gy + rr * math.sin(a)))
        torn_piece(lay, teeth, brass, gx, edge=(230, 200, 140), rim=3)
        torn_piece(lay, circle(gx, gy, gr * .3), iron3, gx + 1, rim=2)
    # long paper roll belt running to the chute
    torn_piece(lay, rect(640, 560, 790, 590), (232, 226, 210), 12, edge=(250, 246, 236), rim=3)
    # chute at the front (right)
    torn_piece(lay, [(770, 560), (930, 610), (950, 680), (770, 640)], iron2, 13)
    torn_piece(lay, [(780, 600), (935, 640), (940, 660), (780, 625)], iron3, 14, rim=2)
    for k in range(3):
        x = 800 + k * 40
        torn_piece(lay, [(x, 600 + k * 11), (x + 60, 615 + k * 11), (x + 60, 627 + k * 11), (x, 612 + k * 11)], (246, 240, 226), 60 + k, rim=2)
    # rivets
    d = ImageDraw.Draw(lay)
    for x in range(255, 780, 66):
        for y in (285, 725):
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=brass + (255,))
    # axle stub where the flywheel sits
    torn_piece(lay, circle(350, 520, 30), brass, 15, edge=(230, 200, 140))
    im = _texture(lay, 21)
    return paper_edge(im, border=8, seed=9, fill=False)


@functools.lru_cache(None)
def machine_wheel(r=170, angle=0):
    S = r * 2 + 60; c = S / 2
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    iron, iron3, brass = (58, 60, 66), (36, 38, 44), (186, 146, 72)
    torn_piece(lay, circle(c, c, r, 60), iron, 31)
    torn_piece(lay, circle(c, c, r - 34, 60), (0, 0, 0), 32, edge=(0, 0, 0), rim=0)
    a = np.asarray(lay).copy()
    yy, xx = np.mgrid[0:S, 0:S]; hole = (xx - c) ** 2 + (yy - c) ** 2 < (r - 34) ** 2
    a[hole] = 0
    lay = Image.fromarray(a, "RGBA")
    for k in range(6):
        t = math.radians(angle + k * 60); n = math.radians(angle + k * 60 + 90)
        x1, y1 = c + (r - 20) * math.cos(t), c + (r - 20) * math.sin(t)
        w0, w1 = 16, 9
        torn_piece(lay, [(c + w0 * math.cos(n), c + w0 * math.sin(n)), (x1 + w1 * math.cos(n), y1 + w1 * math.sin(n)),
                         (x1 - w1 * math.cos(n), y1 - w1 * math.sin(n)), (c - w0 * math.cos(n), c - w0 * math.sin(n))], iron3, 40 + k, rim=3)
    torn_piece(lay, circle(c, c, 38), brass, 47, edge=(230, 200, 140))
    torn_piece(lay, circle(c, c, 12), iron3, 48, rim=2)
    return paper_edge(_texture(lay, 22), border=7, seed=10, fill=False)
