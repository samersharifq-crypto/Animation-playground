"""basira_engine.py - torn-paper stop-motion engine for بصيرة videos."""
import os, math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from scipy import ndimage

W, H, FPS = 1920, 1080, 12
NAVY = (24, 34, 54)
CREAM = (244, 236, 220)
INK = (22, 30, 48)
BRICK = (178, 62, 42)
GOLD = (214, 168, 72)
ROOT = "."
FONT = None

def setup(root, font):
    global ROOT, FONT
    ROOT, FONT = root, font
    for d in ("cut", "bg", "frames"):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)

# ------------------------------------------------------------------ cut-outs
def cutout(name, src, border=10, seed=7, min_hole=2500, wmin=228, wspread=30):
    """White-background illustration -> transparent PNG with a rough cream paper border.
    Big white gaps (between two figures, inside an arm) stay see-through instead of turning white/cream."""
    rng = np.random.default_rng(seed)
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    white = (a.min(axis=2) > wmin) & ((a.max(axis=2) - a.min(axis=2)) < wspread)
    lab, _ = ndimage.label(white)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    wsz = ndimage.sum(white, lab, range(1, lab.max() + 1))
    big_holes = set(np.where(wsz > min_hole)[0] + 1) - edge
    bg = np.isin(lab, list(edge | big_holes))
    fg = ~bg
    fg = ndimage.binary_opening(fg, iterations=1)
    lab2, n2 = ndimage.label(fg)
    if n2:
        sizes = ndimage.sum(fg, lab2, range(1, n2 + 1))
        fg = np.isin(lab2, np.where(sizes > 400)[0] + 1)
    fg = ndimage.binary_fill_holes(ndimage.binary_closing(fg, iterations=6)) & ~ndimage.binary_erosion(bg, iterations=8)
    dist = ndimage.distance_transform_edt(~fg)
    n1 = ndimage.gaussian_filter(rng.standard_normal(fg.shape), 6); n1 /= np.abs(n1).max() + 1e-6
    n2_ = ndimage.gaussian_filter(rng.standard_normal(fg.shape), 1.2); n2_ /= np.abs(n2_).max() + 1e-6
    paper = ndimage.binary_fill_holes(dist <= border + 5 * n1 + 2 * n2_)
    paper &= ~ndimage.binary_erosion(bg, iterations=border + 6)   # keep real gaps see-through
    rgba = np.zeros(fg.shape + (4,), np.uint8)
    rgba[paper, :3] = CREAM; rgba[paper, 3] = 255
    rgba[fg, :3] = np.asarray(im)[fg]
    ys, xs = np.where(paper)
    y0, y1 = max(ys.min() - 30, 0), ys.max() + 30
    x0, x1 = max(xs.min() - 30, 0), xs.max() + 30
    Image.fromarray(rgba[y0:y1, x0:x1], "RGBA").save(os.path.join(ROOT, "cut", name + ".png"))

def cutout_all(mapping, **kw):
    for k, v in mapping.items():
        cutout(k, v, **kw)

@functools.lru_cache(None)
def load(name):
    return Image.open(os.path.join(ROOT, "cut", name + ".png")).convert("RGBA")

@functools.lru_cache(None)
def scaled(name, h):
    im = load(name); s = h / im.height
    return im.resize((max(1, int(im.width * s)), int(h)), Image.LANCZOS)

@functools.lru_cache(None)
def pieces(name, min_px=5000):
    """Split a sheet (e.g. two columns, three trees) into separate pieces, left to right."""
    a = np.asarray(load(name)); m = a[..., 3] > 0
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    out = []
    for k in [i + 1 for i in range(n) if sizes[i] > min_px]:
        ys, xs = np.where(lab == k)
        sub = a.copy(); sub[lab != k, 3] = 0
        out.append((xs.mean(), Image.fromarray(sub, "RGBA").crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))))
    return [im for _, im in sorted(out, key=lambda p: p[0])]

