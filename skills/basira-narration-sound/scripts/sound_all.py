"""sound_all.py (template) - the final mix of every part: the edited voice (proj/vo_N.wav) + synthesized paper-foley effects, no music.
Generic layer for every part: room tone, a tear on each torn scene change, a pop/tick for each label word.
Then each part's own moments. Run: python3 sound_all.py [N ...]  ->  proj/mix_N.wav"""
import sys, os, importlib
import numpy as np
from scipy.io import wavfile
import basira_sound as S

HERE = os.path.dirname(os.path.abspath(__file__))


def warm(dur, f0=220.0, db=-30):
    """soft warm pad (two sines, slow swell) - a 'light' that is not music: no melody, one held tone"""
    n = S.t2i(dur); tt = np.arange(n) / S.SR
    x = np.sin(2 * np.pi * f0 * tt) + 0.5 * np.sin(2 * np.pi * f0 * 1.5 * tt) + 0.25 * np.sin(2 * np.pi * f0 * 2 * tt)
    return S.norm(x * np.sin(np.pi * np.minimum(1, tt / dur)) ** 1.5, db)


def wind(dur, db=-33):
    n = S.t2i(dur); tt = np.arange(n) / S.SR
    x = S.bandnoise(n, 250, 1400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * tt) * np.sin(2 * np.pi * 0.31 * tt + 1))
    return S.norm(x * S._fade(n, dur, 1.2, 1.0), db)


def thud(db=-22):
    n = S.t2i(0.35); return S.norm(S.lownoise(n, 160, 3) * S.env(n, 0.003, 0.35, 7), db)


class Mix:
    def __init__(self, voice, dur):
        self.voice = np.zeros(S.t2i(dur), np.float32)
        v = voice[:len(self.voice)]; self.voice[:len(v)] = v
        self.sfx = np.zeros_like(self.voice)

    def add(self, t, x, duck=False):
        if t < 0: x = x[S.t2i(-t):]; t = 0
        i = S.t2i(t); j = min(len(self.sfx), i + len(x))
        if i >= len(self.sfx) or j <= i: return
        x = x[:j - i]
        if duck:
            e = np.convolve(np.abs(self.voice), np.ones(S.t2i(.15)) / S.t2i(.15), mode="same")[i:j]
            x = x * (1 - 0.7 * np.clip(e / 0.05, 0, 1))
        self.sfx[i:j] += x

    def write(self, out):
        m = self.voice + self.sfx
        n = S.t2i(0.6); m[-n:] *= np.linspace(1, 0, n)
        wavfile.write(out, S.SR, (0.95 * np.tanh(m / 0.95)).astype(np.float32))


def generic(m, P):
    for i, s in enumerate(P.SCENES):
        if i and s.rip: m.add(s.t0 - 0.03, S.tear())
    for L in P.LABELS:
        m.add(L.times[0] - 0.08, S.pop())
        for t in L.times[1:]: m.add(t, S.tick())


def steps(m, t0, t1, every=0.34, db=-31):
    t = t0
    while t < t1: m.add(t, S.shuffle(db)); t += every


def part12(m, P, T):
    """example of a part's own moments (Sisyphus part 12): the screen tears in two, a push, the half falls, a warm tone"""
    m.add(P.SPLIT0, S.tear(0.6))
    m.add(P.STEP_T, thud(-24)); m.add(P.STEP_T, S.shuffle(-30))
    m.add(P.FALL0, S.tear(0.7)); m.add(P.FALL0 + 0.6, S.whoosh(0.6, -30))
    m.add(T["la"] - 0.1, warm(4.5, 196, -31))


EXTRA = {12: part12}                                    # one function per part; parts without one get the generic layer only


def run(n):
    P = importlib.import_module(f"part_{n}")
    vp = os.path.join(HERE, "proj", f"vo_{n}.wav")
    voice = wavfile.read(vp)[1].astype(np.float32) if os.path.exists(vp) else np.zeros(1, np.float32)
    m = Mix(voice, P.DUR)
    generic(m, P)
    if n in EXTRA: EXTRA[n](m, P, P.T)
    m.write(os.path.join(HERE, "proj", f"mix_{n}.wav"))
    print(f"part {n}: mix {P.DUR:.1f}s")


if __name__ == "__main__":
    for n in [int(x) for x in sys.argv[1:]]:
        run(n)
