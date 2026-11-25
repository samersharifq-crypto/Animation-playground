"""Part 15: cut out the footprint trail and the knotted measuring rope."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("footprints", "src/footprints.jpg", border=8, white_min=238)
E.cutout("measuring_rope", "src/measuring_rope.jpg", border=6, white_min=236, min_hole=150, hole_margin=2)
