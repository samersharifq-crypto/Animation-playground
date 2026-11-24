"""Part 12: cut out the pushing hand and the man with his head in his hands."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("hand_push", "src/hand_push.jpg", border=10)
E.cutout("man_head_hands", "src/man_head_hands.jpg", border=10, min_hole=150, hole_margin=3)
