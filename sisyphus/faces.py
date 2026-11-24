"""Smudge every face like a thumb rubbed the wet ink: blur + a sideways smear + grain, inside a soft oval.
Originals are kept in proj/cut_orig/ so this can be re-run or undone."""
import sys, os, shutil; sys.path.insert(0, ".")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

CUT, ORIG = "proj/cut", "proj/cut_orig"
os.makedirs(ORIG, exist_ok=True)
FACES = {   # cutout name: [(cx, cy, rx, ry)] in cutout pixels
    "sis_walk": [(226, 135, 40, 54)], "sis_gesture": [(232, 128, 40, 54)],
    "sis_kneel": [(290, 160, 50, 64)], "sis_throne": [(302, 170, 46, 54)],
    "death_fly": [(393, 198, 28, 34)], "death_chained": [(276, 125, 30, 36)],
    "old_man": [(272, 122, 46, 44)], "wounded": [(306, 162, 40, 48)],
    "ares": [(360, 228, 36, 36)], "zeus": [(287, 190, 34, 42)], "sis_push": [(458, 158, 34, 42)],
    "sis_strain": [(500, 292, 62, 74)], "sis_fallen": [(955, 213, 36, 32)],
    "sis_look": [(458, 292, 66, 80)],
    "hades": [(250, 180, 40, 44), (598, 192, 30, 32)],
    "bored_man": [(338, 290, 88, 108)],
    "sis_letgo": [(298, 104, 32, 42)],
    "man_seated": [(185, 125, 38, 48)], "man_slumped": [(184, 142, 38, 46)],
}

def smudge(im, faces, seed=1):
    rgb = im.convert("RGB")
    blur = rgb.filter(ImageFilter.GaussianBlur(8))
    a = np.asarray(blur).astype(float)
    smear = sum(np.roll(a, s, axis=1) for s in range(-14, 15, 2)) / 15          # thumb drag sideways
    r = np.random.default_rng(seed)
    grain = r.normal(0, 6, a.shape[:2])[..., None]
    out = np.clip(smear * 0.6 + a * 0.4 + grain, 0, 255).astype(np.uint8)
    m = Image.new("L", im.size, 0); d = ImageDraw.Draw(m)
    for cx, cy, rx, ry in faces: d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(10))
    res = Image.composite(Image.fromarray(out), rgb, m).convert("RGBA")
    res.putalpha(im.getchannel("A"))
    return res

for n, fs in FACES.items():
    src = os.path.join(ORIG, n + ".png")
    if not os.path.exists(src): shutil.copy(os.path.join(CUT, n + ".png"), src)
    smudge(Image.open(src).convert("RGBA"), fs).save(os.path.join(CUT, n + ".png"))
for a, b in [("ares", "ares_l"), ("sis_walk", "sis_walk_l")]:
    ImageOps.mirror(Image.open(os.path.join(CUT, a + ".png"))).save(os.path.join(CUT, b + ".png"))
