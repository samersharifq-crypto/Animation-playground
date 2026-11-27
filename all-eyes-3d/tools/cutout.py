# Cuts the white backdrop out of the source renders (flood fill from the border), feathers the
# edge and writes transparent WebP sprites to ../assets. The eye sheet is split into 12 eyes.
# usage: python3 tools/cutout.py <src_dir>   (needs Pillow + numpy)
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets')
JOBS = {  # source -> (name, max size)
    'c701f158-image.jpg': ('boy-sit', 1000),
    'e973e7a1-image.jpg': ('boy-walk', 1000),
    '5c79c8cf-image.jpg': ('boy-stand', 1000),
    '97a22b3d-image.jpg': ('boy-hug', 1000),
    '59a253cd-image.jpg': ('face-worried', 1000),
    'ffd0bd3e-image.jpg': ('face-smile', 1000),
    '81b64a8f-image.jpg': ('sheet', 800),
    '224cd532-image.jpg': ('eyes', 1152),
}

def cut(im, lo=238, spread=14):
    a = np.asarray(im.convert('RGB')).astype(np.int16)
    mn, mx = a.min(2), a.max(2)
    m = Image.fromarray(np.where((mn >= lo) & (mx - mn <= spread), 255, 0).astype(np.uint8)).copy()
    w, h = m.size
    for x in range(0, w, 4):
        for y in (0, h - 1):
            if m.getpixel((x, y)) == 255: ImageDraw.floodfill(m, (x, y), 128)
    for y in range(0, h, 4):
        for x in (0, w - 1):
            if m.getpixel((x, y)) == 255: ImageDraw.floodfill(m, (x, y), 128)
    alpha = Image.fromarray(np.where(np.asarray(m) == 128, 0, 255).astype(np.uint8))
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.1))
    rgba = im.convert('RGBA'); rgba.putalpha(alpha)
    return rgba

def cut_sheet(im):  # white paper on white: keep the paper's rectangle (found from its marks + shadow)
    a = np.asarray(im.convert('L'))
    ys, xs = np.where(a < 246)
    box = (xs.min() + 4, ys.min() + 2, xs.max() - 6, ys.max() - 8)
    return im.convert('RGBA').crop(box)

for src, (name, size) in JOBS.items():
    im = Image.open(os.path.join(SRC, src))
    im = cut_sheet(im) if name == 'sheet' else cut(im)
    if name == 'eyes':  # 3 x 4 grid
        W, H = im.size
        for r in range(4):
            for c in range(3):
                e = im.crop((c * W // 3, r * H // 4, (c + 1) * W // 3, (r + 1) * H // 4))
                e = e.crop(e.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox())
                e.save(os.path.join(OUT, f'eye-{r * 3 + c}.webp'), quality=90)
        print('eyes x12'); continue
    # portraits are cut at the chest: keep the bottom edge, crop the rest
    im = im.crop(im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox())
    im.thumbnail((size, size), Image.LANCZOS)
    im.save(os.path.join(OUT, name + '.webp'), quality=88, method=6)
    print(name, im.size)
