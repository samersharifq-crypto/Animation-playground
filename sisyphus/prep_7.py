"""Part 7: cut out the photo props."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
for n in ["bp_gauge", "inhaler", "stethoscope"]:
    E.cutout(n, f"src/{n}.jpg")
E.cutout("old_map", "src/old_map.jpg", border=6, min_hole=10 ** 9)   # the pale map paper must stay solid
