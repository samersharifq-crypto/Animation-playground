"""Gemini images -> clean cut-outs and backgrounds (removes the orange floor strips and the counter lines)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import basira_engine as E

E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi.ttf"))
SRC = os.path.join(HERE, "src"); CLEAN = os.path.join(E.ROOT, "clean"); os.makedirs(CLEAN, exist_ok=True)


def no_floor(a):
    """Whiten the flat orange floor strip under a figure (wide rows near the bottom)."""
    nw = a.min(axis=2) < 225
    cnt = nw.sum(1)
    lo = int(a.shape[0] * 0.82)
    band = cnt[lo:]
    if band.max() < 250: return a
    rows = np.where(band > 0.6 * band.max())[0] + lo
    a[rows.min():] = 255
    return a


def clean(name, fix=None):
    a = np.asarray(Image.open(os.path.join(SRC, name + ".jpg")).convert("RGB")).copy()
    a = no_floor(a)
    if fix: fix(a)
    p = os.path.join(CLEAN, name + ".png"); Image.fromarray(a).save(p); return p


def counter_lines(a):
    a[290:332, 742:] = 255


def drawer_off(a):
    a[412:, 672:] = 255
    a[:, 786:] = 255


def open_gaps(name, keep=9):
    """Cream paper filling gaps (between stool legs) -> see-through, keeping a thin paper rim."""
    from scipy import ndimage
    p = os.path.join(E.ROOT, "cut", name + ".png"); a = np.asarray(Image.open(p)).copy()
    op = a[..., 3] > 0
    cream = op & (np.abs(a[..., :3].astype(int) - np.array(E.CREAM)).sum(2) < 12)
    white = op & (a[..., :3].min(2) > 225)
    dist = ndimage.distance_transform_edt(~(op & ~cream & ~white))
    a[(cream & (dist > keep)) | (white & (dist > 2)), 3] = 0
    Image.fromarray(a).save(p); E.load.cache_clear(); E.scaled.cache_clear()


if __name__ == "__main__":
    E.cutout("man", clean("man"))
    E.cutout("man_angry", clean("man_angry"))
    E.cutout("man_sit", clean("man_sit", counter_lines), border=6, min_hole=300)
    open_gaps("man_sit")
    E.cutout("cop", clean("cop"))
    E.cutout("youth_drawer", clean("youth_drawer"))
    a = np.asarray(Image.open(os.path.join(SRC, "youth_drawer.jpg")).convert("RGB")).copy(); a = no_floor(a); drawer_off(a)
    Image.fromarray(a).save(os.path.join(CLEAN, "youth.png")); E.cutout("youth", os.path.join(CLEAN, "youth.png"))
    E.cutout("chain", os.path.join(SRC, "chain.jpg"), border=8)
    import make_assets as M
    for y in ("1920", "1933"):
        M.calendar(os.path.join(CLEAN, "cal" + y + ".png"), y); E.cutout("cal" + y, os.path.join(CLEAN, "cal" + y + ".png"))
    for n in ("street", "saloon"):
        Image.open(os.path.join(SRC, n + ".jpg")).convert("RGB").save(os.path.join(E.ROOT, "bg", n + ".png"))
    names = ["man", "man_angry", "man_sit", "cop", "youth_drawer", "youth", "chain"]
    sheet = Image.new("RGBA", (2100, 800), E.NAVY + (255,))
    for i, n in enumerate(names):
        E.paste(sheet, E.scaled(n, 640), 150 + i * 300, 400)
    sheet.convert("RGB").save(os.path.join(E.ROOT, "cut_sheet.png"))
    for n in names:
        im = E.load(n); print(n, im.size)
