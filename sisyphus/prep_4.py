"""Part 4: cut out the strain close-up and the fallen pose."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("sis_strain", "src/sisyphus_strain.jpg")
E.cutout("sis_fallen", "src/sisyphus_fallen.jpg")
