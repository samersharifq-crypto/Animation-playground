"""sound_all.py - the final mix of every part: the edited voice (proj/vo_N.wav) + synthesized paper-foley effects, no music.
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


def part1(m, P, T):
    m.add(0, wind(T["warubbama"]))
    steps(m, T["aash"], T["makran"] - 0.3)
    for k in range(3): m.add(T["mawt"] + 0.1 + k * 0.28, S.whoosh(0.45, -24 - k * 2))
    m.add(T["mawt"], S.rumble(db=-28))
    for k in range(5): m.add(T["famadda"] + 0.2 + k * 0.09, S.clink(-34 - k))
    for k in range(7): m.add(T["faaghlaqaha"] - 0.25 + k * 0.05, S.clink(-28 - k))
    m.add(T["faaghlaqaha"], S.crack(-14))
    n = S.t2i(P.ROLL + 0.8); tt = np.arange(n) / S.SR
    roll = S.lownoise(n, 90, 3) * (0.7 + 0.3 * np.abs(np.sin(2 * np.pi * 2.2 * tt))) * np.sin(np.pi * tt / tt[-1])
    m.add(T["fasakhra"] - 0.1, S.norm(roll, -10)); m.add(T["fasakhra"] + 0.3, S.big_thunder(3.0) * 0.35, duck=True)
    for a, b in P.FLASHES:
        m.add(a, S.zap()); m.add(a, S.hum(min(b, P.DUR) - a))
        if b < P.DUR: m.add(b, S.zap(-28))
    m.add(P.FLASHES[0][0], S.ding())


def part2(m, P, T):
    m.add(T["ghadibat"], S.rumble(db=-26), duck=True)
    m.add(T["ilah_alharb"], S.whoosh(0.7, -25))
    m.add(T["waakhadh"], S.water(T["faad"] - T["waakhadh"] + 0.5, -34))
    m.add(T["yawman"], S.ding(-32))
    m.add(T["faad"], S.whoosh(0.5, -28))


def part3(m, P, T):
    m.add(T["maat"], S.rumble(db=-28))
    m.add(T["zeus"] - 0.02, S.crack(-6)); m.add(T["zeus"] + 0.01, S.big_thunder(4.5), duck=True)
    m.add(T["sakhra"], thud(-20))
    m.add(T["fawada"], thud(-26)); steps(m, T["yadfa"], P.DUR - 0.5, 0.5, -30)


def part4(m, P, T):
    t = T["khutwa"]
    while t < T["intasar"]:                              # heavy steps up the hill
        m.add(t, thud(-30)); m.add(t + 0.05, S.shuffle(-32)); t += 0.8
    m.add(T["aflatat"], S.whoosh(0.5, -24))
    n = S.t2i(T["alqa"] - T["aflatat"] + 0.6); tt = np.arange(n) / S.SR
    roll = S.lownoise(n, 90, 3) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 3 * tt)))
    m.add(T["aflatat"] + 0.1, S.norm(roll * S._fade(n, n / S.SR, 0.2, 0.4), -12), duck=True)
    for k in range(4): m.add(T["aflatat"] + 0.8 + k * (T["alqa"] - T["aflatat"]) / 4, thud(-20 - 2 * k))
    m.add(T["saqat"], thud(-18))


def part5(m, P, T):
    steps(m, T["nahad"] + 0.9, T["min_jadid"] - 0.2)
    m.add(T["wafi"], thud(-28))
    m.add(T["awda"] - 0.6, S.rumble(2.0, -26), duck=True)
    for a, b in P.FLASHES:
        m.add(a, S.zap()); m.add(a, S.hum(b - a))
        m.add(b, S.zap(-28))
    m.add(P.FLASHES[0][0], S.ding())
    m.add(T["aadat"], S.rumble(2.2, -22), duck=True)


def part6(m, P, T):
    for t0, _ in P.SWAPS: m.add(t0, S.zap()); m.add(t0 + 0.55, S.zap(-28))
    m.add(P.LETGO, S.whoosh(0.5, -27)); m.add(P.LETGO + 0.6, thud(-24))
    for _, key, _, _ in P.STAMPS: m.add(T[key], thud(-16)); m.add(T[key], S.pop(-22))
    m.add(T["ilm"], S.whoosh(0.8, -27))
    m.add(T["tamaman"] + 0.5, S.drone(1.8, -30))


def part7(m, P, T):
    m.add(T["arbain"], S.ding(-32))
    m.add(T["daght"], S.ding(-33))
    m.add(T["la"], S.whoosh(0.5, -30))


def part8(m, P, T):
    m.add(P.CUT1, S.whoosh(0.5, -26))
    for k in ("makan", "waqt", "shuur"): m.add(T[k], S.whoosh(0.35, -30))
    m.add(T["tashtail"], S.crack(-24))
    m.add(T["damaghak"], S.ding(-31))


def part10(m, P, T):
    for t in P.KEYS: m.add(t, S.tick(-22)); m.add(t + 0.06, S.tick(-26))
    for i in range(0, 60, 3): m.add(P.CHAIN0 + i * 0.022, S.tick(-34))
    m.add(P.SLIP, S.crack(-20))
    for i in range(0, 60, 2): m.add(T["faukmil"] + (59 - i) * P.TOPPLE, S.tick(-30))
    m.add(T["faukmil"] + 60 * P.TOPPLE + 0.3, thud(-18))
    m.add(P.FLASH0, S.zap()); m.add(P.FLASH0 + 0.3, S.rumble(2.0, -24), duck=True); m.add(P.FLASH1, S.zap(-26))
    m.add(T["fikra"], S.tear())


def part11(m, P, T):
    m.add(0.3, S.hum(P.CUT_CAM - 0.3, -40))
    for i in range(46): m.add(P.chair_t(i), S.tick(-33))
    m.add(P.CUT_CAM, S.hum(T["khizy"] - P.CUT_CAM, -41))
    m.add(P.GROW0, S.rumble(P.GROW1 - P.GROW0 + 1.5, -25), duck=True)


def part12(m, P, T):
    m.add(P.SPLIT0, S.tear(0.6))
    m.add(T["shuur"], thud(-26)); m.add(T["shuur"] + 0.05, S.shuffle(-30))
    m.add(P.STEP_T, thud(-24)); m.add(P.STEP_T, S.shuffle(-30))
    m.add(P.FALL0, S.tear(0.7)); m.add(P.FALL0 + 0.6, S.whoosh(0.6, -30))
    m.add(T["la"] - 0.1, warm(4.5, 196, -31))


def part13(m, P, T):
    m.add(T["ishrin"], thud(-22))
    m.add(P.FLY0 - 0.3, S.whoosh(P.FLY1 - P.FLY0 + 1.2, -26))
    m.add(T["khamsa"], S.tear(0.5)); m.add(T["khamsa"] + 0.1, S.ding(-30))
    for k in ("ard", "rifaq", "insan"): m.add(T[k] - 0.1, S.pop(-26))
    m.add(P.DARK, wind(P.DUR - P.DARK, -32))


def part14(m, P, T):
    m.add(0, wind(P.DUR, -31))
    m.add(T["rajul"] - 0.6, S.shuffle(-31)); m.add(T["rajul"] - 0.25, S.shuffle(-32)); m.add(T["rajul"] + 0.1, S.shuffle(-33))
    for t in (T["nafsan"] + 0.6, T["mia"] + 1.0): m.add(t - 0.1, wind(1.6, -24))
    m.add(T["la"], S.whoosh(0.35, -32))
    m.add(T["naam"], S.ding(-30))
    m.add(T["ard"], warm(4.0, 220, -33))
    m.add(P.TURN + 0.3, S.drone(P.DUR - P.TURN - 0.3, -30))


def part15(m, P, T):
    m.add(0, wind(P.DUR, -32))
    for i in range(len(P.PRINTS)):
        m.add(T["fakharaj"] + i * (T["muntasaf"] - T["fakharaj"]) / len(P.PRINTS), S.shuffle(-31))
    m.add(T["mawt"], thud(-28))
    m.add(T["rahma"] - 0.2, warm(T["faqila"] - T["rahma"] + 1.0, 262, -33))
    m.add(T["adhab"] - 0.2, warm(T["faqila"] - T["adhab"] + 1.0, 155, -34))
    m.add(T["aqrab"], S.ding(-27))
    m.add(T["faghufir"], warm(4.0, 220, -30))
    m.add(T["suqut"], S.tear(0.6))


def part16(m, P, T):
    m.add(0.2, S.drone(T["tawwabun"], -33))
    m.add(T["tawwabun"], warm(6.0, 196, -32))
    m.add(T["tawwabun"] + 0.9, S.shuffle(-30)); steps(m, T["tawwabun"] + 1.6, T["latajlis"] - 0.1)
    m.add(T["latajlis"], thud(-26))
    t = T["tariq"] + 0.3
    while t < T["basira"] - 0.4:
        m.add(t, thud(-30)); m.add(t + 0.05, S.shuffle(-32)); t += (T["basira"] - 0.4 - T["tariq"] - 0.3) / 9
    m.add(T["taaliqat"], warm(4.0, 262, -33))
    m.add(P.LOGO0 + 0.5, S.ding(-26))


def part9(m, P, T):
    m.add(T["nura"] - 0.3, S.hum(P.CUT1 - T["nura"] + 0.3, -42))   # the scanner
    m.add(P.FLIP0, S.whoosh(P.FLIP1 - P.FLIP0, -30))                # a year of calendar pages
    for k in range(10): m.add(P.FLIP0 + k * (P.FLIP1 - P.FLIP0) / 10, S.tick(-33))
    m.add(T["irtafaat"], warm(3.0, 220, -33))
    m.add(T["yataafa"], S.ding(-30))


EXTRA = {1: part1, 2: part2, 3: part3, 4: part4, 5: part5, 6: part6, 7: part7, 8: part8, 9: part9, 10: part10,
         11: part11, 12: part12, 13: part13, 14: part14, 15: part15, 16: part16}


def run(n):
    P = importlib.import_module(f"part_{n}")
    vp = os.path.join(HERE, "proj", f"vo_{n}.wav")
    voice = wavfile.read(vp)[1].astype(np.float32) if os.path.exists(vp) else np.zeros(1, np.float32)
    m = Mix(voice, P.DUR)
    generic(m, P)
    EXTRA[n](m, P, P.T)
    m.write(os.path.join(HERE, "proj", f"mix_{n}.wav"))
    print(f"part {n}: mix {P.DUR:.1f}s")


if __name__ == "__main__":
    for n in [int(x) for x in sys.argv[1:]] or range(1, 17):
        run(n)
