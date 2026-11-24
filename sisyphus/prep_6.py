"""Part 6: cut out the photo props (collage world)."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
for n in ["microscope", "cigarette_pack", "hand_letgo", "stamp"]:
    E.cutout(n, f"src/{n}.jpg")
