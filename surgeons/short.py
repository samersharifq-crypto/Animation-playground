"""شورت: الجرّاحون الذين رفضوا التخدير — 1080x1920, 12 fps, 2.5D paper stage.

Timing comes from TIMING below. Until the narration is recorded the segment
bounds are the estimates from the script doc and word times are spread by
word length; once s0..s5 are recorded, replace SEG (and optionally WORDS)
with the real times and re-render.
"""
import sys, math, functools, re
sys.path.insert(0, ".")
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import basira_engine as E
import fx3d as FX

# ---------------------------------------------------------------- vertical setup
E.W, E.H = 1080, 1920
W, H = E.W, E.H
E.TEX = E._texture()
_yy, _xx = np.mgrid[0:H, 0:W]
E.VIG = (1 - 0.38 * (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) ** 1.2)[..., None]
E.FADE = False
E.PRE_LABEL_POST = True
E.setup("proj", "font/ReemKufi-Bold-arabic.ttf")
FPS = E.FPS

SEPIA = (40, 29, 22)          # dark engraving paper
RED = (214, 44, 30)           # pain only
ORANGE = (236, 128, 44)       # pills / present

# ---------------------------------------------------------------- timing
TEXT = {
    "s0": "تخيّل أن يشقّ الجرّاح جلدك… وأنت مستيقظ. والدواء الذي ينيمك… في يده. لكنّه… يرفض.",
    "s1": "في عام ألف وثمانمئة وستة وأربعين، في مستشفى ببوسطن… نام مريض، وأجريت له العملية، ولم يشعر بالألم. كان ذلك أول عرض ناجح للتخدير أمام الأطباء.",
    "s2": "لكنّ بعض كبار الجرّاحين… تردّدوا. كانوا يعتقدون أن الألم نافع: يقوّي المناعة، وينشّط القلب، ويسرّع الشفاء. ولم يكن عندهم… دليل على ذلك.",
    "s3": "وقبلهم، في القرن السابع عشر، كتب الطبيب الإنجليزي توماس سيدنهام: قدر معتدل من الألم… أداة تستخدمها الطبيعة… لأغراض حكيمة.",
    "s4": "ثمّ… انقلب الميزان. اليوم ينتظر من الطبيب أن يمحو كل ألم… وصار أيّ ألم خطرًا. فتدفّقت الوصفات… حتى صار أكثر من أمريكيّ بالغ من كلّ أربعة… يتناول دواءً نفسيًّا كلّ يوم.",
    "s5": "لم يكن الألم كلّه دواءً… وليس كلّه عدوًّا. فمتى آخر مرّة… تركت ألمًا صغيرًا… يقول لك شيئًا؟",
}
# (start, end) of each recording in video seconds — ESTIMATES until the voice exists
SEG = {"s0": (0.0, 7.0), "s1": (7.0, 17.0), "s2": (17.0, 30.0), "s3": (30.0, 39.0),
       "s4": (39.0, 54.0), "s5": (54.0, 65.0)}
LOGO = (65.0, 68.5)
DUR = LOGO[1]


def _spread(seg):
    """Estimated start time of every word: speaking time ∝ letters, pauses after … and punctuation."""
    t0, t1 = SEG[seg]
    words = TEXT[seg].split(" ")
    def pause(w):
        return 0.55 if "…" in w else 0.3 if w[-1] in ".،:؟" else 0.0
    weight = [len(re.sub(r"[^ء-ي]", "", w)) + 1.5 for w in words]
    lead, tail = 0.25, 0.35
    speak = (t1 - t0) - lead - tail - sum(pause(w) for w in words)
    k = speak / sum(weight)
    out, t = [], t0 + lead
    for w, wt in zip(words, weight):
        out.append((re.sub(r"[.،:؟]", "", w).replace("…", ""), t))
        t += wt * k + pause(w)
    return out

WORDS = {s: _spread(s) for s in TEXT}


def T(seg, word, n=0):
    """Start time of the n-th occurrence of `word` in recording `seg`."""
    hits = [t for w, t in WORDS[seg] if w == word or w.startswith(word)]
    return hits[n]


# ---------------------------------------------------------------- helpers
def hb(t):
    """Heartbeat pulse 0..1 (lub-dub ~ 80 bpm)."""
    u = t % 0.75
    return math.exp(-(u / 0.06) ** 2) + 0.6 * math.exp(-((u - 0.2) / 0.06) ** 2)