@functools.lru_cache(None)
def piece_h(name, i, h):
    im = pieces(name)[i]; s = h / im.height
    return im.resize((int(im.width * s), int(h)), Image.LANCZOS)

def match_orange(name, target=(226, 110, 52)):
    """Pull a figure's orange paint toward the channel's standard orange (keeps characters consistent)."""
    im = load(name); a = np.asarray(im).astype(float)
    hsv = np.asarray(im.convert("RGB").convert("HSV")).astype(float)
    m = (hsv[..., 0] > 8) & (hsv[..., 0] < 26) & (hsv[..., 1] > 110)
    mean = a[m, :3].mean(0)
    a[m, :3] = np.clip(a[m, :3] * (np.array(target) / mean), 0, 255)
    Image.fromarray(a.astype(np.uint8), "RGBA").save(os.path.join(ROOT, "cut", name + ".png"))
    load.cache_clear(); scaled.cache_clear()

# ------------------------------------------------------------------ textures
_rng = np.random.default_rng(3)
def _texture():
    h, w = H + 200, W + 200
    low = ndimage.gaussian_filter(_rng.standard_normal((h, w)), 40); low /= np.abs(low).max()
    mid = ndimage.gaussian_filter(_rng.standard_normal((h, w)), 3); mid /= np.abs(mid).max()
    fib = np.zeros((h, w))
    for _ in range(900):
        x, y = _rng.integers(0, w), _rng.integers(0, h)
        L = _rng.integers(10, 40); ang = _rng.uniform(0, math.pi)
        for t in range(L):
            xx, yy = int(x + t * math.cos(ang)), int(y + t * math.sin(ang))
            if 0 <= xx < w and 0 <= yy < h: fib[yy, xx] = 1
    return low * 10 + mid * 5 + ndimage.gaussian_filter(fib, 0.7) * 14
TEX = _texture()
_yy, _xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.38 * (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) ** 1.2)[..., None]

def paper_bg(f, color=NAVY, dark=0.0):
    """Plain paper background in a flat colour; the texture shifts every frame (stop-motion boil)."""
    r = np.random.default_rng(f)
    ox, oy = r.integers(0, 12), r.integers(0, 12)
    arr = (np.array(color, float)[None, None, :] * (1 - dark) + TEX[oy:oy + H, ox:ox + W][..., None]) * VIG
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

@functools.lru_cache(None)
def bg_img(name, blur=0.0, sat=0.9, bright=1.0):
    im = Image.open(os.path.join(ROOT, "bg", name + ".png")).convert("RGB")
    s = 1.18 * max(W / im.width, H / im.height)            # oversized for camera moves
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat)
    if bright != 1.0: im = ImageEnhance.Brightness(im).enhance(bright)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return im

def image_bg(name, f, pan=0.5, zoom=1.0, blur=0.0, sat=0.9, ox=0.0, center=None):
    """Background image with stepped pan/zoom. pan 0..1 moves left->right; center=(x,y) in oversized px."""
    im = bg_img(name, blur, sat)
    pan = round(pan * 40) / 40
    cw, ch = int(W / zoom), int(H / zoom)
    dx, dy, _ = jit(f // 2, 31, 1.2, 0)
    if center:
        x, y = center[0] - cw / 2, center[1] - ch / 2
    else:
        x = (im.width - cw) * (0.15 + 0.7 * pan + ox); y = (im.height - ch) * 0.5
    x = int(np.clip(x + dx, 0, im.width - cw)); y = int(np.clip(y + dy, 0, im.height - ch))
    crop = im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR)
    arr = np.asarray(crop).astype(float) * (0.55 + 0.45 * VIG)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

# ------------------------------------------------------------------ placing things
def jit(f, seed, px=2.5, deg=0.6):
    r = np.random.default_rng(seed * 7919 + f)
    return r.normal(0, px), r.normal(0, px), r.normal(0, deg)

