"""engine.py - vertical (1080x1920) torn-paper stop-motion engine with 2.5D camera helpers.
Based on the basira paper engine: 12 fps boil, paper grain, vignette, right->left tear transitions."""
import os, math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from scipy import ndimage

W, H, FPS = 1080, 1920, 12
NAVY = (24, 34, 54)
CREAM = (244, 236, 220)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUT = os.path.join(ROOT, "build", "cut")
FRAMES = os.path.join(ROOT, "build", "frames")
SRC = os.path.join(ROOT, "src")
for d in (CUT, FRAMES):
    os.makedirs(d, exist_ok=True)

# ------------------------------------------------------------------ cut-outs
def cutout(name, src, border=8, seed=7, min_hole=2500):
    rng = np.random.default_rng(seed)
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    white = (a.min(axis=2) > 232) & ((a.max(axis=2) - a.min(axis=2)) < 26)
    lab, _ = ndimage.label(white)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    wsz = ndimage.sum(white, lab, range(1, lab.max() + 1))
    big_holes = set(np.where(wsz > min_hole)[0] + 1) - edge
    bg = np.isin(lab, list(edge | big_holes))
    fg = ndimage.binary_opening(~bg, iterations=1)
    lab2, n2 = ndimage.label(fg)
    if n2:
        sizes = ndimage.sum(fg, lab2, range(1, n2 + 1))
        fg = np.isin(lab2, np.where(sizes > 400)[0] + 1)
    fg = ndimage.binary_fill_holes(ndimage.binary_closing(fg, iterations=6)) & ~ndimage.binary_erosion(bg, iterations=8)
    dist = ndimage.distance_transform_edt(~fg)
    n1 = ndimage.gaussian_filter(rng.standard_normal(fg.shape), 6); n1 /= np.abs(n1).max() + 1e-6
    n2_ = ndimage.gaussian_filter(rng.standard_normal(fg.shape), 1.2); n2_ /= np.abs(n2_).max() + 1e-6
    paper = ndimage.binary_fill_holes(dist <= border + 5 * n1 + 2 * n2_)
    paper &= ~ndimage.binary_erosion(bg, iterations=border + 6)
    rgba = np.zeros(fg.shape + (4,), np.uint8)
    rgba[paper, :3] = CREAM; rgba[paper, 3] = 255
    rgba[fg, :3] = np.asarray(im)[fg]; rgba[fg, 3] = 255
    ys, xs = np.where(paper)
    y0, y1 = max(ys.min() - 30, 0), ys.max() + 30
    x0, x1 = max(xs.min() - 30, 0), xs.max() + 30
    Image.fromarray(rgba[y0:y1, x0:x1], "RGBA").save(os.path.join(CUT, name + ".png"))

@functools.lru_cache(None)
def load(name):
    return Image.open(os.path.join(CUT, name + ".png")).convert("RGBA")

@functools.lru_cache(None)
def scaled(name, h):
    im = load(name); s = h / im.height
    return im.resize((max(1, int(im.width * s)), int(h)), Image.LANCZOS)

@functools.lru_cache(None)
def pieces(name, min_px=5000):
    a = np.asarray(load(name)); m = a[..., 3] > 0
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    out = []
    for k in [i + 1 for i in range(n) if sizes[i] > min_px]:
        ys, xs = np.where(lab == k)
        sub = a.copy(); sub[lab != k, 3] = 0
        out.append((round(ys.mean() / 150), xs.mean(),
                    Image.fromarray(sub, "RGBA").crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))))
    return [im for _, _, im in sorted(out, key=lambda p: (p[0], p[1]))]

@functools.lru_cache(None)
def piece_h(name, i, h):
    im = pieces(name)[i]; s = h / im.height
    return im.resize((max(1, int(im.width * s)), max(1, int(h))), Image.LANCZOS)

# ------------------------------------------------------------------ textures
_rng = np.random.default_rng(3)
def _texture():
    h, w = H + 40, W + 40
    low = ndimage.gaussian_filter(_rng.standard_normal((h, w)), 40); low /= np.abs(low).max()
    mid = ndimage.gaussian_filter(_rng.standard_normal((h, w)), 3); mid /= np.abs(mid).max()
    fib = np.zeros((h, w))
    for _ in range(1100):
        x, y = _rng.integers(0, w), _rng.integers(0, h)
        L = _rng.integers(10, 40); ang = _rng.uniform(0, math.pi)
        for t in range(L):
            xx, yy = int(x + t * math.cos(ang)), int(y + t * math.sin(ang))
            if 0 <= xx < w and 0 <= yy < h: fib[yy, xx] = 1
    return low * 8 + mid * 4 + ndimage.gaussian_filter(fib, 0.7) * 10
