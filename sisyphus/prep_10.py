"""Part 10: cut out the typewriter, the head silhouette and Sisyphus letting go."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("typewriter", "src/typewriter.jpg", border=8)
E.cutout("head_silhouette", "src/head_silhouette.jpg", border=10)
E.cutout("sis_letgo", "src/sisyphus_letgo.jpg", border=10)
