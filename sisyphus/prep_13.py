"""Part 13: cut out the Vietnam map, the soldiers, the plane, the house, the family and the soldier back home."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("vietnam_map", "src/vietnam_map.jpg", border=8)
E.cutout("soldiers", "src/soldiers.jpg", border=10)
E.cutout("airplane", "src/airplane.jpg", border=8, white_min=249)          # a white plane on white: tighter threshold
E.cutout("house", "src/house.jpg", border=8, white_min=236)
E.cutout("family", "src/family.jpg", border=10, white_min=236, min_hole=150, hole_margin=3)
E.cutout("soldier_home", "src/soldier_home.jpg", border=10, white_min=236)