def sparks(c, cx, cy, R, t, f, amount=1.0, n=14, seed=5, size=1.0):
    """Red torn-paper pain shards ringing a point, pulsing with the heart."""
    if amount <= 0.01:
        return
    r = np.random.default_rng(seed)
    pad = int(R + 140 * size)
    lay = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    beat = hb(t)
    shards = []
    for i in range(n):
        a = r.uniform(0, 2 * math.pi)
        rr = R * r.uniform(0.85, 1.15) * (1 + 0.08 * beat)
        L = (r.uniform(34, 70) * (0.7 + 0.6 * beat)) * size * amount
        wd = r.uniform(7, 13) * size
        j = np.random.default_rng(seed * 31 + f // 1 + i).normal(0, 3, 4)
        x, y = pad + rr * math.cos(a), pad + rr * math.sin(a)
        ux, uy = math.cos(a), math.sin(a)
        shards.append([(x - uy * wd + j[0], y + ux * wd + j[1]), (x + ux * L, y + uy * L),
                       (x + uy * wd + j[2], y - ux * wd + j[3]), (x - ux * L * 0.25, y - uy * L * 0.25)])
    for p in shards:
        d.polygon(p, fill=RED + (int(170 * amount),))
    glow = lay.filter(ImageFilter.GaussianBlur(14 * size))
    lay2 = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(lay2)
    for p in shards:
        d2.polygon(p, fill=RED + (int(255 * amount),), outline=(255, 200, 170, int(255 * amount)))
    glow.alpha_composite(glow)
    glow.alpha_composite(lay2)
    E.safe(c, glow, int(cx - pad), int(cy - pad))


def one_spark(c, cx, cy, t, f, amount=1.0, s=1.0):
    """A single small red spark (the 'small pain' at the end)."""
    if amount <= 0:
        return
    pad = int(90 * s)
    lay = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    beat = hb(t)
    L = (26 + 10 * beat) * s
    for k in range(4):
        a = k * math.pi / 2 + 0.2 + 0.05 * ((f // 2) % 3)
        d.polygon([(pad + math.cos(a) * L, pad + math.sin(a) * L), (pad + math.cos(a + 1.3) * 6 * s, pad + math.sin(a + 1.3) * 6 * s),
                   (pad, pad), (pad + math.cos(a - 1.3) * 6 * s, pad + math.sin(a - 1.3) * 6 * s)], fill=RED + (255,))
    g = lay.filter(ImageFilter.GaussianBlur(16 * s))
    g.alpha_composite(g)
    g.alpha_composite(lay)
    g.putalpha(g.getchannel("A").point(lambda v: int(v * amount)))
    E.safe(c, g, int(cx - pad), int(cy - pad))


@functools.lru_cache(None)
def blurred(name, h, r):
    im = E.scaled(name, h)
    return im.filter(ImageFilter.GaussianBlur(r)) if r else im


@functools.lru_cache(None)
def dimmed(name, h, r, k):
    im = blurred(name, h, r).copy()
    rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(k)
    rgb.putalpha(im.getchannel("A"))
    return rgb


def put(c, name, h, x, y, f, seed, blur=0, dim=1.0, rot=0.0, alpha=1.0, shadow=True):
    im = dimmed(name, int(h), blur, round(dim, 2)) if (blur or dim != 1.0) else E.scaled(name, int(h))
    E.paste(c, im, x, y, rot=rot, seed=seed, f=f, alpha=alpha, shadow=shadow)


def cam_bg(name, f, zoom, cx, cy, blur=0.0, sat=0.95):
    """Full-frame background viewed by a camera: centre (cx, cy) in 0..1 of the oversized image, zoom ≥ 1."""
    im = E.bg_img(name, blur, sat)
    zoom = round(zoom * 60) / 60                      # stepped like stop-motion
    cw, ch = int(W / zoom), int(H / zoom)
    dx, dy, _ = E.jit(f // 2, 31, 1.2, 0)
    x = int(np.clip(cx * im.width - cw / 2 + dx, 0, im.width - cw))
    y = int(np.clip(cy * im.height - ch / 2 + dy, 0, im.height - ch))
    crop = im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR)
    arr = np.asarray(crop).astype(float) * (0.55 + 0.45 * E.VIG)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def lerp(a, b, u):
    return a + (b - a) * u


# ---------------------------------------------------------------- the scale
# geometry in the cut-out's own pixels (scale.png is 797x1017)
PIV = (398, 245)
BEAM_BOX = (115, 212)
HOOK_L, HOOK_R = (155, 280), (640, 280)
PANL_BOX, PANR_BOX = (20, 292), (495, 292)


@functools.lru_cache(None)
def scale_parts(h):
    s = h / 1017
    def sc(name):
        im = E.load(name)
        return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    beam = sc("scale_beam")
    # pad the beam so the pivot sits at the image centre (rotate about the centre)
    px, py = (PIV[0] - BEAM_BOX[0]) * s, (PIV[1] - BEAM_BOX[1]) * s
    half_w = half_h = int(max(px, beam.width - px, py, beam.height - py)) + 6
    padded = Image.new("RGBA", (half_w * 2, half_h * 2), (0, 0, 0, 0))
    padded.paste(beam, (int(half_w - px), int(half_h - py)))
    return s, sc("scale_col"), padded, sc("scale_panL"), sc("scale_panR")


def draw_scale(c, cx, top, h, angle, f, t, pills=0.0, pain=0.0, small_spark=0.0, blur=0, seed=70,
               yaw_deg=0.0, floor_shadow=True):
    """angle > 0 : right pan (pain) goes DOWN.  pills 0..1 fill the left pan with a clear, coloured heap.
    pain 0..1 red sparks in the right pan.  yaw_deg turns the whole scale like a 3D object."""
    s, col, beam, panL, panR = scale_parts(int(h))
    ox, oy = cx - PIV[0] * s, top
    jx, jy, _ = E.jit(f, seed, 1.6, 0)
    ox += jx; oy += jy
    pv = (ox + PIV[0] * s, oy + PIV[1] * s)
    a = math.radians(angle)
    def hook(p):
        dx, dy = (p[0] - PIV[0]) * s, (p[1] - PIV[1]) * s
        return pv[0] + dx * math.cos(a) - dy * math.sin(a), pv[1] + dx * math.sin(a) + dy * math.cos(a)
    if floor_shadow:
        FX.contact_shadow(c, cx + 20, oy + 975 * s, 700 * s, alpha=200)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    def shadowed(im, x, y):
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.6)))
        E.safe(lay, sh, int(x + 12), int(y + 16))
        E.safe(lay, im, int(x), int(y))
    shadowed(col, ox, oy)
    heap_info = None
    for (hk, box, pan, side) in ((HOOK_L, PANL_BOX, panL, "L"), (HOOK_R, PANR_BOX, panR, "R")):
        hx, hy = hook(hk)
        px, py = hx - (hk[0] - box[0]) * s, hy - (hk[1] - box[1]) * s
        bowl_x = px + pan.width / 2
        rim_y = py + (700 - box[1]) * s
        shadowed(pan, px, py)
        if side == "L" and pills > 0.01:
            hw = int(pan.width * 0.95)
            him = FX.heap(hw, max(1, int(round(pills * 20))))
            base = him.height - max(10, int(hw / 8)) * 1.4
            E.safe(lay, him, int(bowl_x - him.width / 2), int(rim_y + 26 * s - base))
            heap_info = (bowl_x, rim_y, hw)
        if side == "R":
            if pain > 0.01:
                sparks(lay, bowl_x, rim_y - 40 * s, 70 * s, t, f, amount=pain, n=9, seed=11, size=s * 1.2)
            if small_spark > 0.01:
                one_spark(lay, bowl_x, rim_y - 22 * s, t, f, small_spark, s=s * 1.3)
    rb = beam.rotate(-angle, resample=Image.BICUBIC)
    shadowed(rb, pv[0] - rb.width / 2, pv[1] - rb.height / 2)
    if blur:
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
    if abs(yaw_deg) > 0.3:
        bb = lay.getbbox()
        if bb:
            part = lay.crop(bb)
            pw = FX.yaw(part, yaw_deg)
            ccx, ccy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            E.safe(c, pw, int(ccx - pw.width / 2), int(ccy - pw.height / 2))
    else:
        c.alpha_composite(lay)
    return heap_info