def step(t, t0, t1):
    """eased 0..1 between t0 and t1; frames are 12 fps so movement reads as stop-motion steps."""
    if t <= t0: return 0.0
    if t >= t1: return 1.0
    u = (t - t0) / (t1 - t0); return 1 - (1 - u) ** 3

def safe(canvas, im, x, y):
    sx, sy, dx, dy = max(0, -x), max(0, -y), max(0, x), max(0, y)
    w = min(im.width - sx, canvas.width - dx); h = min(im.height - sy, canvas.height - dy)
    if w > 0 and h > 0:
        canvas.alpha_composite(im.crop((sx, sy, sx + w, sy + h)), (dx, dy))

def paste(canvas, im, cx, cy, rot=0.0, shadow=True, alpha=1.0, seed=None, f=None, boil=True):
    """Centre-paste a cut-out with drop shadow. With seed+f it jitters (boil) like hand-placed paper."""
    if seed is not None and f is not None and boil:
        dx, dy, dr = jit(f, seed); cx += dx; cy += dy; rot += dr
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    if shadow:
        sh = Image.new("RGBA", im.size, (5, 8, 16, 0))
        sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.55)))
        safe(canvas, sh, x + 10, y + 14)
    safe(canvas, im, x, y)

def walk_in(canvas, name, h, t, t0, t1, x_from, x_to, y, f, seed=3):
    """Stop-motion walk: stepped slide with a bob on alternate frames until it arrives."""
    k = step(t, t0, t1)
    bob = 0 if k >= 1 else (8 if f % 2 else 0)
    paste(canvas, scaled(name, h), x_from + (x_to - x_from) * k, y - bob, seed=seed, f=f)

def drop_in(canvas, name, h, t, t0, t1, x, y_to, f, seed=4):
    k = step(t, t0, t1)
    paste(canvas, scaled(name, h), x, -h + (y_to + h) * k, seed=seed, f=f)

def pivot_paste(canvas, im, pivot_src, pivot_dst, angle, f, seed=61, pad=400):
    """Rotate a big cut-out (tree, branch, arm) around a pivot point, e.g. a tree pulling its fruit away."""
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0)); big.paste(im, (pad, pad))
    px, py = pad + pivot_src[0], pad + pivot_src[1]
    rot = big.rotate(angle, resample=Image.BICUBIC, center=(px, py))
    dx, dy, _ = jit(f, seed, 1.5, 0)
    x, y = int(pivot_dst[0] - px + dx), int(pivot_dst[1] - py + dy)
    sh = Image.new("RGBA", rot.size, (5, 8, 16, 0))
    sh.putalpha(rot.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.5)))
    safe(canvas, sh, x + 12, y + 16); safe(canvas, rot, x, y)

