"""Part 8: cut out the brain, the three memory photos and Tantalus (pottery style, from the dopamine video)."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("brain", "src/brain.jpg", border=8)
E.cutout("street", "src/street.jpg", border=6, min_hole=10 ** 9)      # the whole printed photo stays solid
E.cutout("wall_clock", "src/wall_clock.jpg", border=8, min_hole=10 ** 9)
E.cutout("bored_man", "src/bored_man.jpg", border=8)
E.cutout("tantalus_reach", "src/tantalus_reach.png")