TEX = _texture()
_yy, _xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.34 * (((_xx - W / 2) / (W / 2)) ** 2 * 0.8 + ((_yy - H / 2) / (H / 2)) ** 2) ** 1.2)[..., None]

def grain(arr, f):
    r = np.random.default_rng(f)
    ox, oy = r.integers(0, 30), r.integers(0, 30)
    return arr + TEX[oy:oy + H, ox:ox + W][..., None] * 0.7

# ------------------------------------------------------------------ 2.5D camera
@functools.lru_cache(None)
def bg_img(name, sat=0.95, scale=1.0, blur=0.0, bright=1.0):
    """Background scaled to cover the frame (x scale for dolly headroom), sharpened after upscaling."""
    im = Image.open(os.path.join(SRC, name + ".jpg")).convert("RGB")
    s = scale * max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(2, 60, 2))
    if sat != 1: im = ImageEnhance.Color(im).enhance(sat)
    if bright != 1: im = ImageEnhance.Brightness(im).enhance(bright)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return im

def cam(name, f, zoom=1.0, fx=0.5, fy=0.5, sx=0.0, sy=0.0, **kw):
    """Camera crop: zoom toward focus point (fx,fy as 0..1 of image), shift sx,sy in px. Stepped + jitter."""
    im = bg_img(name, **kw)
    zoom = round(zoom * 120) / 120                      # stepped, stop-motion dolly
    base = min(im.width / W, im.height / H)             # frame fits inside the image at zoom 1
    cw, ch = W * base / zoom, H * base / zoom
    dx, dy, _ = jit(f // 2, 31, 1.2, 0)
    x = fx * im.width - cw * fx + sx + dx
    y = fy * im.height - ch * fy + sy + dy
    x = float(np.clip(x, 0, im.width - cw)); y = float(np.clip(y, 0, im.height - ch))
    return im.transform((W, H), Image.EXTENT, (x, y, x + cw, y + ch), Image.BILINEAR).convert("RGBA")

def jit(f, seed, px=2.5, deg=0.6):
    r = np.random.default_rng(seed * 7919 + f)
    return r.normal(0, px), r.normal(0, px), r.normal(0, deg)

def step(t, t0, t1):
    if t <= t0: return 0.0
    if t >= t1: return 1.0
    u = (t - t0) / (t1 - t0); return 1 - (1 - u) ** 3

def lin(t, t0, t1):
    return float(np.clip((t - t0) / (t1 - t0), 0, 1))

def smooth(t, t0, t1):
    u = lin(t, t0, t1); return u * u * (3 - 2 * u)

def safe(canvas, im, x, y):
    sx, sy, dx, dy = max(0, -x), max(0, -y), max(0, x), max(0, y)
    w = min(im.width - sx, canvas.width - dx); h = min(im.height - sy, canvas.height - dy)
    if w > 0 and h > 0:
        canvas.alpha_composite(im.crop((sx, sy, sx + w, sy + h)), (dx, dy))

def paste(canvas, im, cx, cy, rot=0.0, shadow=True, alpha=1.0, seed=None, f=None, sh_off=(12, 16), sh_a=0.55, anchor="c"):
    """Paste a cut-out; anchor 'c' centre or 'b' bottom-centre (feet). Boils with seed+f."""
    if seed is not None and f is not None:
        dx, dy, dr = jit(f, seed); cx += dx; cy += dy; rot += dr
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x = int(cx - im.width / 2)
    y = int(cy - im.height / 2) if anchor == "c" else int(cy - im.height)
    if shadow:
        sh = Image.new("RGBA", im.size, (5, 8, 16, 0))
        sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * sh_a * alpha)))
        safe(canvas, sh, x + sh_off[0], y + sh_off[1])
    safe(canvas, im, x, y)

def tint(im, color, amt):
    """Pull a cut-out toward a light colour (lamp glow / night)."""
    a = np.asarray(im).astype(float)
    a[..., :3] = a[..., :3] * (1 - amt) + np.array(color)[None, None, :] * amt * (a[..., :3] / 255)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")

