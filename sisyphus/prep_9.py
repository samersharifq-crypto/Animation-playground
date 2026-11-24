"""Part 9: cut out the scanner, the brain-scan print and the tear-off calendar."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("scanner", "src/scanner.jpg", border=8)
E.cutout("brain_scan", "src/brain_scan.jpg", border=6, min_hole=10 ** 9)
E.cutout("calendar_block", "src/calendar_block.jpg", border=8, min_hole=10 ** 9)