def confetti(canvas, t, f, n=26, color=GOLD, seed=77):
    """Falling gold paper scraps (wealth, celebration)."""
    d = ImageDraw.Draw(canvas); r = np.random.default_rng(seed)
    for i in range(n):
        x0 = r.uniform(200, 1720); sp = r.uniform(60, 140); ph = r.uniform(0, 900)
        y = (ph + t * sp) % 1200 - 80; s = r.uniform(10, 22); ang = (f // 2 + i) % 4 * 0.6
        d.polygon([(x0 + s * math.cos(ang + k * 1.7), y + s * math.sin(ang + k * 1.7)) for k in range(4)], fill=color + (255,))

def water_bands(canvas, f, y0=905, cols=((30, 48, 76), (22, 36, 60)), line=(200, 205, 210)):
    d = ImageDraw.Draw(canvas)
    for i, col in enumerate(cols):
        yy = y0 + i * 55
        pts = [(-20, H + 20)] + [(x, yy + 14 * math.sin(x / 70 + f * 0.9 + i)) for x in range(-20, W + 40, 30)] + [(W + 40, H + 20)]
        d.line(pts[1:-1], fill=line + (255,), width=4); d.polygon(pts, fill=col + (255,))

def torn_poly(points, f, seed, amp=6):
    r = np.random.default_rng(seed * 100 + (f // 2) % 3); out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 9))
        for i in range(n):
            u = i / n; out.append((x0 + (x1 - x0) * u + r.normal(0, amp * .4), y0 + (y1 - y0) * u + r.normal(0, amp)))
    out.append(points[-1]); return out

def make_phone(h=430):
    """Paper smartphone with warm glow (the modern 'fruit')."""
    w, pad = int(h * 0.5), 120
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((pad - 30, pad - 30, pad + w + 30, pad + h + 30), 60, fill=(255, 240, 200, 210))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(45)))
    d = ImageDraw.Draw(im); k = h / 430
    d.rounded_rectangle((pad - 10, pad - 10, pad + w + 10, pad + h + 10), int(42 * k), fill=CREAM + (255,))
    d.rounded_rectangle((pad, pad, pad + w, pad + h), int(34 * k), fill=(16, 20, 32, 255))
    d.rounded_rectangle((pad + 12 * k, pad + 30 * k, pad + w - 12 * k, pad + h - 30 * k), int(18 * k), fill=(255, 246, 225, 255))
    for i in range(4):
        y = pad + (60 + i * 80) * k
        d.rounded_rectangle((pad + 30 * k, y, pad + w - 30 * k, y + 50 * k), int(10 * k), fill=(240, 205, 170, 255))
        d.ellipse((pad + w - 70 * k, y + 10 * k, pad + w - 40 * k, y + 40 * k), fill=BRICK + (255,))
    return im

def glow_spot(box, color=(255, 225, 160), alpha=70, blur=120):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse(box, fill=color + (alpha,))
    return lay.filter(ImageFilter.GaussianBlur(blur))

# ------------------------------------------------------------------ word-by-word labels
class Label:
    """Cream torn strip; words ink in at `times` (when the narrator says them); red_words in brick red."""
    def __init__(self, text, red_words=(), times=(0,), hide=1e9, x=W / 2, y=150, size=78):
        self.text, self.red, self.times, self.hide, self.x, self.y, self.size = text, tuple(red_words), list(times), hide, x, y, size

@functools.lru_cache(None)
def _strip(text, reds, n, seed, size):
    font = ImageFont.truetype(FONT, size)
    words = text.split(" ")
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    space = tmp.textlength(" ", font=font) * 1.1
    widths = [tmp.textlength(w, font=font, direction="rtl", language="ar") for w in words]
    padx, pady = 48, 34
    w, h = int(sum(widths) + space * (len(words) - 1) + padx * 2), int(size * 1.5 + pady * 2)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed); pts = []
    for x in np.linspace(6, w - 6, 40): pts.append((x, 8 + r.normal(0, 3.5)))
    for y in np.linspace(8, h - 8, 10): pts.append((w - 6 + r.normal(0, 3), y))
    for x in np.linspace(w - 6, 6, 40): pts.append((x, h - 8 + r.normal(0, 3.5)))
    for y in np.linspace(h - 8, 8, 10): pts.append((6 + r.normal(0, 3), y))
    d.polygon(pts, fill=CREAM + (255,))
    x = w - padx                                        # right-to-left
    for i, (wd, ww) in enumerate(zip(words, widths)):
        if i < n:
            d.text((x - ww, pady - size * 0.12), wd, font=font, fill=(BRICK if wd in reds else INK) + (255,), direction="rtl", language="ar")
        x -= ww + space
    return im

def draw_labels(canvas, labels, t, f):
    for i, L in enumerate(labels):
        if t < L.times[0] - 0.08 or t >= L.hide: continue
        n = sum(1 for tt in L.times if t >= tt)
        im = _strip(L.text, L.red, n, i + 2, L.size)
        k = int((t - (L.times[0] - 0.08)) * FPS)
        s = {0: 0.6, 1: 1.08, 2: 0.97}.get(k, 1.0)                 # pop in
        if any(0 <= (t - tt) * FPS < 1 for tt in L.times[1:]): s = 1.03   # jolt on each new word
        if s != 1.0: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        dx, dy, dr = jit(f, i + 52, 1.5, 0.4)
        paste(canvas, im, L.x + dx, L.y + dy, rot=-1.2 + dr)

