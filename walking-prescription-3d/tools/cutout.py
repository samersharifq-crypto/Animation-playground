# Cuts the white paper backdrop out of the source images (flood fill from the border),
# feathers the edge and writes transparent WebP files to ../assets.
# usage: python3 tools/cutout.py <src_dir>   (needs Pillow + numpy)
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets')
# name in src dir -> (output name, cut background? (True or cut() options), max size)
JOBS = {
    '538a88e0-image.jpg': ('pills', dict(lo=251, spread=3, border=5), 900),
    'cbd0277d-image.jpg': ('girl-walk-a', dict(border=7), 1000),
    '68b3236b-image.jpg': ('girl-walk-b', dict(border=7), 1000),
    '619509c2-image.jpg': ('girl-stand', dict(border=7), 1000),
    '7dc5c46f-image.jpg': ('girl-back', dict(border=7), 1000),
    '7d3dd0a2-image.jpg': ('rx', True, 900),
    'e64c1637-image.jpg': ('hand', dict(holes=True), 900),
    'ee2ab475-image.jpg': ('tree-digital', dict(border=7), 1100),
    '8d50cd41-image.jpg': ('tree-green', dict(border=7), 1100),
    'ee27aab1-image.jpg': ('seedling', dict(border=7), 600),
    '12d3b9bf-image.jpg': ('canopy', False, 1100),
}

def cut(im, lo=236, spread=14, holes=False, border=0):
    a = np.asarray(im.convert('RGB')).astype(np.int16)
    mn, mx = a.min(2), a.max(2)
    white = (mn >= lo) & (mx - mn <= spread)
    m = Image.fromarray(np.where(white, 255, 0).astype(np.uint8)).copy()
    h, w = white.shape
    # flood every white border pixel region with 128 = "outside"
    for x in range(0, w, 4):
        for y in (0, h - 1):
            if m.getpixel((x, y)) == 255: ImageDraw.floodfill(m, (x, y), 128)
    for y in range(0, h, 4):
        for x in (0, w - 1):
            if m.getpixel((x, y)) == 255: ImageDraw.floodfill(m, (x, y), 128)
    outside = (np.asarray(m) == 128) | (white if holes else False)
    alpha = Image.fromarray(np.where(outside, 0, 255).astype(np.uint8))
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    rgba = im.convert('RGBA'); rgba.putalpha(alpha)
    if border:  # cream sticker edge, like a paper cut-out glued on card
        edge = alpha.filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(1))
        card = Image.new('RGBA', im.size, (246, 240, 226, 0)); card.putalpha(edge)
        rgba = Image.alpha_composite(card, rgba)
        alpha = rgba.getchannel('A')
    return rgba.crop(alpha.point(lambda v: 255 if v > 8 else 0).getbbox())

for src, (name, do_cut, size) in JOBS.items():
    im = Image.open(os.path.join(SRC, src))
    if do_cut: im = cut(im, **(do_cut if isinstance(do_cut, dict) else {}))
    im.thumbnail((size, size), Image.LANCZOS)
    im.save(os.path.join(OUT, name + '.webp'), quality=88, method=6)
    print(name, im.size)

# the pills sheet -> one sprite per pill (split on the empty columns between them)
import numpy as np
im = Image.open(os.path.join(OUT, 'pills.webp')); a = np.asarray(im)[..., 3].max(0) > 10
runs, start = [], None
for x, v in enumerate(list(a) + [False]):
    if v and start is None: start = x
    if not v and start is not None:
        if x - start > 20: runs.append((start, x))
        start = None
for i, (x0, x1) in enumerate(runs):
    p = im.crop((x0, 0, x1, im.height)); p = p.crop(p.getchannel('A').getbbox())
    p.save(os.path.join(OUT, f'pill-{i}.webp'), quality=90); print('pill', i, p.size)
os.remove(os.path.join(OUT, 'pills.webp'))
