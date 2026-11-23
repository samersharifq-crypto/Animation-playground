"""Clean the source drawings (remove drawn ground/shadows), then cut them out."""
import sys; sys.path.insert(0, ".")
import numpy as np
from PIL import Image, ImageDraw
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
os = __import__("os"); os.makedirs("clean", exist_ok=True)

def whiten_below(name, poly_pts, keep=None):
    im = Image.open(f"src/{name}.jpg").convert("RGB")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).polygon(poly_pts, fill=255)
    if keep:                                   # areas (feet) that stay even inside the white zone
        for k in keep: ImageDraw.Draw(m).ellipse(k, fill=0)
    white = Image.new("RGB", im.size, (255, 255, 255))
    im.paste(white, (0, 0), m)
    im.save(f"clean/{name}.png")

W0, H0 = 1344, 756
# rock: everything under its lower contour is ground + pebbles
rock_lo = [(330, 520), (380, 543), (450, 603), (530, 638), (590, 658), (670, 678), (750, 658), (830, 628), (910, 583), (972, 512), (1030, 500)]
whiten_below("rock", rock_lo + [(W0, 500), (W0, H0), (0, H0), (0, 520)])

# figures: the drawn ground line / shadow hatching around the feet goes, the feet stay
band = lambda y: [(0, y), (W0, y), (W0, H0), (0, H0)]
whiten_below("sisyphus_walk", band(688), keep=[(515, 640, 604, 728), (703, 655, 816, 726)])
whiten_below("sisyphus_gesture", band(690), keep=[(536, 650, 644, 728), (686, 640, 750, 732)])
whiten_below("thanatos_chained", [(0, 662), (836, 662), (836, 600), (W0, 600), (W0, H0), (0, H0)], keep=[(556, 560, 836, 700), (580, 650, 668, 726), (700, 650, 764, 726)])

srcs = {"sis_walk": "clean/sisyphus_walk.png", "sis_gesture": "clean/sisyphus_gesture.png",
}
for k, v in srcs.items(): E.cutout(k, v)
# chains: the gaps inside links / between chain and robe stay see-through
for k, v in {"death_fly": "src/thanatos_fly.jpg", "death_chained": "clean/thanatos_chained.png", "chain": "src/chain.jpg"}.items():
    E.cutout(k, v, min_hole=90, hole_margin=2)
E.cutout("rock", "clean/rock.png", border=6)
