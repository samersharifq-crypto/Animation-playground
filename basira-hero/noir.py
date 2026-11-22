"""Noir toolkit for «سمّوه البطل»: camera (zoom / pan / dutch tilt / shake), light pools, venetian-blind
shadows, a noir grade, noir transitions (iris, blinds, zoom-through, rip, hard cut) and the Gemini props
(bottles with HEROIN printed in code, medal, balance scale, clock, cigarettes, notifications)."""
import math, functools, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage
import basira_engine as E

W, H = E.W, E.H
HERE = os.path.dirname(os.path.abspath(__file__))
SERIF = os.path.join(HERE, "font", "DejaVuSerif-Bold.ttf")

# ------------------------------------------------------------------ camera
def ease(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def ramp(t, t0, t1, a, b):
    return a + (b - a) * ease((t - t0) / max(1e-6, t1 - t0))


def shake(f, t, t0, dur=0.35, amp=18, seed=5):
    if not (t0 <= t < t0 + dur): return 0.0, 0.0
    k = 1 - (t - t0) / dur
    r = np.random.default_rng(seed * 31 + f)
    return r.normal(0, amp * k), r.normal(0, amp * k)


def camera(img, z=1.0, fx=None, fy=None, rot=0.0, dx=0.0, dy=0.0):
    """Crop a W/z x H/z window around (fx, fy), resize back to WxH, then dutch-tilt by rot degrees."""
    fx = W / 2 if fx is None else fx; fy = H / 2 if fy is None else fy
    z = max(1.0, z) * (1 + abs(rot) * 0.065)
    cw, ch = W / z, H / z
    x0 = min(max(fx - cw / 2 + dx, 0), W - cw); y0 = min(max(fy - ch / 2 + dy, 0), H - ch)
    out = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    if rot: out = out.rotate(rot, resample=Image.BILINEAR)
    return out


def to_screen(p, z, fx, fy):
    """Where a scene point lands on screen for camera (z, fx, fy) (no tilt)."""
    cw, ch = W / z, H / z
    x0 = min(max(fx - cw / 2, 0), W - cw); y0 = min(max(fy - ch / 2, 0), H - ch)
    return (p[0] - x0) * z, (p[1] - y0) * z


# ------------------------------------------------------------------ light & shadow
@functools.lru_cache(None)
def _poly_mask(pts, blur):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(list(pts), fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255


@functools.lru_cache(None)
def _ellipse_mask(box, blur):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse(box, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255


def cone(top, bottom, w_top, w_bot, blur=45):
    (x0, y0), (x1, y1) = top, bottom
    pts = ((x0 - w_top / 2, y0), (x0 + w_top / 2, y0), (x1 + w_bot / 2, y1), (x1 - w_bot / 2, y1))
    return _poly_mask(tuple((round(x), round(y)) for x, y in pts), blur)


def pool(box, blur=120):
    return _ellipse_mask(tuple(int(v) for v in box), blur)


@functools.lru_cache(None)
def blinds(angle=-18, period=70, duty=0.45, shift=0, soft=3):
    """Venetian-blind shadow: 1 in the light, 0 in the slat shadows."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle)
    v = (yy * math.cos(a) - xx * math.sin(a) + shift) % period
    m = (v > duty * period).astype(np.float32)
    return ndimage.gaussian_filter(m, soft)


def light(c, mask, dark=0.35, warm=(255, 236, 196), glow=0.22):
    """Noir lighting on a canvas: everything outside `mask` falls into shadow, the lit area warms up."""
    a = np.asarray(c.convert("RGB")).astype(np.float32)
    m = mask[..., None]
    a = a * (dark + (1 - dark) * m) + np.array(warm, np.float32) * glow * m
    c.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA"))


@functools.lru_cache(None)
def _vig(strength):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    return np.clip(1 - strength * d ** 1.1, 0.08, 1)[..., None]


SHADOW = np.array((14, 20, 36), np.float32)
HILITE = np.array((250, 238, 214), np.float32)


def grade(arr, amt=0.5, vig=0.55):
    """Noir grade: desaturate, S-curve contrast, navy shadows / cream highlights, heavy vignette."""
    if amt <= 0: return arr * _vig(vig)
    lum = arr.mean(axis=2, keepdims=True)
    a = arr * (1 - 0.6 * amt) + lum * 0.6 * amt
    x = np.clip(a / 255, 0, 1)
    s = x * x * (3 - 2 * x)
    x = x * (1 - 0.8 * amt) + s * 0.8 * amt
    l = np.clip(lum / 255, 0, 1)
    tone = SHADOW * (1 - l) + HILITE * l
    a = x * 255 * (1 - 0.22 * amt) + tone * 0.22 * amt
    return a * _vig(vig)


# ------------------------------------------------------------------ transitions (screen space, float arrays)
@functools.lru_cache(None)
def _circle(cx, cy, r):
    m = Image.new("L", (W, H), 0)
    if r > 0: ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)[..., None] / 255


def iris(arr, u, cx=W / 2, cy=H / 2):
    """u=1 fully open, 0 closed to black."""
    r = int(round(ease(u) * 1150 / 10) * 10)
    return arr * _circle(int(cx), int(cy), r)


def blinds_wipe(prev, cur, u, slats=14):
    """Venetian-blind wipe: each slat rotates open onto the new scene."""
    p = H / slats
    yy = (np.arange(H) % p) / p
    m = (np.abs(yy - 0.5) < 0.5 * ease(u)).astype(np.float32)[:, None, None]
    edge = (np.abs(np.abs(yy - 0.5) - 0.5 * ease(u)) < 0.012).astype(np.float32)[:, None, None]
    out = prev * (1 - m) + cur * m
    return out * (1 - edge) + np.array(E.CREAM, np.float32) * edge


def rip(prev, cur, u, f):
    a = Image.fromarray(np.clip(prev, 0, 255).astype(np.uint8)).convert("RGBA")
    b = Image.fromarray(np.clip(cur, 0, 255).astype(np.uint8)).convert("RGBA")
    return np.asarray(E.tear(a, b, u, f).convert("RGB")).astype(np.float32)


# ------------------------------------------------------------------ the Gemini props
@functools.lru_cache(None)
def comp(name, x, y):
    """The separate piece of a cut-out sheet that contains cut-coords point (x, y): (image, origin)."""
    a = np.asarray(E.load(name)).copy()
    lab, _ = ndimage.label(a[..., 3] > 0)
    k = lab[int(y), int(x)]
    assert k, (name, x, y)
    ys, xs = np.where(lab == k)
    a[lab != k, 3] = 0
    x0, y0 = xs.min(), ys.min()
    return Image.fromarray(a, "RGBA").crop((x0, y0, xs.max() + 1, ys.max() + 1)), (int(x0), int(y0))


def _sc(im, s):
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


# bottles: label box and neck point in cut-out coords (source minus cut offset 263, 42)
LABEL = (90, 480, 410, 720)
NECK = (249, 262)


@functools.lru_cache(None)
def bottle(h, variant="bottle", text="HEROIN", letters=6, red=0):
    im = E.load(variant).copy(); d = ImageDraw.Draw(im)
    if text and letters:
        L = LABEL; lw = (L[2] - L[0]) * 0.84; size = 120
        fnt = ImageFont.truetype(SERIF, size)
        while d.textlength(text, font=fnt) > lw: size -= 2; fnt = ImageFont.truetype(SERIF, size)
        x = (L[0] + L[2]) / 2 - d.textlength(text, font=fnt) / 2; y = (L[1] + L[3]) / 2 - size * 0.62
        for i, ch in enumerate(text):
            if i < letters:
                col = (178, 48, 34, 240) if i < red else (32, 36, 52, 235)
                d.text((x, y), ch, font=fnt, fill=col)
            x += d.textlength(ch, font=fnt)
    return _sc(im, h / im.height)


def neck_point(h, cx, cy, variant="bottle"):
    im = E.load(variant); s = h / im.height
    return cx + (NECK[0] - im.width / 2) * s, cy + (NECK[1] - im.height / 2) * s


def label_point(h, cx, cy, variant="bottle", fx=0.5, fy=0.5):
    im = E.load(variant); s = h / im.height
    lx = LABEL[0] + (LABEL[2] - LABEL[0]) * fx; ly = LABEL[1] + (LABEL[3] - LABEL[1]) * fy
    return cx + (lx - im.width / 2) * s, cy + (ly - im.height / 2) * s


@functools.lru_cache(None)
def medal(h):
    im = E.load("medal"); return _sc(im, h / im.height)


def hang_medal(c, px, py, h, angle, f):
    m = medal(h)
    E.pivot_paste(c, m, (m.width / 2, 14 * h / 900), (px, py), angle, f, seed=63, pad=160)


# balance scale (cut coords of the "scale" sheet)
POST_TOP = (215, 62); BEAM_PIVOT = (536, 290); HOOKS = ((338, 336), (735, 336))
PAN_RING = {"L": (210, 588), "R": (576, 586)}; PAN_DISH = 968


def draw_scale(c, cx, top_y, s, tilt, left, right, f, seed=21):
    """Scale with its post fork at (cx, top_y), sheet scale s. tilt>0: right pan down.
    left/right: RGBA items standing in the pans (or None). Returns the pan dish positions."""
    dx, dy, _ = E.jit(f, seed, 1.5, 0); cx += dx; top_y += dy
    base, bo = comp("scale", 215, 300)
    beam, bmo = comp("scale", 536, 285)
    def scr(p): return cx + (p[0] - POST_TOP[0]) * s, top_y + (p[1] - POST_TOP[1]) * s
    bx, by = scr(bo); E.paste(c, _sc(base, s), bx + base.width * s / 2, by + base.height * s / 2)
    E.pivot_paste(c, _sc(beam, s), ((BEAM_PIVOT[0] - bmo[0]) * s, (BEAM_PIVOT[1] - bmo[1]) * s), (cx, top_y), -tilt, f, seed=seed + 1, pad=260)
    th = math.radians(tilt); out = []
    for side, hook in zip(("L", "R"), HOOKS):
        vx, vy = (hook[0] - BEAM_PIVOT[0]) * s, (hook[1] - BEAM_PIVOT[1]) * s
        hx = cx + vx * math.cos(th) - vy * math.sin(th); hy = top_y + vx * math.sin(th) + vy * math.cos(th)
        ring = PAN_RING[side]
        pan, po = comp("scale", ring[0], 1000)
        ps = _sc(pan, s)
        px = hx - (ring[0] - po[0]) * s; py = hy - (ring[1] - po[1]) * s
        out.append((hx, hy + (PAN_DISH - ring[1]) * s))
        E.paste(c, ps, px + ps.width / 2, py + ps.height / 2, shadow=False)
        item = left if side == "L" else right
        if item is not None:
            E.paste(c, item, hx, hy + (PAN_DISH - ring[1]) * s - item.height / 2 + 6, seed=seed + 4, f=f)
    return out


# clock (cut coords of the "clock" sheet)
FACE_C = (382, 367); RED_RING = (388, 899); RED_TIP = (45, 760); NAVY_RING = (527, 828); NAVY_TIP = (725, 680)


def draw_clock(c, x, y, size, turn, f):
    face, fo = comp("clock", 382, 367)
    s = size / face.height
    E.paste(c, _sc(face, s), x + (fo[0] + face.width / 2 - FACE_C[0]) * s, y + (fo[1] + face.height / 2 - FACE_C[1]) * s, seed=71, f=f)
    for ring, tip, piece_pt, ang in ((NAVY_RING, NAVY_TIP, (600, 773), -60), (RED_RING, RED_TIP, (250, 843), -90 + 360 * round(turn * 60) / 60)):
        hand, ho = comp("clock", *piece_pt)
        nat = math.degrees(math.atan2(tip[1] - ring[1], tip[0] - ring[0]))
        E.pivot_paste(c, _sc(hand, s), ((ring[0] - ho[0]) * s, (ring[1] - ho[1]) * s), (x, y), -(ang - nat), f, seed=72, pad=int(400 * s) + 20)


# cigarettes & notifications
CIG_PTS = ((360, 127), (368, 383), (354, 607), (375, 825))
NOTE_PTS = ((357, 143), (357, 384), (356, 625), (358, 865))


@functools.lru_cache(None)
def cig(i, length=150, angle=0):
    im, _ = comp("cigarettes", *CIG_PTS[i % 4])
    im = _sc(im, length / im.width)
    return im.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else im


@functools.lru_cache(None)
def note(i, width=250, angle=0):
    im, _ = comp("notifications", *NOTE_PTS[i % 4])
    im = _sc(im, width / im.width)
    return im.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else im


def cig_sprite(a, i): return cig(i % 4, 150, a * 15)
def note_sprite(a, i): return note(i % 4, 250, (a - 12) * 3)