# ------------------------------------------------------------------ transitions & effects
def tear_mask(u, f):
    """Jagged tear sweeping right->left (Arabic reading direction). Returns (mask of new scene, edge points)."""
    r = np.random.default_rng(500 + f)
    m = Image.new("L", (W, H), 0); xb = W + 200 - u * (W + 600)
    pts = [(xb + 160 * (y / H) + r.normal(0, 14), y) for y in range(-20, H + 40, 24)]
    ImageDraw.Draw(m).polygon([(W + 50, -20)] + pts + [(W + 50, H + 40)], fill=255)
    return m, pts

def tear(prev, cur, u, f):
    m, pts = tear_mask(u, f)
    out = prev.copy(); out.paste(cur, (0, 0), m)
    d = ImageDraw.Draw(out)
    d.line(pts, fill=CREAM + (255,), width=16)
    d.line([(x + 10, y) for x, y in pts], fill=(5, 8, 16, 255), width=4)
    return out

def drain(arr, u):
    """Colour world -> dark navy paper world (the fall). arr float HxWx3."""
    g = arr.mean(axis=2, keepdims=True)
    navy = g / 255 * np.array([48, 64, 96])[None, None, :] + np.array(NAVY)[None, None, :] * 0.55
    return arr * (1 - u) + navy * u

@functools.lru_cache(None)
def bolt_layer(seed, tip_x, tip_y):
    """Torn-paper lightning from the top edge down to (tip_x, tip_y), with glow and impact sparks."""
    r = np.random.default_rng(seed)
    x0 = tip_x + r.uniform(-120, 120); ys = np.linspace(-40, tip_y, 8)
    xs = [x0] + [tip_x + (x0 - tip_x) * (1 - i / 7) + r.uniform(-70, 70) for i in range(1, 7)] + [tip_x]
    def rib(xs, ys, w0, w1):
        L, Rr = [], []
        for i, (x, y) in enumerate(zip(xs, ys)):
            w = w0 + (w1 - w0) * i / (len(xs) - 1); L.append((x - w, y)); Rr.append((x + w, y))
        return L + Rr[::-1]
    k = int(r.integers(2, 4))
    bx = [xs[k], xs[k] + r.choice([-1, 1]) * 150, xs[k] + r.choice([-1, 1]) * 210]; by = [ys[k], ys[k] + 90, ys[k] + 170]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.polygon(rib(xs, ys, 110, 50), fill=(255, 236, 170, 200))
    gd.ellipse((tip_x - 140, tip_y - 110, tip_x + 140, tip_y + 60), fill=(255, 236, 170, 150))
    lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(lay)
    for poly in (rib(xs, ys, 46, 10), rib(bx, by, 18, 4)):
        d.polygon(poly, fill=CREAM + (255,), outline=CREAM + (255,), width=8)
        d.polygon(poly, fill=(255, 214, 92, 255))
    d.polygon(rib(xs, ys, 17, 3), fill=(255, 252, 235, 255))
    for a in np.linspace(0, math.pi, 7):
        Lz = r.uniform(40, 80)
        d.line((tip_x + math.cos(a) * 30, tip_y - math.sin(a) * 20, tip_x + math.cos(a) * (30 + Lz), tip_y - math.sin(a) * (20 + Lz * .7)), fill=(255, 226, 130, 255), width=7)
    return lay