def scale_top_for_floor(h, floor_y):
    return floor_y - 960 * h / 1017

# ---------------------------------------------------------------- small drawn props
def vapour(c, x, y, t, t0, amount=1.0, seed=9):
    """Ether vapour: soft cream wisps rising and swaying."""
    if t < t0 or amount <= 0:
        return
    u = t - t0
    lay = Image.new("RGBA", (700, 900), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = np.random.default_rng(seed)
    for i in range(9):
        ph = r.uniform(0, 3)
        k = ((u * 0.45 + ph / 3) % 1.0)
        yy = 850 - k * 800
        xx = 350 + 90 * math.sin(k * 5 + ph * 2 + u * 0.8)
        rw, rh = 70 + 120 * k, 40 + 60 * k
        al = int(95 * amount * math.sin(math.pi * k) * min(1, u / 0.8))
        d.ellipse((xx - rw, yy - rh, xx + rw, yy + rh), fill=(250, 244, 230, al))
    E.safe(c, lay.filter(ImageFilter.GaussianBlur(26)), int(x - 350), int(y - 850))


@functools.lru_cache(None)
def stamp_img(text, size=190):
    font = ImageFont.truetype(E.FONT, size)
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    w = int(d0.textlength(text, font=font)) + 120
    h = int(size * 1.45) + 60
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(4)
    pts = [(x, 10 + r.normal(0, 4)) for x in np.linspace(8, w - 8, 30)] + \
          [(w - 8 + r.normal(0, 4), y) for y in np.linspace(10, h - 10, 8)] + \
          [(x, h - 10 + r.normal(0, 4)) for x in np.linspace(w - 8, 8, 30)] + \
          [(8 + r.normal(0, 4), y) for y in np.linspace(h - 10, 10, 8)]
    d.polygon(pts, fill=E.CREAM + (255,))
    ink = (52, 34, 24, 255)
    d.rectangle((30, 28, w - 30, h - 28), outline=ink, width=9)
    d.text((w / 2, h / 2), text, font=font, fill=ink, anchor="mm", direction="rtl", language="ar")
    # worn ink: knock out speckles
    a = np.asarray(im).copy()
    m = (np.random.default_rng(8).random(a.shape[:2]) < 0.10) & (a[..., 0] < 120)
    a[m, :3] = E.CREAM
    return Image.fromarray(a, "RGBA")


@functools.lru_cache(None)
def rx_paper(seed):
    r = np.random.default_rng(seed)
    w, h = 120, 160
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(4 + r.normal(0, 2), 4), (w - 4, 4 + r.normal(0, 2)), (w - 4 + r.normal(0, 2), h - 4), (4, h - 4 + r.normal(0, 2))],
              fill=(246, 236, 214, 255), outline=(120, 96, 70, 255))
    d.text((18, 12), "Rx", fill=(70, 50, 36, 255), font=ImageFont.truetype(E.FONT.replace("arabic", "latin"), 30))
    for i in range(5):
        y = 60 + i * 18
        d.line((18, y, w - 18 - r.uniform(0, 40), y), fill=(110, 90, 70, 255), width=3)
    return im


