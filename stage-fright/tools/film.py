"""film.py - «رهبة» : vertical 3D paper short (28 s, 12 fps stop-motion).
Usage: python3 tools/film.py START END   (frame range)"""
import sys, os, math, functools
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from scipy import ndimage
import engine as E
from engine import W, H, FPS, paste, scaled, step, smooth, lin, jit

DUR = 33.0
SRCW = 756                                    # all backgrounds are 756x1344

# ------------------------------------------------------------------ world helpers
class World:
    """A background at `scale` x cover size; things are pasted in source-pixel coords, then a camera crops it."""
    def __init__(self, name, scale=1.5, **kw):
        self.base = E.bg_img(name, scale=scale, **kw)
        self.k = self.base.width / SRCW
        self.im = self.base.copy().convert("RGBA")
    def put(self, im_name, h_src, x_src, feet_src, f, seed, flip=False, blur=0, alpha=1.0):
        im = scaled(im_name, int(h_src * self.k))
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if blur: im = blurred(im_name, int(h_src * self.k), blur, flip)
        paste(self.im, im, x_src * self.k, feet_src * self.k, anchor="b", seed=seed, f=f, alpha=alpha,
              sh_off=(int(10 * self.k), int(8 * self.k)))
    def shot(self, f, zoom, fx, fy, sx=0, sy=0):
        """Returns (frame, mapper) - mapper(x_src, y_src) -> screen px."""
        im = self.im
        z = round(zoom * 120) / 120
        base = min(im.width / W, im.height / H)
        cw, ch = W * base / z, H * base / z
        dx, dy, _ = jit(f // 2, 31, 1.0, 0)
        x = float(np.clip(fx * im.width - cw * fx + sx + dx, 0, im.width - cw))
        y = float(np.clip(fy * im.height - ch * fy + sy + dy, 0, im.height - ch))
        fr = im.transform((W, H), Image.EXTENT, (x, y, x + cw, y + ch), Image.BICUBIC)
        return fr, (lambda xs, ys: ((xs * self.k - x) / cw * W, (ys * self.k - y) / ch * H, W / cw))

@functools.lru_cache(None)
def blurred(name, h, r, flip=False):
    im = scaled(name, h)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    pad = Image.new("RGBA", (im.width + 4 * r, im.height + 4 * r), (0, 0, 0, 0)); pad.paste(im, (2 * r, 2 * r))
    return pad.filter(ImageFilter.GaussianBlur(r))

@functools.lru_cache(None)
def sized(name, h, flip=False):
    im = scaled(name, h)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im

def navy_paper():
    return Image.new("RGBA", (W, H), E.NAVY + (255,))

def darken(img, amt, color=(10, 16, 30)):
    if amt <= 0: return img
    lay = Image.new("RGBA", img.size, color + (int(255 * amt),))
    out = img.copy(); out.alpha_composite(lay); return out

EYES = E.pieces("eyes")
@functools.lru_cache(None)
def eye(i, h, blink=False):
    im = EYES[i]; s = h / im.height
    im = im.resize((max(1, int(im.width * s)), max(1, int(h))), Image.LANCZOS)
    if blink:
        im = im.resize((im.width, max(4, int(im.height * 0.16))), Image.LANCZOS)
    return im

def blinking(i, f):
    return (f + i * 17) % 41 in (0,)

# ------------------------------------------------------------------ 1. city (0 - 3.0)
@functools.lru_cache(None)
def city_layers():
    w = World("city", scale=1.3)
    a = np.asarray(w.base).astype(float)
    lum = a.mean(axis=2)
    yy = np.arange(a.shape[0])[:, None] / w.k
    roof = (lum < 105) & (yy > 600)
    roof = ndimage.binary_closing(roof, iterations=3)
    roof = ndimage.binary_fill_holes(roof)
    lab, n = ndimage.label(roof)
    sizes = ndimage.sum(roof, lab, range(1, n + 1))
    roof = np.isin(lab, np.where(sizes > 20000)[0] + 1)
    # everything below the roofline is roof too (no gaps at the bottom)
    top = np.argmax(roof, axis=0)
    rows = np.arange(roof.shape[0])[:, None]
    roof |= (rows >= top[None, :]) & roof.any(axis=0)[None, :]
    m = Image.fromarray((ndimage.gaussian_filter(roof.astype(float), 1.2) * 255).astype(np.uint8))
    roofs = w.base.convert("RGBA"); roofs.putalpha(m)
    return w.base.convert("RGBA"), roofs, w.k

def crop_layer(im, f, zoom, fx, fy, sx=0, sy=0):
    z = round(zoom * 120) / 120
    base = min(im.width / W, im.height / H)
    cw, ch = W * base / z, H * base / z
    dx, dy, _ = jit(f // 2, 31, 1.0, 0)
    x = float(np.clip(fx * im.width - cw * fx + sx + dx, -40, im.width - cw + 40))
    y = float(np.clip(fy * im.height - ch * fy + sy + dy, -40, im.height - ch + 40))
    return im.transform((W, H), Image.EXTENT, (x, y, x + cw, y + ch), Image.BICUBIC)

def city(t, f):
    sky, roofs, k = city_layers()
    u = lin(t, 0, 3.2)
    c = crop_layer(sky, f, 1.02 + 0.03 * u, 0.5, 0.5, sx=-30 * u)
    r = crop_layer(roofs, f + 1, 1.03 + 0.16 * u, 0.5, 1.0, sx=-120 * u)
    c.alpha_composite(r)
    E.light_dust(c, t, f, n=22, seed=4, box=(0, 600, W, 1500), color=(255, 214, 170))
    # foreground: he walks home, right -> left, fastest layer
    x = 1250 - 760 * lin(t, 0, 3.2)
    bob = 10 if f % 2 else 0
    im = sized("walk", 1350)
    paste(c, im, x, 1990 - bob, anchor="b", seed=3, f=f)
    return c

# ------------------------------------------------------------------ 2. hallway (3.0 - 7.5)
def hallway(t, f):
    t0 = 3.0
    w = World("hallway", scale=1.5)
    u = smooth(t, t0, 7.6)
    fr, _ = w.shot(f, 1.03 + 0.45 * u, 378 / SRCW, 715 / 1344)
    # he walks down the corridor: away from camera, getting smaller (perspective)
    k = step(t, t0 + 0.2, 7.5) * 0.6 + lin(t, t0 + 0.2, 7.5) * 0.4
    hgt = 1450 * (1 - k) + 430 * k
    x = 300 * (1 - k) + 590 * k
    feet = 2010 * (1 - k) + 1215 * k
    bob = int(hgt * 0.007) if f % 2 else 0
    im = sized("walk", int(hgt), True)
    paste(fr, im, x, feet - bob, anchor="b", seed=5, f=f, sh_off=(14, 8), sh_a=0.4)
    return fr

# ------------------------------------------------------------------ 3. the door (7.5 - 12.0)
DOOR = dict(x0=410, x1=590, top=512, bottom=928)        # door cut-out placed over the open arch (src px)

def door_scene(t, f):
    w = World("hall_end", scale=1.6)
    k = w.k
    ang = 88 * smooth(t, 9.6, 10.6)
    ang = round(ang / 6) * 6                               # stepped stop-motion swing
    open_u = ang / 88
    # light behind the door
    d = ImageDraw.Draw(w.im)
    d.rectangle((425 * k, 520 * k, 575 * k, 928 * k), fill=(int(20 + 235 * open_u), int(28 + 220 * open_u), int(38 + 175 * open_u), 255))
    if open_u > 0:
        g = Image.new("RGBA", w.im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((340 * k, 520 * k, 660 * k, 1000 * k), fill=(255, 236, 196, int(200 * open_u)))
        w.im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60 * k / 2)))
    # the paper door, swinging open in 3D on its left hinge
    dh = int((DOOR["bottom"] - DOOR["top"]) * k)
    door = sized("door", dh)
    sw, yoff = E.swing(door, ang, "left", persp=0.30)
    dx, dy, _ = jit(f, 71, 1.5, 0)
    x = int(500 * k - door.width / 2 + dx); y = int(DOOR["top"] * k + yoff + dy)
    sh = Image.new("RGBA", sw.size, (5, 8, 16, 0))
    sh.putalpha(sw.getchannel("A").filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.45)))
    E.safe(w.im, sh, x + 10, y + 8); E.safe(w.im, sw, x, y)
    # he waits on a chair, knee bouncing (anxiety)
    bounce = 6 if (f % 3 == 0 and t < 9.8) else 0
    w.put("sit_chair", 500, 205, 1165 - bounce / k, f, seed=8)
    # camera: slow creep, then rushes through the door into the light
    z = 1.04 + 0.08 * lin(t, 7.5, 10.6) + 3.2 * (lin(t, 10.6, 12.0) ** 2.2)
    fr, _ = w.shot(f, z, 500 / SRCW, 740 / 1344)
    return fr

