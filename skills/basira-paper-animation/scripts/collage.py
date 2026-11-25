"""collage.py - the 'science' look of بصيرة: old photos on light grid paper (like the dopamine video).
grid_bg(f): boiling grid-paper background. impression(text, seed): red rubber-stamp print (e.g. «فاشل»)."""
import functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import basira_engine as E

# ------------------------------------------------------------------ 2. the collage world: grid paper
GRID = (246, 242, 232)


@functools.lru_cache(None)
def _grid_lines():
    lay = Image.new("RGBA", (E.W + 80, E.H + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i, x in enumerate(range(0, E.W + 80, 40)):
        d.line([(x, 0), (x, E.H + 80)], fill=(120, 160, 190, 120 if i % 5 == 0 else 55), width=2 if i % 5 == 0 else 1)
    for i, y in enumerate(range(0, E.H + 80, 40)):
        d.line([(0, y), (E.W + 80, y)], fill=(120, 160, 190, 120 if i % 5 == 0 else 55), width=2 if i % 5 == 0 else 1)
    return lay


def grid_bg(f):
    r0 = np.random.default_rng(f); ox, oy = r0.integers(0, 12), r0.integers(0, 12)
    arr = (np.array(GRID, float)[None, None, :] + E.TEX[oy:oy + E.H, ox:ox + E.W][..., None]) * (0.8 + 0.2 * E.VIG)
    c = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    r = np.random.default_rng(f // 2)
    c.alpha_composite(_grid_lines().crop((int(r.integers(0, 4)), int(r.integers(0, 4)), int(r.integers(0, 4)) + E.W, 0 + E.H)))
    return c




@functools.lru_cache(None)
def impression(text, seed):
    """red rubber-stamp ink: double border, uneven ink, a few gaps"""
    font = ImageFont.truetype(E.FONT, 120)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = tmp.textlength(text, font=font, direction="rtl", language="ar")
    w, h = int(tw + 120), 230
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = E.BRICK + (235,)
    d.rounded_rectangle((8, 8, w - 8, h - 8), 22, outline=col, width=10)
    d.rounded_rectangle((26, 26, w - 26, h - 26), 14, outline=col, width=4)
    d.text((60, 28), text, font=font, fill=col, direction="rtl", language="ar")
    a = np.asarray(im).copy()
    r = np.random.default_rng(seed)
    blot = r.random(a.shape[:2])
    from scipy import ndimage
    blot = ndimage.gaussian_filter(blot, 3)
    a[..., 3] = (a[..., 3] * np.clip((blot - 0.40) * 6, 0.25, 1)).astype(np.uint8)
    return Image.fromarray(a)