def rx_rain(c, t, t0, f, n=26):
    if t < t0:
        return
    u = t - t0
    r = np.random.default_rng(21)
    for i in range(n):
        x0 = r.uniform(40, W - 40)
        start = r.uniform(0, 1.6)
        sp = r.uniform(520, 820)
        y = -120 + (u - start) * sp
        if y < -150 or u < start:
            continue
        if y > H + 150:
            continue
        rot = (r.uniform(-30, 30) + 25 * math.sin(u * 2 + i) + (f // 2 % 3) * 2)
        x = x0 + 40 * math.sin(u * 1.6 + i)
        E.paste(c, rx_paper(i % 6).rotate(rot, expand=True, resample=Image.BICUBIC), x, y, shadow=True)


@functools.lru_cache(None)
def quote_paper(n_words, w=960):
    """Yellowed paper with Sydenham's line, words inked one by one; key phrases in brick red."""
    words = "قدرٌ معتدلٌ من الألمِ أداةٌ تستخدمها الطبيعة لأغراضٍ حكيمة".split(" ")
    reds = {"قدرٌ", "معتدلٌ", "لأغراضٍ", "حكيمة"}
    size = 66
    font = ImageFont.truetype(E.FONT, size)
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = [words[:4], words[4:7], words[7:]]
    h = 3 * int(size * 1.6) + 90
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(12)
    pts = [(x, 10 + r.normal(0, 5)) for x in np.linspace(8, w - 8, 44)] + \
          [(w - 8 + r.normal(0, 4), y) for y in np.linspace(10, h - 10, 10)] + \
          [(x, h - 10 + r.normal(0, 5)) for x in np.linspace(w - 8, 8, 44)] + \
          [(8 + r.normal(0, 4), y) for y in np.linspace(h - 10, 10, 10)]
    d.polygon(pts, fill=(236, 214, 160, 255))
    k = 0
    space = d0.textlength(" ", font=font) * 1.1
    for li, line in enumerate(lines):
        widths = [d0.textlength(x, font=font, direction="rtl", language="ar") for x in line]
        x = w / 2 + (sum(widths) + space * (len(line) - 1)) / 2
        y = 45 + li * int(size * 1.6)
        for wd, ww in zip(line, widths):
            if k < n_words:
                col = E.BRICK if wd in reds else (52, 36, 24)
                d.text((x - ww, y), wd, font=font, fill=col + (255,), direction="rtl", language="ar")
            x -= ww + space
            k += 1
    # age stains
    a = np.asarray(im).astype(float)
    stain = E.ndimage.gaussian_filter(np.random.default_rng(3).standard_normal(a.shape[:2]), 30)
    stain = (stain - stain.min()) / (stain.max() - stain.min())
    a[..., :3] *= (0.86 + 0.14 * stain)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def strike(c, x0, y0, x1, y1, u, f, width=16):
    if u <= 0:
        return
    d = ImageDraw.Draw(c)
    xe, ye = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    pts = E.torn_poly([(x0, y0), (xe, ye)], f, 3, amp=3)
    d.line(pts, fill=E.BRICK + (255,), width=width)


def orange_figure(name, h):
    """A modern figure painted in pill-orange (the one in four)."""
    return _orange(name, int(h))


@functools.lru_cache(None)
def _orange(name, h):
    im = E.scaled(name, h)
    a = np.asarray(im).astype(float)
    lum = a[..., :3].mean(2, keepdims=True) / 255
    col = np.array(ORANGE)[None, None, :]
    out = a.copy()
    out[..., :3] = np.clip(lum * col * 1.25 + (1 - lum) * np.array([60, 24, 8]) * 0.4, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- scenes (3D stage + psychological horror)
def card_in(im, t, t0, dur=0.45, start=78):
    """A paper card swinging in around its vertical axis."""
    k = E.step(t, t0, t0 + dur)
    return FX.yaw(im, start * (1 - k))


def sc_hook(t, f, c):
    """s0: extreme close-up on the eyes; slow dolly back with real depth; the surgeon looms in the foreground."""
    t_surg, t_flask, t_ref = T("s0", "الجرّاح"), T("s0", "في"), T("s0", "يرفض")
    pull = E.step(t, 0.6, 6.6)
    zoom = lerp(2.1, 1.0, pull)
    orbit = 70 * math.sin(t * 0.55)
    c.alpha_composite(FX.bg3d("awake", f, 0.5, lerp(0.30, 0.42, pull), zoom, px=orbit, py=-30 * pull, dolly=0.45))
    sparks(c, 560 + orbit * 0.3, lerp(560, 640, pull), lerp(620, 470, pull), t, f, amount=1.0, n=22, seed=5, size=1.25)
    if t >= t_flask:
        k_out = E.step(t, t_ref + 0.1, t_ref + 0.8)
        fx = lerp(250, -280, k_out) - orbit * 1.2
        c.alpha_composite(E.glow_spot((fx - 230, 1180, fx + 230, 1560), (255, 200, 130), int(110 * (1 - k_out)), 60))
        im = card_in(E.scaled("ether", 400), t, t_flask, 0.35, 60)
        E.paste(c, im, fx, 1380, rot=-22 * k_out, seed=41, f=f)
    if t >= t_surg - 0.3:
        k = E.step(t, t_surg - 0.3, t_surg + 1.1)
        x = lerp(1500, 840, k) - orbit * 1.8
        sim = FX.yaw(E.scaled("surgeon", 1320), -14 + orbit * 0.06)
        E.paste(c, sim, x, 1440, seed=3, f=f)
        # scalpel glint
        g = t - (t_surg + 1.2)
        if 0 <= g < 0.35:
            one_spark_white(c, x - 205, 1560, 1 - g / 0.35)
    FX.dust(c, t, f, orbit, 0, n=30)


def one_spark_white(c, x, y, a):
    lay = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    L = 110 * a
    d.polygon([(130 - L, 130), (130, 124), (130 + L, 130), (130, 136)], fill=(255, 255, 250, 255))
    d.polygon([(130, 130 - L * 0.7), (124, 130), (130, 130 + L * 0.7), (136, 130)], fill=(255, 255, 250, 255))
    g = lay.filter(ImageFilter.GaussianBlur(10))
    g.alpha_composite(lay)
    E.safe(c, g, int(x - 130), int(y - 130))


@functools.lru_cache(None)
def shaft_layer():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon([(380, -50), (700, -50), (900, 1500), (180, 1500)], fill=(255, 246, 220, 60))
    return lay.filter(ImageFilter.GaussianBlur(60))


def sc_theatre(t, f, c):
    """s1: the 1846 amphitheatre; the camera cranes down past the rows (rows move at their own depth)."""
    t0 = SEG["s1"][0]
    t_year = T("s1", "ألف")
    down = E.step(t, t0, T("s1", "نام") - 0.3)
    orbit = 60 * math.sin((t - t0) * 0.6)
    c.alpha_composite(FX.bg3d("theatre", f, 0.5, lerp(0.30, 0.60, down), lerp(1.3, 1.05, down),
                              px=orbit, py=lerp(160, -60, down), dolly=0.5))
    sh = shaft_layer().copy()
    fl = 0.75 + 0.25 * math.sin(f * 0.7) * math.sin(f * 0.23)
    sh.putalpha(sh.getchannel("A").point(lambda v: int(v * fl)))
    c.alpha_composite(sh)
    FX.dust(c, t, f, orbit, 0, n=40, seed=7)
    if t >= t_year:
        k = int((t - t_year) * FPS)
        s = {0: 1.9, 1: 1.5, 2: 0.92, 3: 1.03}.get(k, 1.0)
        im = stamp_img("١٨٤٦")
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        im = FX.yaw(im, 18 * math.sin((t - t_year) * 0.8) * math.exp(-(t - t_year) * 0.6) + orbit * 0.05)
        jx, jy = (14, -8) if k == 3 else (0, 0)
        E.paste(c, im, 540 + jx - orbit * 0.6, 900 + jy, rot=-7, seed=81, f=f)


def sc_sleep(t, f, c):
    """s1: ether vapour; the red sparks go out and his eyes close. The camera creeps in."""
    t_sleep = T("s1", "نام")
    k = E.step(t, t_sleep + 0.35, t_sleep + 1.3)
    push = E.step(t, t_sleep - 0.4, SEG["s1"][1])
    zoom = lerp(1.05, 1.3, push)
    orbit = 50 * math.sin(t * 0.5)
    awake = FX.bg3d("awake", f, 0.5, 0.42, zoom, px=orbit, dolly=0.4)
    c.alpha_composite(awake)
    if k > 0:
        sl = FX.bg3d("asleep", f, 0.5, 0.42, zoom, px=orbit, dolly=0.4)
        if k < 1:
            sl.putalpha(int(255 * k))
        c.alpha_composite(sl)
    sparks(c, 560, 660, 470, t, f, amount=max(0, 1 - E.step(t, t_sleep + 0.1, t_sleep + 1.0)), n=20, seed=5, size=1.2)
    vapour(c, 470 - orbit, 1320, t, t_sleep - 0.3, amount=1 - 0.5 * E.step(t, t_sleep + 2.5, t_sleep + 4))
    FX.dust(c, t, f, orbit, 0, n=24, seed=9)


FLOOR = 1500


def sc_doubt(t, f, c):
    """s2: a dark room. The hesitant surgeon in the foreground; the scale lowers onto the floor behind him and
    tips toward pain; three anatomical cards swing in, then are struck out."""
    t0 = SEG["s2"][0]
    orbit = 110 * math.sin((t - t0) * 0.33)
    c.alpha_composite(FX.stage_bg(f, orbit, horizon=1080))
    t_sc = t0 + 0.3
    t_pain = T("s2", "الألم")
    drop = E.step(t, t_sc, t_sc + 1.3)
    ang = lerp(0, 24, E.step(t, t_pain, t_pain + 0.9))
    if t >= t_pain + 0.75:
        ang += 2.5 * math.exp(-(t - t_pain - 0.75) * 4) * math.cos((t - t_pain) * 18)
    clip_t = [T("s2", "المناعة"), T("s2", "القلب"), T("s2", "الشفاء")]
    focus = E.step(t, clip_t[0] - 0.3, clip_t[0] + 0.4)
    h = 960
    top = scale_top_for_floor(h, FLOOR - 140)
    draw_scale(c, 640 - orbit * 0.45, lerp(-1300, top, drop), h, ang, f, t, pain=E.step(t, t_pain, t_pain + 0.6),
               blur=int(round(2 * focus)), yaw_deg=-orbit * 0.07, floor_shadow=drop > 0.97)
    FX.fog(c, t, y0=1250, strength=0.30)
    # surgeon: nearest layer, moves most
    sx = 250 - orbit * 1.4
    FX.contact_shadow(c, sx + 30, 1890, 520, alpha=200)
    im = FX.yaw(dimmed("surgeon_doubt", 1300, int(round(3 * focus)), round(1 - 0.45 * focus, 2)), 10 - orbit * 0.06)
    E.paste(c, im, sx, 1290, seed=3, f=f)
    t_none = T("s2", "ولم")
    for i, (name, x, hh) in enumerate((("cell", 830, 250), ("heart", 540, 300), ("arm", 250, 190))):
        tt = clip_t[i]
        if t < tt:
            continue
        s = 1 + (0.06 * hb(t) if name == "heart" else 0)
        im = card_in(E.scaled(name, int(hh * s)), t, tt, 0.4, 85)
        bob = 10 * math.sin(t * 1.3 + i)
        E.paste(c, im, x - orbit * 0.9, 1150 + bob, seed=90 + i, f=f)
    if t >= t_none:
        for i, x in enumerate((830, 540, 250)):
            u = E.step(t, t_none + 0.15 * i + 0.4, t_none + 0.15 * i + 0.75)
            strike(c, x - 150 - orbit * 0.9, 1090, x + 150 - orbit * 0.9, 1210, u, f)
    FX.dust(c, t, f, orbit, 0, n=36, seed=11)


def sc_sydenham(t, f, c):
    """s3: candle-lit; the 1600s physician writes; his sentence swings in; the scale far behind levels for a moment."""
    t0 = SEG["s3"][0]
    orbit = 90 * math.sin((t - t0) * 0.4)
    c.alpha_composite(FX.stage_bg(f, orbit, horizon=1000, lamp=0.5))
    t_mod = T("s3", "معتدل")
    ang = lerp(24, 0, E.step(t, t_mod - 0.1, t_mod + 0.5))
    ang = lerp(ang, 24, E.step(t, t_mod + 1.4, t_mod + 2.2))
    h = 700
    draw_scale(c, 760 - orbit * 0.25, scale_top_for_floor(h, 1180), h, ang, f, t, pain=0.7, blur=3, yaw_deg=-orbit * 0.05)
    FX.fog(c, t, y0=1150, strength=0.35)
    fl = 0.8 + 0.2 * math.sin(f * 1.7) * math.sin(f * 0.9)
    c.alpha_composite(E.glow_spot((260, 760, 1000, 1500), (255, 170, 80), int(95 * fl), 100))
    x = 470 - orbit * 1.1
    FX.contact_shadow(c, x, 1500, 700, alpha=180)
    E.paste(c, FX.yaw(E.scaled("sydenham", 640), 12 - orbit * 0.05), x, 1240, seed=5, f=f)
    qw = [T("s3", w) for w in ("قدر", "معتدل", "من", "الألم", "أداة", "تستخدمها", "الطبيعة", "لأغراض")]
    qw.append(T("s3", "حكيمة"))
    n = sum(1 for x_ in qw if t >= x_)
    if n:
        im = card_in(quote_paper(n), t, qw[0], 0.5, 80)
        E.paste(c, im, 540 - orbit * 0.3, 450, rot=1.2, seed=60, f=f)
    FX.dust(c, t, f, orbit, 0, n=30, seed=13)


def scale_flip_angle(t):
    t_flip = T("s4", "انقلب")
    if t < t_flip:
        return 24 + 1.2 * math.sin(t * 3)
    u = t - t_flip
    if u < 0.25:
        return 24 + 6 * math.sin(u * 80)
    u -= 0.25
    a = lerp(24, -26, E.step(u, 0, 0.55))
    if u > 0.55:
        a += 5 * math.exp(-(u - 0.55) * 3) * math.cos((u - 0.55) * 11)
    return a


def sc_flip(t, f, c):
    """s4: climax. The scale flips; pain flies up empty; coloured pills pour into the other pan;
    the camera pushes in on the pills."""
    t0 = SEG["s4"][0]
    t_flip = T("s4", "انقلب")
    orbit = 80 * math.sin((t - t0) * 0.45)
    c.alpha_composite(FX.stage_bg(f, orbit, horizon=1050))
    k_fill = E.step(t, t_flip + 0.35, t_flip + 1.8)
    pain = 1.0 - E.step(t, t_flip + 0.2, t_flip + 0.6)
    shake = (0, 0)
    if 0 <= t - t_flip < 0.45:
        shake = np.random.default_rng(f).normal(0, 22, 2)
    push = E.step(t, t_flip + 1.0, t_flip + 3.2)
    h = lerp(1080, 1500, push)
    cx = lerp(540, 860, push) - orbit * 0.5
    top = lerp(scale_top_for_floor(1080, FLOOR - 120), 230, push)
    info = draw_scale(c, cx + shake[0], top + shake[1], h, scale_flip_angle(t), f, t, pills=k_fill, pain=pain,
                      yaw_deg=-orbit * 0.07)
    if info:
        bx, ry, hw = info
        FX.falling_pills(c, t, t_flip + 0.3, t_flip + 1.7, (bx, ry), hw, f)
    elif t >= t_flip + 0.3:
        FX.falling_pills(c, t, t_flip + 0.3, t_flip + 1.7, (cx - 240 * h / 1017, top + 700 * h / 1017), 250, f)
    FX.fog(c, t, y0=1350, strength=0.25)
    FX.dust(c, t, f, orbit, 0, n=30, seed=15)


def sc_pharmacy(t, f, c):
    """s4: the present. A cold, flickering pharmacy aisle; the camera walks down it; prescriptions fall
    at every depth; four people — three dark, one lit orange with a pill."""
    t0 = scene_t0("pharmacy")
    push = E.step(t, t0, SEG["s4"][1] + 0.5)
    orbit = 50 * math.sin((t - t0) * 0.7)
    c.alpha_composite(FX.bg3d("pharmacy", f, 0.5, 0.47, lerp(1.0, 1.4, push), px=orbit, dolly=0.3))
    rx_rain(c, t, T("s4", "فتدفّقت"), f)
    t_ppl = T("s4", "أكثر")
    t_four = T("s4", "أربعة")
    xs = (870, 650, 430, 210)
    for i, x in enumerate(xs):
        ti = t_ppl + i * 0.28
        if t < ti:
            continue
        k = E.step(t, ti, ti + 0.4)
        y = lerp(-500, 1180, k)
        xx = x - orbit * 1.2
        if k >= 1:
            FX.contact_shadow(c, xx, 1560, 300, alpha=170)
        if i == 2 and t >= t_four:
            ko = E.step(t, t_four, t_four + 0.4)
            c.alpha_composite(E.glow_spot((xx - 260, 600, xx + 260, 1700), (255, 160, 70), int(120 * ko), 70))
            E.paste(c, dimmed("modern", 760, 0, 0.35), xx, y, seed=30 + i, f=f)
            im = orange_figure("modern_pill", 760)
            if ko < 1:
                im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * ko)))
            E.paste(c, im, xx, y, seed=30 + i, f=f, shadow=False)
        else:
            E.paste(c, dimmed("modern", 760, 0, 0.35 if t >= t_four else 0.8), xx, y, seed=30 + i, f=f)
    FX.dust(c, t, f, orbit, 0, n=26, seed=17)


