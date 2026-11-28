"""3D-ish stage + psychological-horror effects for the surgeons short (1080x1920)."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
import basira_engine as E

W, H = 1080, 1920
ORANGE = (238, 122, 34)
RED = (214, 44, 30)

# ------------------------------------------------------------ depth-mapped photo backgrounds
_GY, _GX = np.mgrid[0:H, 0:W].astype(np.float32)
_NX, _NY = _GX / W, _GY / H


def _smooth(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1)
    return u * u * (3 - 2 * u)


@functools.lru_cache(None)
def depth(name):
    """0 = far, 1 = near, in output (screen) space."""
    if name in ("awake", "asleep"):
        d = 0.15 + 0.5 * np.exp(-(((_NX - .5) ** 2) / .06 + ((_NY - .42) ** 2) / .05)) + 0.75 * _smooth(.62, 1.0, _NY)
    elif name == "theatre":
        d = 0.05 + 0.95 * _smooth(0.25, 1.0, _NY) ** 1.4
    elif name == "pharmacy":
        r = np.sqrt(((_NX - .5) / .5) ** 2 + ((_NY - .45) / .55) ** 2)
        d = np.clip(r, 0, 1) ** 1.3
    else:
        d = np.full((H, W), 0.5, np.float32)
    return ndimage.gaussian_filter(d.astype(np.float32), 25)


@functools.lru_cache(None)
def bg_array(name, sat=0.95):
    im = E.bg_img(name, 0, sat)
    return np.asarray(im.convert("RGB")).astype(np.float32)


def bg3d(name, f, cx, cy, zoom, px=0.0, py=0.0, dolly=0.0):
    """Background with real parallax: near parts (depth map) shift (px,py) and grow with dolly; far parts stay."""
    a = bg_array(name)
    ih, iw = a.shape[:2]
    d = depth(name)
    jx, jy, _ = E.jit(f // 2, 31, 1.0, 0)
    z = zoom * (1 + dolly * (d - 0.5))
    sx = cx * iw + (_GX - W / 2) / z - px * d + jx
    sy = cy * ih + (_GY - H / 2) / z - py * d + jy
    sx = np.clip(sx, 0, iw - 1.001)
    sy = np.clip(sy, 0, ih - 1.001)
    out = np.empty((H, W, 3), np.float32)
    for ch in range(3):
        out[..., ch] = ndimage.map_coordinates(a[..., ch], (sy, sx), order=1, mode="nearest")
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ------------------------------------------------------------ dark stage with a perspective floor
@functools.lru_cache(None)
def stage(cam_x_q, horizon_q, lamp=1.0):
    """A dark room: back wall, wooden floor in perspective, one overhead lamp cone. Cached by quantised camera."""
    cam_x, horizon = cam_x_q * 4, horizon_q * 4
    w, h = W // 2, H // 2
    hz = horizon / 2
    vx = w / 2 - cam_x * 0.15 / 2
    im = Image.new("RGB", (w, h), (14, 12, 11))
    d = ImageDraw.Draw(im)
    # floor
    d.polygon([(0, hz), (w, hz), (w, h), (0, h)], fill=(34, 25, 19))
    for i in range(-14, 15):
        xb = w / 2 + i * 70 - cam_x * 0.9 / 2
        d.line((vx + (xb - vx) * 0.04, hz, xb, h), fill=(16, 12, 10), width=2)
    for k in range(1, 14):
        y = hz + (h - hz) * (k / 13) ** 2
        d.line((0, y, w, y), fill=(22, 16, 12), width=1)
    # skirting line
    d.line((0, hz, w, hz), fill=(48, 36, 28), width=3)
    a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    # lamp pool on the floor + cone of light
    pool = np.exp(-(((xx - w / 2) / (w * 0.36)) ** 2 + ((yy - (hz + (h - hz) * 0.42)) / ((h - hz) * 0.35)) ** 2))
    cone_w = 40 + (yy / h) * w * 0.42
    cone = np.clip(1 - np.abs(xx - w / 2) / cone_w, 0, 1) ** 1.6 * (yy < hz + (h - hz) * 0.5) * 0.55
    wall_glow = np.exp(-(((xx - w / 2) / (w * 0.5)) ** 2 + ((yy - hz * 0.7) / (hz * 0.6)) ** 2)) * 0.35
    light = lamp * (pool * 1.25 + cone + wall_glow)
    a = a * (0.35 + light[..., None] * 1.6) + light[..., None] * np.array([46, 36, 24]) * lamp
    # fog toward the horizon
    fog = np.exp(-((yy - hz) / (h * 0.06)) ** 2) * 0.5
    a = a * (1 - fog[..., None]) + np.array([30, 30, 32]) * fog[..., None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return out.filter(ImageFilter.GaussianBlur(1.2)).convert("RGBA")


def stage_bg(f, cam_x, horizon=1000, lamp=1.0):
    im = stage(int(round(cam_x / 4)), int(round(horizon / 4)), round(lamp, 1)).copy()
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    r = np.random.default_rng(f)
    ox, oy = r.integers(0, 12), r.integers(0, 12)
    arr += E.TEX[oy:oy + H, ox:ox + W][..., None] * 0.6
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def contact_shadow(c, x, y, w, h=None, alpha=170):
    h = h or w * 0.16
    lay = Image.new("RGBA", (int(w * 1.6), int(h * 4)), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse((w * 0.3, h * 1.5, w * 1.3, h * 2.5), fill=(0, 0, 0, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(h * 0.5 + 4))
    E.safe(c, lay, int(x - lay.width / 2), int(y - lay.height / 2))


# ------------------------------------------------------------ perspective tilt (yaw) of a flat card
def _coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def yaw(im, deg, pitch=0.0):
    """Turn a flat cut-out around its vertical axis (deg) so it reads as a card in 3D space."""
    if abs(deg) < 0.3 and abs(pitch) < 0.3:
        return im
    w, h = im.size
    th = math.radians(deg)
    k = math.sin(th) * 0.22
    dx = w * (1 - math.cos(th)) / 2
    p = math.sin(math.radians(pitch)) * 0.18
    pad = int(h * abs(k) + w * abs(p)) + 4
    dst = [(dx + w * p, pad - k * h / 2), (w - dx - w * p, pad + k * h / 2),
           (w - dx + w * p, pad + h - k * h / 2), (dx - w * p, pad + h + k * h / 2)]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    out = im.transform((w, h + 2 * pad), Image.PERSPECTIVE, _coeffs(dst, src), Image.BICUBIC)
    return out


# ------------------------------------------------------------ particles: dust at three depths
@functools.lru_cache(None)
def mote(r, a):
    s = int(r * 2 + 4)
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / r
    al = np.clip(1 - d, 0, 1) ** 1.6 * a
    im = np.zeros((s, s, 4), np.uint8)
    im[..., :3] = (236, 226, 204)
    im[..., 3] = (al * 255).astype(np.uint8)
    return Image.fromarray(im, "RGBA")


def dust(c, t, f, cam_x=0.0, cam_y=0.0, n=46, seed=3, warm=False):
    r = np.random.default_rng(seed)
    for i in range(n):
        layer = i % 3                              # 0 far, 1 mid, 2 near
        par = (0.25, 0.7, 1.8)[layer]
        rad = (2.2, 4.5, 16)[layer] * r.uniform(0.7, 1.3)
        al = (0.55, 0.45, 0.22)[layer]
        x0, y0 = r.uniform(0, W), r.uniform(0, H)
        vx, vy = r.uniform(-14, 14), r.uniform(-26, -6)
        x = (x0 + vx * t + 30 * math.sin(t * 0.4 + i) - cam_x * par) % (W + 80) - 40
        y = (y0 + vy * t - cam_y * par) % (H + 80) - 40
        tw = 0.65 + 0.35 * math.sin(t * 2.3 + i * 1.7)
        im = mote(round(rad, 0), round(al * tw, 1))
        E.safe(c, im, int(x - im.width / 2), int(y - im.height / 2))


@functools.lru_cache(None)
def _fog_tex():
    rng = np.random.default_rng(17)
    n = ndimage.gaussian_filter(rng.standard_normal((H // 4, W // 2)), (18, 30), mode="wrap")
    n = (n - n.min()) / (n.max() - n.min())
    return np.tile(n, (1, 2))


def fog(c, t, y0=1250, strength=0.35, speed=18, color=(170, 175, 180)):
    """Low drifting fog bank (two layers at different speeds)."""
    tex = _fog_tex()
    th, tw = tex.shape
    out = np.zeros((H, W), np.float32)
    for k, (sp, sc) in enumerate(((speed, 1.0), (speed * 2.2, 0.7))):
        off = int(t * sp / 2 + k * 200) % (tw // 2)
        layer = tex[:, off:off + W // 2]
        layer = np.asarray(Image.fromarray((layer * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        out += layer * sc
    mask = _smooth(y0 - 250, y0 + 250, _NY * H)
    al = np.clip(out * mask * strength, 0, 1)
    lay = np.zeros((H, W, 4), np.uint8)
    lay[..., :3] = color
    lay[..., 3] = (al * 255).astype(np.uint8)
    c.alpha_composite(Image.fromarray(lay, "RGBA"))


# ------------------------------------------------------------ pills (clear, coloured)
@functools.lru_cache(None)
def pill_sprite(kind, size, rot):
    s = size
    im = Image.new("RGBA", (int(s * 2.4), int(s * 2.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = im.width / 2, im.height / 2
    ink = (40, 24, 14, 255)
    if kind in ("cap", "amber"):
        L, T = s * 1.0, s * 0.42
        col = ORANGE if kind == "cap" else (246, 178, 52)
        d.rounded_rectangle((cx - L, cy - T, cx + L, cy + T), int(T), fill=(246, 238, 222, 255), outline=ink, width=max(2, int(s * 0.07)))
        d.rounded_rectangle((cx - L, cy - T, cx, cy + T), int(T), fill=col + (255,), outline=ink, width=max(2, int(s * 0.07)))
        d.rectangle((cx - T * 0.6, cy - T + 2, cx, cy + T - 2), fill=col + (255,))
        d.line((cx, cy - T, cx, cy + T), fill=ink, width=max(2, int(s * 0.06)))
        d.line((cx - L * 0.7, cy - T * 0.45, cx + L * 0.7, cy - T * 0.45), fill=(255, 255, 250, 200), width=max(2, int(s * 0.09)))
    else:
        R = s * 0.55
        d.ellipse((cx - R, cy - R * 0.92, cx + R, cy + R * 0.92), fill=(250, 246, 236, 255), outline=ink, width=max(2, int(s * 0.07)))
        d.line((cx - R * 0.6, cy, cx + R * 0.6, cy), fill=(150, 130, 110, 255), width=max(2, int(s * 0.06)))
        d.arc((cx - R * 0.7, cy - R * 0.7, cx + R * 0.3, cy + R * 0.3), 190, 260, fill=(255, 255, 255, 220), width=max(2, int(s * 0.08)))
    return im.rotate(rot, resample=Image.BICUBIC)


@functools.lru_cache(None)
def _heap_layout(w, n=80, seed=5):
    r = np.random.default_rng(seed)
    pts = []
    hm = w * 0.55
    for i in range(n):
        u = r.uniform(-1, 1)
        lim = math.sqrt(max(0, 1 - u * u))
        v = r.uniform(0, 1) ** 0.8 * lim
        kind = r.choice(["cap", "cap", "amber", "tab", "tab"])
        pts.append((u * w / 2, -v * hm, kind, int(r.uniform(0, 180)), v))
    fill_rank = np.argsort([p[4] for p in pts])          # bottom pills arrive first
    rank = np.empty(n, int); rank[fill_rank] = np.arange(n)
    return pts, rank


@functools.lru_cache(None)
def heap(w, level):
    """Pile of colourful pills, width w px, filled to level/20."""
    pts, rank = _heap_layout(w)
    n_show = int(len(pts) * level / 20)
    size = max(10, int(w / 8))
    im = Image.new("RGBA", (int(w * 1.5), int(w * 1.2)), (0, 0, 0, 0))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    base_x, base_y = im.width / 2, im.height - size * 1.4
    if n_show:
        top = max(-p[1] for i, p in enumerate(pts) if rank[i] < n_show)
        gd.ellipse((base_x - w * 0.6, base_y - top - w * 0.15, base_x + w * 0.6, base_y + w * 0.12), fill=(255, 150, 60, 150))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(w * 0.12)))
    order = sorted(range(len(pts)), key=lambda i: -pts[i][4])
    for i in order:
        if rank[i] >= n_show:
            continue
        x, y, kind, rot, _ = pts[i]
        sp = pill_sprite(kind, size, rot)
        E.safe(im, sp, int(base_x + x - sp.width / 2), int(base_y + y - sp.height / 2))
    return im


def falling_pills(c, t, t0, t1, target, w, f, n=26, seed=8):
    """Pills pouring from above into `target` between t0 and t1."""
    if not (t0 <= t < t1 + 0.4):
        return
    r = np.random.default_rng(seed)
    size = max(10, int(w / 8))
    for i in range(n):
        ts = t0 + (t1 - t0) * i / n
        u = t - ts
        if u < 0 or u > 0.55:
            continue
        x = target[0] + r.uniform(-w * 0.35, w * 0.35)
        y0 = target[1] - 1400
        y = y0 + (target[1] - y0) * min(1, (u / 0.55) ** 2)
        sp = pill_sprite(r.choice(["cap", "amber", "tab"]), size, int((r.uniform(0, 180) + u * 700) % 360))
        E.safe(c, sp, int(x - sp.width / 2), int(y - sp.height / 2))


# ------------------------------------------------------------ horror grade & glitches
_R2 = (((_GX - W / 2) / (W / 2)) ** 2 + ((_GY - H / 2) / (H / 2)) ** 2).astype(np.float32)


def horror_grade(arr, t, f, vig=0.5, flicker=0.10, sat=0.45, cold=1.0):
    """Desaturate the engraving world (but keep vivid reds/oranges), crush blacks, cold shadows,
    heavy breathing vignette, gas-lamp flicker."""
    mx, mn = arr.max(2), arr.min(2)
    chroma = mx - mn
    lum = arr.mean(2, keepdims=True)
    keep = np.clip((chroma - 70) / 70, 0, 1)[..., None]
    des = lum + (arr - lum) * sat
    arr = des * (1 - keep) + arr * keep
    arr = 255 * (np.clip(arr, 0, 255) / 255) ** 1.25                      # crush
    sh = (1 - lum / 255) ** 2
    arr = arr + sh * np.array([-8, 1, 9]) * cold
    v = 1 - vig * np.clip(_R2, 0, 1.6) ** 1.1
    arr = arr * np.clip(v, 0.05, 1)[..., None]
    r = np.random.default_rng(f * 3 + 1)
    b = 1 - flicker * r.random()
    if r.random() < 0.025:
        b *= 0.55
    return arr * b


def rgb_split(arr, px=10):
    out = arr.copy()
    out[..., 0] = np.roll(arr[..., 0], px, axis=1)
    out[..., 2] = np.roll(arr[..., 2], -px, axis=1)
    return out


def scratches(arr, f):
    r = np.random.default_rng(f * 11 + 5)
    for _ in range(r.integers(0, 3)):
        x = int(r.uniform(0, W))
        v = r.choice([-40, 50])
        arr[:, x:x + 2] += v
    for _ in range(r.integers(4, 14)):
        x, y = int(r.uniform(0, W - 6)), int(r.uniform(0, H - 6))
        arr[y:y + 4, x:x + 4] -= 70
    return arr


@functools.lru_cache(None)
def eyes_flash():
    """Subliminal frame: the patient's terrified eyes, extreme close-up, red-cast, full screen."""
    im = Image.open("proj/bg/awake.png").convert("RGB")
    w, h = im.size
    cw = int(w * 0.30); ch = int(cw * H / W)
    x0 = (w - cw) // 2; y0 = max(0, int(h * 0.33) - ch // 2)
    crop = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
    a = np.asarray(crop).astype(np.float32)
    lum = a.mean(2, keepdims=True)
    return 255 * (lum / 255) ** 1.6 * np.array([1.0, 0.32, 0.26])