# ------------------------------------------------------------------ 4. lecture hall - the eyes (12.0 - 17.0)
EYE_POS = [(380, 610, 120), (190, 700, 150), (560, 690, 150), (300, 790, 175), (470, 800, 180), (130, 860, 200),
           (630, 870, 205), (390, 520, 105), (240, 590, 120), (530, 575, 120), (380, 900, 230), (90, 640, 135)]
EYE_T = [12.7 + i * 0.24 for i in range(12)]
BEATS = []
_tb = 12.6
while _tb < 17.0:
    BEATS.append(_tb); _tb += max(0.32, 0.75 - (_tb - 12.6) * 0.11)

def beat_pulse(t):
    for b in BEATS:
        k = int((t - b) * FPS + 1e-6)
        if k == 0: return 1.035
        if k == 1: return 1.012
    return 1.0

def lecture(t, f):
    w = World("lecture", scale=1.4)
    u = smooth(t, 12.0, 17.2)
    zoom = 1.05 + 0.22 * u
    zoom *= beat_pulse(t)
    w.im = darken(w.im, 0.12 + 0.42 * lin(t, 12.6, 16.0))
    fr, mp = w.shot(f, zoom, 0.5, 0.52)
    # eyes in the seats, each at its own depth (nearer = bigger, more parallax)
    look = smooth(t, 15.6, 16.3)
    for i in sorted(range(12), key=lambda i: EYE_POS[i][2]):
        if t < EYE_T[i]: continue
        xs, ys, hs = EYE_POS[i]
        sx, sy, sc = mp(xs, ys)
        depth = hs / 150
        sx = W / 2 + (sx - W / 2) * (1 + (depth - 1) * 0.35 * u)
        n = int((t - EYE_T[i]) * FPS)
        pop = {0: 0.55, 1: 1.15, 2: 0.95}.get(n, 1.0)
        hh = int(hs * 1.7 * pop * (1 + 0.12 * u * depth))
        im = eye(i, hh, blinking(i, f))
        paste(fr, im, sx - 18 * look * depth, sy, seed=90 + i, f=f, sh_a=0.6)
    # foreground: podium + him, shrinking away from the audience (fast parallax)
    pz = 1 + (zoom - 1.05) * 2.2
    paste(fr, sized("crouch", int(640 * pz)), W / 2 + (250 - W / 2) * pz, 1640 + 260 * pz, anchor="b", seed=12, f=f)
    paste(fr, sized("podium", int(720 * pz)), W / 2 + (870 - W / 2) * pz, 1600 + 330 * pz, anchor="b", seed=13, f=f)
    return fr

