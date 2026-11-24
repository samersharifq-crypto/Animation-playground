"""Part 11: cut out the video camera, the chair and the man (upright and slumped)."""
import sys; sys.path.insert(0, ".")
import basira_engine as E
E.setup("proj", "font/ReemKufi-Bold.ttf")
E.cutout("video_camera", "src/video_camera.jpg", border=8, min_hole=150, hole_margin=3)
E.cutout("chair", "src/chair.jpg", border=8, min_hole=150, hole_margin=3)
E.cutout("man_seated", "src/man_seated.jpg", border=10, min_hole=150, hole_margin=3)
E.cutout("man_slumped", "src/man_slumped.jpg", border=10, min_hole=150, hole_margin=3)
