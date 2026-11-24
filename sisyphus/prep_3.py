"""Part 3: cut out Zeus and the pushing pose; cut the cup off the throne drawing."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("zeus", "src/zeus.jpg")
E.cutout("sis_push", "src/sisyphus_push.jpg")
# the cup that falls when the king dies (cut off the throne drawing)
from PIL import Image
Image.open("proj/cut/sis_throne.png").convert("RGBA").crop((20, 20, 180, 96)).save("proj/cut/cup.png")