# ------------------------------------------------------------------ 5. close-up, eyes orbit (17.0 - 19.6)
def orbit(t, f):
    c = navy_paper()
    c.alpha_composite(E.glow_spot((140, 500, 940, 1500), (90, 110, 150), 90, 160))
    u = lin(t, 17.0, 19.6)
    push = 1.0 + 0.16 * smooth(t, 17.0, 19.6)
    push *= beat_pulse(t + 0.0) if t < 18.5 else 1.0
    ang0 = round(u * 1.4 * 2 * math.pi * 24) / 24
    R = (520 - 140 * u) * push
    items = []
    for i in range(12):
        a = ang0 + i * 2 * math.pi / 12
        z = math.sin(a)
        x = W / 2 + R * math.cos(a)
        y = 900 + (420 - 40 * u) * z + 40 * math.sin(a * 2 + 1)
        items.append((z, i, x, y))
    face = sized("face_front", int(1240 * push))
    for z, i, x, y in sorted(items):
        if z >= 0: continue
        im = eye(i, int(150 * (1 + 0.35 * z) * push), blinking(i, f))
        paste(c, ImageEnhance.Brightness(im).enhance(0.55 + 0.3 * (1 + z)), x, y, seed=40 + i, f=f, sh_a=0.4)
    paste(c, face, W / 2, 1150 + 40 * (push - 1), seed=21, f=f)
    for z, i, x, y in sorted(items):
        if z < 0: continue
        im = eye(i, int(150 * (1 + 0.45 * z) * push), blinking(i, f))
        paste(c, im, x, y, seed=40 + i, f=f, sh_off=(16, 22), sh_a=0.6)
    if 19.25 <= t < 19.6 and f % 2 == 0:
        c = E.glitch(c, f)
    return c

