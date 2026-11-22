import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import film as F
from PIL import Image
times = [float(x) for x in sys.argv[2:]]
for t in times: F.render_frame(int(round(t * F.FPS)))
ims = [Image.open(os.path.join(F.OUT, f"{int(round(t*12)):05d}.png")).resize((270, 480)) for t in times]
cols = 6; rows = (len(ims) + cols - 1) // cols
c = Image.new("RGB", (270 * cols, 480 * rows))
for i, im in enumerate(ims): c.paste(im, ((i % cols) * 270, (i // cols) * 480))
c.save(sys.argv[1])
