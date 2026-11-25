"""Part 16: cut out Sisyphus rising; prepare the Basira logo (mark and full)."""
import sys; sys.path.insert(0, ".")
from PIL import Image
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("sis_rise", "src/sisyphus_rise.jpg", border=10, white_min=236)
full = Image.open("src/basira_logo_full.png").convert("RGB").resize((E.W, E.H), Image.LANCZOS)
full.save("proj/bg/basira_logo_full.png")
