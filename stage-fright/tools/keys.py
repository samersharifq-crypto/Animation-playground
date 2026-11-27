import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import film, engine as E
T=[float(x) for x in sys.argv[1:]]
for t in T: E.frame(int(round(t*E.FPS)), film.SCENES, film.post)
E.contact_sheet(T, os.path.join(E.ROOT,"build","sheet.png"), cols=6)