def sc_middle(t, f, c):
    """s5: the scale alone under the lamp, swinging and settling toward the middle; the dark closes in."""
    t0 = SEG["s5"][0]
    u = t - t0
    orbit = 100 * math.sin(u * 0.3)
    c.alpha_composite(FX.stage_bg(f, orbit, horizon=1050))
    ang = -26 * math.exp(-u * 0.45) * math.cos(u * 2.4)
    t_small = T("s5", "ألمًا")
    h = lerp(1080, 1180, E.step(t, t0, SEG["s5"][1]))
    draw_scale(c, 540 - orbit * 0.5, scale_top_for_floor(h, FLOOR - 100), h, ang, f, t, pills=0.45,
               small_spark=E.step(t, t_small, t_small + 0.4), yaw_deg=-orbit * 0.08)
    FX.fog(c, t, y0=1350, strength=0.3)
    FX.dust(c, t, f, orbit, 0, n=30, seed=19)


def sc_logo(t, f, c):
    """Book title, a pill rolls to the middle and becomes the eye of بصيرة."""
    u = t - LOGO[0]
    roll = E.step(u, 0.3, 1.4)
    x = lerp(180, 540, roll)
    y = 960
    eye_k = E.step(u, 1.3, 1.9)
    d = ImageDraw.Draw(c)
    if eye_k > 0:
        w2, h2 = 330 * eye_k, 150 * eye_k
        top = [(540 + w2 * math.cos(a), y - h2 * math.sin(a)) for a in np.linspace(0, math.pi, 40)]
        bot = [(540 + w2 * math.cos(a), y - h2 * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 40)]
        d.line(E.torn_poly(top, f, 6, 2), fill=E.CREAM + (255,), width=14)
        d.line(E.torn_poly(bot, f, 7, 2), fill=E.CREAM + (255,), width=14)
    rr = 70 + 40 * eye_k
    c.alpha_composite(E.glow_spot((x - rr * 2, y - rr * 2, x + rr * 2, y + rr * 2), (255, 160, 70), 130, 40))
    pill = Image.new("RGBA", (int(rr * 2) + 8, int(rr * 2) + 8), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.ellipse((4, 4, rr * 2 + 4, rr * 2 + 4), fill=ORANGE + (255,), outline=E.CREAM + (255,), width=6)
    pd.line((rr + 4, 10, rr + 4, rr * 2 - 2), fill=(170, 80, 30, 255), width=5)
    E.paste(c, pill.rotate(roll * 540, resample=Image.BICUBIC), x, y, seed=99, f=f)
    if u > 1.9:
        font = ImageFont.truetype(E.FONT, 120)
        k = int((u - 1.9) * FPS)
        s = {0: 0.6, 1: 1.08}.get(k, 1.0)
        tim = Image.new("RGBA", (600, 220), (0, 0, 0, 0))
        ImageDraw.Draw(tim).text((300, 110), "بصيرة", font=font, fill=E.CREAM + (255,), anchor="mm", direction="rtl", language="ar")
        tim = tim.resize((int(600 * s), int(220 * s)))
        E.paste(c, tim, 540, 1240, shadow=False, seed=98, f=f)


def scene_t0(name):
    return {s.draw.__name__: s.t0 for s in SCENES}["sc_" + name]


SCENES = [
    E.Scene(0.0, None, sc_hook, bg=None),
    E.Scene(SEG["s1"][0], None, sc_theatre, bg=None),
    E.Scene(T("s1", "نام") - 0.35, None, sc_sleep, bg=None),
    E.Scene(SEG["s2"][0], None, sc_doubt, bg=None),
    E.Scene(SEG["s3"][0], None, sc_sydenham, bg=None),
    E.Scene(SEG["s4"][0], None, sc_flip, bg=None),
    E.Scene(T("s4", "فتدفّقت") - 0.45, None, sc_pharmacy, bg=None),
    E.Scene(SEG["s5"][0], None, sc_middle, bg=None),
    E.Scene(LOGO[0], None, sc_logo, bg=(16, 13, 12)),
]

L = E.Label
LABELS = [
    L("وأنت مستيقظ", ("وأنت", "مستيقظ"), [T("s0", "وأنت"), T("s0", "مستيقظ")], hide=T("s0", "والدواء"), x=540, y=330, size=88),
    L("لكنّه يرفض", ("يرفض",), [T("s0", "لكنّه"), T("s0", "يرفض")], hide=SEG["s0"][1], x=540, y=330, size=88),
    L("لم يشعر بالألم", ("يشعر", "بالألم"), [T("s1", "يشعر") - 0.15, T("s1", "يشعر"), T("s1", "بالألم")],
      hide=SEG["s1"][1], x=540, y=330, size=84),
    L("الألم نافع", ("نافع",), [T("s2", "الألم"), T("s2", "نافع")], hide=T("s2", "يقوّي"), x=540, y=250, size=84),
    L("بلا دليل", ("دليل",), [T("s2", "دليل") - 0.2, T("s2", "دليل")], hide=SEG["s2"][1], x=540, y=250, size=90),
    L("انقلب الميزان", ("انقلب", "الميزان"), [T("s4", "انقلب"), T("s4", "الميزان")], hide=T("s4", "فتدفّقت") - 0.45, x=540, y=200, size=92),
    L("واحد من كل أربعة", ("واحد", "أربعة"), [T("s4", "أمريكيّ"), T("s4", "من", 2), T("s4", "كلّ"), T("s4", "أربعة")],
      hide=SEG["s4"][1], x=540, y=330, size=80),
    L("ألمًا صغيرًا", ("ألمًا", "صغيرًا"), [T("s5", "ألمًا"), T("s5", "صغيرًا")], hide=T("s5", "يقول"), x=540, y=250, size=88),
    L("يقول لك شيئًا؟", ("شيئًا؟",), [T("s5", "يقول"), T("s5", "لك"), T("s5", "شيئًا")], hide=SEG["s5"][1], x=540, y=250, size=88),
    L("أمة الدوبامين", (), [LOGO[0] + 0.1, LOGO[0] + 0.3], hide=DUR + 1, x=540, y=560, size=80),
]




# subliminal 2-frame flashes of the patient's eyes (psychological horror)
SUBLIM = [T("s0", "يرفض") + 0.45, T("s2", "دليل") + 0.5, T("s4", "خطرًا") + 0.1, SEG["s5"][1] - 0.35]
# words that get an RGB-split jolt
JOLTS = [T("s0", "مستيقظ"), T("s0", "يرفض"), T("s2", "دليل"), T("s4", "انقلب"), T("s4", "أربعة"), T("s5", "شيئًا")]


def post(arr, t, f, idx):
    t_flip = T("s4", "انقلب")
    early = t < SEG["s2"][0]
    vig = 0.55 + (0.3 * hb(t) if early else 0.0)
    if SEG["s5"][0] <= t < LOGO[0]:
        vig = lerp(0.6, 1.25, E.step(t, SEG["s5"][0], SEG["s5"][1]))      # the dark closes in
    flick = 0.10
    if scene_t0("pharmacy") <= t < SEG["s5"][0]:
        flick = 0.22                                                       # fluorescent tubes
    sat = 0.4
    if LOGO[0] <= t:
        vig, flick, sat = 0.45, 0.03, 1.0
    arr = FX.horror_grade(arr, t, f, vig=vig, flicker=flick, sat=sat)
    # the flip: white flash
    if t >= t_flip + 0.25:
        fl = {0: 0.7, 1: 0.3, 2: 0.1}.get(int(math.floor((t - t_flip - 0.25) * FPS + 1e-6)), 0)
        if fl:
            arr = arr * (1 - fl) + 250 * fl
    for tj in JOLTS:
        k = int(math.floor((t - tj) * FPS + 1e-6))
        if k in (0, 1):
            arr = FX.rgb_split(arr, 14 if k == 0 else 6)
            arr = np.asarray(E.glitch(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), f, band=30, every=140, amount=30).convert("RGB")).astype(float)
    for ts in SUBLIM:
        k = int(math.floor((t - ts) * FPS + 1e-6))
        if k in (0, 1):
            arr = FX.rgb_split(FX.eyes_flash() * (1.0 if k == 0 else 0.6) + arr * (0 if k == 0 else 0.4), 12)
    if t < LOGO[0]:
        arr = FX.scratches(arr, f)
    return arr



def word_table():
    for s in TEXT:
        print(s, " ".join(f"{w}@{t:.2f}" for w, t in WORDS[s]))


if __name__ == "__main__":
    if sys.argv[1] == "words":
        word_table()
    elif sys.argv[1] == "at":
        for x in sys.argv[2:]:
            E.frame(int(round(float(x) * FPS)), SCENES, LABELS, DUR, post=post)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, b), post=post)