def perspective_coeffs(src, dst):
    """Coefficients for Image.transform(PERSPECTIVE) mapping output quad dst -> input quad src."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def swing(im, angle, hinge="left", persp=0.35):
    """3D door swing around a vertical hinge. angle 0 = closed, 90 = edge-on. Returns (image, x offset)."""
    w, h = im.size
    a = math.radians(angle)
    nw = max(2, int(w * math.cos(a)))
    k = persp * math.sin(a) * h * 0.5                   # free edge gets taller (comes toward camera)
    out_w, out_h = w, int(h + 2 * k)
    if hinge == "left":
        dst = [(0, k), (nw, 0), (nw, out_h), (0, out_h - k)]
    else:
        dst = [(w - nw, 0), (w, k), (w, out_h - k), (w - nw, out_h)]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    c = perspective_coeffs(src, dst)
    res = im.transform((out_w, out_h), Image.PERSPECTIVE, c, Image.BICUBIC)
    shade = 1 - 0.45 * math.sin(a)
    arr = np.asarray(res).astype(float); arr[..., :3] *= shade
    return Image.fromarray(arr.astype(np.uint8), "RGBA"), -k

def glow_spot(box, color=(255, 210, 140), alpha=90, blur=120):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse(box, fill=color + (alpha,))
    return lay.filter(ImageFilter.GaussianBlur(blur))

def light_dust(canvas, t, f, n=30, seed=9, box=(0, 0, W, H), color=(255, 236, 200), z_speed=1.0):
    """Floating paper dust at random depths - nearer specks are bigger, faster, blurrier (depth cue)."""
    r = np.random.default_rng(seed); d = ImageDraw.Draw(canvas)
    for i in range(n):
        z = r.uniform(0.3, 1.0)
        x = box[0] + (r.uniform(0, 1) * (box[2] - box[0]) + t * 18 * z * z_speed) % (box[2] - box[0])
        y = box[1] + (r.uniform(0, 1) * (box[3] - box[1]) - t * 30 * z * z_speed) % (box[3] - box[1])
        s = 2 + 5 * z; a = int(70 + 120 * z)
        if (f // 2 + i) % 7 == 0: a //= 2
        d.ellipse((x - s, y - s, x + s, y + s), fill=color + (a,))

# ------------------------------------------------------------------ transitions
def tear_mask(u, f):
    r = np.random.default_rng(500 + f)
    m = Image.new("L", (W, H), 0); xb = W + 300 - u * (W + 800)
    pts = [(xb + 380 * (y / H) + r.normal(0, 14), y) for y in range(-20, H + 40, 24)]
    ImageDraw.Draw(m).polygon([(W + 600, -20)] + pts + [(W + 600, H + 40)], fill=255)
    return m, pts

def tear(prev, cur, u, f):
    m, pts = tear_mask(u, f)
    out = prev.copy(); out.paste(cur, (0, 0), m)
    d = ImageDraw.Draw(out)
    d.line(pts, fill=CREAM + (255,), width=18)
    d.line([(x + 11, y) for x, y in pts], fill=(5, 8, 16, 255), width=5)
    return out

def glitch(img, f, band=50, every=110, amount=50):
    a = np.asarray(img.convert("RGB")).copy()
    for y0 in range(0, H, every):
        a[y0:y0 + band] = np.roll(a[y0:y0 + band], int(np.random.default_rng(f + y0).integers(-amount, amount)), axis=1)
    return Image.fromarray(a).convert("RGBA")

# ------------------------------------------------------------------ render loop
class Scene:
    def __init__(self, t0, draw, rip=True):
        self.t0, self.draw, self.rip = t0, draw, rip

RIP = 0.5

def frame(f, scenes, post=None):
    t = f / FPS
    idx = max(i for i, s in enumerate(scenes) if s.t0 <= t)
    s = scenes[idx]
    cur = s.draw(t, f)
    if idx > 0 and s.rip and t - s.t0 < RIP:
        cur = tear(scenes[idx - 1].draw(t, f), cur, (t - s.t0) / RIP, f)
    arr = np.asarray(cur.convert("RGB")).astype(float)
    if post: arr = post(arr, t, f, idx)
    arr = grain(arr, f) * (0.62 + 0.38 * VIG)
    arr = arr + np.random.default_rng(1000 + f).normal(0, 6, (H, W, 1))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(os.path.join(FRAMES, f"{f:05d}.png"))

def contact_sheet(times, out, cols=4):
    ims = [Image.open(os.path.join(FRAMES, f"{int(round(t * FPS)):05d}.png")).resize((360, 640)) for t in times]
    rows = (len(ims) + cols - 1) // cols
    c = Image.new("RGB", (360 * cols, 640 * rows), (0, 0, 0))
    for i, im in enumerate(ims): c.paste(im, ((i % cols) * 360, (i // cols) * 640))
    c.save(out)

def encode(audio, out, dur):
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%05d.png"),
                    "-i", audio, "-r", "24", "-c:v", "libx264", "-profile:v", "main", "-level", "4.0", "-preset", "veryfast",
                    "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "44100",
                    "-t", f"{dur}", "-movflags", "+faststart", out], check=True)