# ------------------------------------------------------------------ 6. room at night (19.6 - 25.0)
def lamp(w, f, strength=1.0):
    fl = 1.0 - (0.25 if (f * 7) % 23 == 0 else 0)
    k = w.k
    g = Image.new("RGBA", w.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((250 * k, 280 * k, 640 * k, 640 * k), fill=(255, 205, 130, int(120 * fl * strength)))
    w.im.alpha_composite(g.filter(ImageFilter.GaussianBlur(70 * k / 2)))

def room_phone(t, f):
    w = World("room", scale=1.4)
    w.im = darken(w.im, 0.22)
    lamp(w, f)
    # phone light on his face
    w.put("phone", 600, 400, 1150, f, seed=31)
    g = Image.new("RGBA", w.im.size, (0, 0, 0, 0)); k = w.k
    if (f // 2) % 5 != 0:
        ImageDraw.Draw(g).ellipse((260 * k, 590 * k, 420 * k, 740 * k), fill=(200, 225, 255, 70))
        w.im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    fr, _ = w.shot(f, 1.06 + 0.12 * smooth(t, 19.6, 22.4), 400 / SRCW, 860 / 1344)
    return fr

def room_floor(t, f):
    w = World("room", scale=1.4)
    w.im = darken(w.im, 0.3)
    lamp(w, f, 0.8)
    # rack focus: he is sharp, then focus pulls to the bottle in front
    rf = smooth(t, 23.3, 23.9)
    rf_step = round(rf * 4) / 4
    w.put("floor", 560, 470, 1170, f, seed=33, blur=int(round(6 * rf_step)))
    zoom = 1.06 + 0.10 * smooth(t, 22.4, 25.0)
    fr, mp = w.shot(f, zoom, 470 / SRCW, 900 / 1344)
    pz = 1 + (zoom - 1.06) * 2.5
    r = int(round(10 * (1 - rf_step)))
    im = blurred("pills", int(860 * pz), r) if r else sized("pills", int(860 * pz))
    paste(fr, im, W / 2 + (200 - W / 2) * pz, 2080 + 80 * pz - (2 * r if r else 0), anchor="b", seed=35, f=f, sh_a=0.5)
    return fr

# ------------------------------------------------------------------ 7. toward the light (25.0 - 28.0)
@functools.lru_cache(None)
def soft_room():
    return E.bg_img("room", scale=1.4, blur=14, bright=0.8)

def ending(t, f):
    im = soft_room().convert("RGBA")
    c = crop_layer(im, f, 2.0 + 0.12 * lin(t, 25.0, 28.0), 470 / SRCW, 470 / 1344, sx=60)
    c.alpha_composite(E.glow_spot((560, 400, 1240, 1150), (255, 214, 150), 150, 140))
    E.light_dust(c, t, f, n=40, seed=12, box=(420, 250, W, 1400), color=(255, 232, 190))
    push = 1.0 + 0.10 * round(lin(t, 25.0, 28.0) * 10) / 10
    face = sized("face_side", int(1500 * push))
    warm = E.tint(face, (255, 214, 160), 0.16)
    paste(c, warm, 420 - 40 * (push - 1) * 10, 1260, seed=51, f=f)
    return c

# ------------------------------------------------------------------ 8. pull back: it was a photo on a stack of papers (27.2 - 29.4)
WIN = (212, 397, 551, 743)                     # the square window inside the papers cut-out
WC = ((WIN[0] + WIN[2]) / 2, (WIN[1] + WIN[3]) / 2)

@functools.lru_cache(None)
def papers_holed():
    im = E.load("papers").copy()
    a = np.asarray(im).copy(); a[WIN[1]:WIN[3], WIN[0]:WIN[2], 3] = 0
    im = Image.fromarray(a, "RGBA"); d = ImageDraw.Draw(im)
    d.line((WIN[0], WIN[1], WIN[2], WIN[1]), fill=(120, 110, 96, 255), width=4)   # cut edge catches shadow
    d.line((WIN[0], WIN[1], WIN[0], WIN[3]), fill=(120, 110, 96, 255), width=4)
    d.line((WIN[0], WIN[3], WIN[2], WIN[3]), fill=(255, 252, 244, 255), width=3)
    return im

def pullback(t, f):
    u = smooth(t, 27.25, 29.2)
    u = round(u * 24) / 24
    g0, g1 = 1930 / (WIN[3] - WIN[1]), 1480 / 1049
    g = math.exp(math.log(g0) * (1 - u) + math.log(g1) * u)
    dx, dy, dr = jit(f, 61, 2.0, 0)
    cx, cy = W / 2 + dx, H / 2 - 30 * u + dy
    c = navy_paper()
    c.alpha_composite(E.glow_spot((100, 300, 980, 1700), (70, 90, 130), 110, 180))
    # window content: the live close-up, at a scale that matches full screen when u = 0
    side = g * (WIN[3] - WIN[1])
    sc = side / H
    end = ending(t, f)
    inner = end.resize((max(1, int(W * sc)), max(1, int(H * sc))), Image.BILINEAR)
    m = np.ones((inner.height, inner.width)); fe = max(2, int(inner.width * 0.12))
    ramp = np.linspace(0, 1, fe) ** 1.5; m[:, :fe] *= ramp; m[:, -fe:] *= ramp[::-1]
    inner.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    sq = int(side) + 2
    back = end.crop((0, (H - W) // 2, W, (H + W) // 2)).resize((96, 96), Image.BILINEAR) \
        .filter(ImageFilter.GaussianBlur(10)).resize((sq, sq), Image.BILINEAR)
    E.safe(c, back, int(cx - side / 2), int(cy - side / 2))
    E.safe(c, inner, int(cx - inner.width / 2), int(cy - inner.height / 2))
    # the stack, sampled straight to screen (cheap at any scale)
    pim = papers_holed()
    box = (WC[0] - cx / g, WC[1] - cy / g, WC[0] + (W - cx) / g, WC[1] + (H - cy) / g)
    lay = pim.transform((W, H), Image.EXTENT, box, Image.BICUBIC)
    if u > 0.3:
        sh = Image.new("RGBA", (W, H), (5, 8, 16, 0))
        sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.6 * (u - 0.3) / 0.7)))
        E.safe(c, sh, 16, 22)
    c.alpha_composite(lay)
    return c

# ------------------------------------------------------------------ 9. a new day (29.4 - 33.0)
def day(t, f):
    w = World("day_room", scale=1.4)
    k = w.k
    g = Image.new("RGBA", w.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((-60 * k, 200 * k, 420 * k, 900 * k), fill=(255, 240, 205, 120))
    w.im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60 * k / 2)))
    kk = step(t, 29.6, 32.6) * 0.5 + lin(t, 29.6, 32.6) * 0.5
    hgt = 830 * (1 - kk) + 440 * kk
    x = 610 * (1 - kk) + 360 * kk
    feet = 1300 * (1 - kk) + 915 * kk
    bob = 10 / k if (f % 2 and kk < 1) else 0
    w.put("walk", hgt, x, feet - bob, f, seed=71)
    fr, _ = w.shot(f, 1.04 + 0.10 * smooth(t, 29.4, 33.0), 330 / SRCW, 760 / 1344)
    E.light_dust(fr, t, f, n=34, seed=21, box=(0, 300, 640, 1300), color=(255, 246, 220))
    return fr

def loop_back(t, f):
    return city(0.0, f)

SCENES = [E.Scene(0.0, city, rip=False), E.Scene(3.0, hallway), E.Scene(7.5, door_scene),
          E.Scene(12.0, lecture, rip=False), E.Scene(17.0, orbit), E.Scene(19.6, room_phone),
          E.Scene(22.4, room_floor), E.Scene(25.0, ending), E.Scene(27.25, pullback, rip=False),
          E.Scene(29.4, day), E.Scene(32.5, loop_back)]

def post(arr, t, f, idx):
    if 11.2 <= t < 12.0:                                   # through the door: white-out
        u = lin(t, 11.2, 11.95); arr = arr * (1 - u) + np.array([250, 244, 232]) * u
    if 12.0 <= t < 12.5:
        u = 1 - lin(t, 12.0, 12.5); arr = arr * (1 - u) + np.array([250, 244, 232]) * u
    return arr

if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fr in range(a, min(b, int(DUR * FPS))):
        E.frame(fr, SCENES, post)
