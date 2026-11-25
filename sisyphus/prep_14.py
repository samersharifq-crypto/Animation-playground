"""Part 14: the night desert background and the cut-outs (traveler from behind, hermitage, scholar's house, two villages)."""
import sys; sys.path.insert(0, ".")
from PIL import Image
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
Image.open("src/desert_night.jpg").convert("RGB").save("proj/bg/desert_night.png")
E.cutout("traveler_back", "src/traveler_back.jpg", border=10, white_min=236)
E.cutout("hermitage", "src/hermitage.jpg", border=8, white_min=236)
E.cutout("scholar_house", "src/scholar_house.jpg", border=8, white_min=236)
E.cutout("village_good", "src/village_good.jpg", border=8, white_min=236)
E.cutout("village_bad", "src/village_bad.jpg", border=8, white_min=236)