def lightning(arr, t, t_strike, tip):
    """Apply a strike at t_strike: dark strike frame + bolt, white flash, second bolt. Returns new arr."""
    k = int(math.floor((t - t_strike) * FPS + 1e-6))
    if k in (0, 3, 4): arr = drain(arr, 1.0) * 0.7
    fl = {1: 0.6, 2: 0.2}.get(k, 0)
    if fl: arr = arr * (1 - fl) + 250 * fl
    b = {0: 1, 1: 1, 3: 2, 4: 2}.get(k)
    if b:
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        im.alpha_composite(bolt_layer(b, int(tip[0]), int(tip[1])))
        arr = np.asarray(im.convert("RGB")).astype(float)
    return arr

def glitch(img, f, band=40, every=90, amount=40):
    """Horizontal band-shift glitch for one frame (used when two worlds flicker into each other)."""
    a = np.asarray(img.convert("RGB")).copy()
    for y0 in range(0, H, every):
        a[y0:y0 + band] = np.roll(a[y0:y0 + band], int(np.random.default_rng(f + y0).integers(-amount, amount)), axis=1)
    return Image.fromarray(a).convert("RGBA")

def in_any(t, intervals):
    return any(a <= t < b for a, b in intervals)

# ------------------------------------------------------------------ render loop
class Scene:
    """t0..t1 in video seconds. draw(t, f, canvas). bg: None (draw your own) or an RGB colour for paper_bg."""
    def __init__(self, t0, t1, draw, bg=NAVY, dark=0.0, rip=True):
        self.t0, self.t1, self.draw, self.bg, self.dark, self.rip = t0, t1, draw, bg, dark, rip

RIP = 0.5

def scene_canvas(s, t, f):
    c = paper_bg(f, s.bg, s.dark) if s.bg is not None else Image.new("RGBA", (W, H), (0, 0, 0, 255))
    s.draw(t, f, c); return c

def frame(f, scenes, labels, dur, post=None, out_dir=None):
    """post(arr, t, f, scene_index) -> arr lets a part add lightning, drains, flashes, etc."""
    t = f / FPS
    idx = max(i for i, s in enumerate(scenes) if s.t0 <= t)
    s = scenes[idx]
    cur = scene_canvas(s, t, f)
    if idx > 0 and s.rip and t - s.t0 < RIP:
        cur = tear(scene_canvas(scenes[idx - 1], t, f), cur, (t - s.t0) / RIP, f)
    draw_labels(cur, labels, t, f)
    arr = np.asarray(cur.convert("RGB")).astype(float)
    if post: arr = post(arr, t, f, idx)
    if t < 0.4: arr *= t / 0.4
    if t > dur - 0.5: arr *= max(0, (dur - t) / 0.5)
    arr = arr + np.random.default_rng(1000 + f).normal(0, 7, (H, W, 1))      # film grain
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(
        os.path.join(out_dir or os.path.join(ROOT, "frames"), f"{f:05d}.png"))

def render(scenes, labels, dur, frames=None, post=None, out_dir=None):
    for f in (frames if frames is not None else range(int(round(dur * FPS)))):
        frame(f, scenes, labels, dur, post, out_dir)

def contact_sheet(times, out, out_dir=None, cols=2):
    """Downscaled grid of rendered frames at given seconds - LOOK at it before rendering everything."""
    d = out_dir or os.path.join(ROOT, "frames")
    ims = [Image.open(os.path.join(d, f"{int(round(t * FPS)):05d}.png")).resize((640, 360)) for t in times]
    rows = (len(ims) + cols - 1) // cols
    c = Image.new("RGB", (640 * cols, 360 * rows))
    for i, im in enumerate(ims): c.paste(im, ((i % cols) * 640, (i // cols) * 360))
    c.save(out)

def encode(audio, out, dur, frames_dir=None):
    """Phone-safe MP4 (~5-6 MB per 35 s). Big CRF-18 files failed to open in the mobile app."""
    import subprocess
    fd = frames_dir or os.path.join(ROOT, "frames")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(fd, "%05d.png"),
                    "-i", audio, "-r", "24", "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-preset", "veryfast",
                    "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "44100",
                    "-t", f"{dur}", "-movflags", "+faststart", out], check=True)
