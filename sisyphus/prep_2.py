"""Part 2: cut out the new drawings."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
from PIL import Image, ImageDraw
# calendar: rub out the drawn cast shadow, keep the falling pages
im = Image.open("src/calendar.jpg").convert("RGB")
m = Image.new("L", im.size, 0); d = ImageDraw.Draw(m)
d.polygon([(470, 526), (698, 512), (752, 484), (722, 528), (760, 548), (820, 572), (852, 530), (900, 520), (900, 720), (470, 720)], fill=255)
d.polygon([(617, 557), (697, 540), (720, 570), (760, 590), (789, 601), (760, 625), (732, 642), (710, 642), (680, 632), (660, 615), (625, 575)], fill=0)
im.paste((255, 255, 255), (0, 0), m); im.save("clean/calendar.png")
for n in ["hourglass", "old_man", "wounded", "sisyphus_kneel", "sisyphus_throne", "calendar"]:
    E.cutout(n.replace("sisyphus_", "sis_"), "clean/calendar.png" if n == "calendar" else f"src/{n}.jpg")
E.cutout("hades", "src/hades.jpg", border=6)
