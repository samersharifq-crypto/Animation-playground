import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import engine as E
for n in ["sit_chair","podium","face_front","walk","crouch","face_side","phone","floor","pills","eyes","door"]:
    E.cutout(n, os.path.join(E.SRC, n + ".jpg"), border=6 if n in ("podium","door","pills") else 8)
    print(n, E.load(n).size)
print("eyes pieces", len(E.pieces("eyes")))
# navy contact sheet
from PIL import Image
names=["sit_chair","podium","face_front","walk","crouch","face_side","phone","floor","pills","eyes","door"]
c=Image.new("RGBA",(6*300,2*420),E.NAVY+(255,))
for i,n in enumerate(names):
    im=E.scaled(n,380); c.alpha_composite(im,(i%6*300+max(0,(300-im.width)//2) if im.width<300 else i%6*300, i//6*420+20)) if im.width<=300 else c.alpha_composite(im.resize((290,int(380*290/im.width))),(i%6*300,i//6*420+20))
c.save("build/cut_sheet.png")
