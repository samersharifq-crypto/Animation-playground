"""Sound for part 1. Without the voice yet: effects only, on the estimated timings."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.io import wavfile
import basira_sound as S
import part_1 as P
T, DUR = P.T, P.DUR
voice = sys.argv[1] if len(sys.argv) > 1 else None
if voice is None:                                   # silent placeholder voice
    voice = "proj/silence.wav"; wavfile.write(voice, S.SR, np.zeros(S.t2i(DUR + 1), np.float32))
    tl = S.Timeline(DUR, voice, [], start=0, place_at=0)
else:
    raise SystemExit("real voice: timing step not wired yet")

# night wind in Corinth (soft, until the room)
n = S.t2i(T["warubbama"]); tt = np.arange(n) / S.SR
wind = S.bandnoise(n, 250, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * tt) * np.sin(2 * np.pi * 0.31 * tt + 1))
tl.add(0, S.norm(wind * S._fade(n, n / S.SR, 1.5, 1.0), -33))
# footsteps while Sisyphus walks in
t = T["aash"]
while t < T["makran"] - 0.3: tl.add(t, S.shuffle()); t += 0.34
# Death: wing flap on «الموت», a distant rumble
for k in range(3): tl.add(T["mawt"] + 0.1 + k * 0.28, S.whoosh(0.45, -24 - k * 2))
tl.add(T["mawt"], S.rumble(db=-28))
tl.add(T["lam_yahrub"], S.whoosh(0.35, -27))
# chains: rattle when he holds them out, clatter + lock on «فأغلقها»
for k in range(5): tl.add(T["famadda"] + 0.2 + k * 0.09, S.clink(-34 - k))
for k in range(7): tl.add(T["faaghlaqaha"] - 0.25 + k * 0.05, S.clink(-28 - k))
tl.add(T["faaghlaqaha"], S.crack(-14)); tl.add(T["faaghlaqaha"], S.clink(-20))
# scene tear on «لكنّ»
tl.add(T["lakin"] - 0.13, S.tear())
# the rock: heavy rolling rumble with the shadow
n = S.t2i(P.ROLL + 0.8); tt = np.arange(n) / S.SR
roll = S.lownoise(n, 90, 3) * (0.7 + 0.3 * np.abs(np.sin(2 * np.pi * 2.2 * tt))) * np.sin(np.pi * tt / tt[-1])
tl.add(T["fasakhra"] - 0.1, S.norm(roll, -9)); tl.add(T["fasakhra"] + 0.3, S.big_thunder(3.0) * 0.35, duck=True)
# flashes into the room: zap on each switch, ding on the first, hum while there
for a, b in P.FLASHES:
    tl.add(a, S.zap())
    tl.add(a, S.hum(min(b, DUR) - a))
    if b < DUR: tl.add(b, S.zap(-28))
tl.add(P.FLASHES[0][0], S.ding())
tl.labels([[T["korintha"]], [T["sisyphus"]], [T["mawt"]], [T["dahrajtaha"], T["anta"], T["ams"]]])
tl.mix("proj/mix_1.wav")
