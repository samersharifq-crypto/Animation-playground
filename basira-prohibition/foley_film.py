"""Draft foley for the full Short (no music): old projector rattle in the past, silence + phone hum today."""
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
HERE = os.path.dirname(os.path.abspath(__file__))

import json
SR = 48000
_W = json.load(open(os.path.join(HERE, "proj", "warp.json"))) if os.path.exists(os.path.join(HERE, "proj", "warp.json")) else None
def M(t): return float(np.interp(t, _W["old"], _W["new"])) if _W else t
DUR = _W["dur"] if _W else 61.5; N = int(DUR * SR); T_TODAY = M(44.0)
mix = np.zeros((N, 2)); rng = np.random.default_rng(1)


def bp(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band"); return lfilter(b, a, x)

def lp(x, hi):
    b, a = butter(2, hi / (SR / 2)); return lfilter(b, a, x)

def env(n, a, d):
    t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)

def add(t, sig, gain=1.0, pan=0.0, raw=False):
    i = int((t if raw else M(t)) * SR); sig = sig[: max(0, N - i)]
    mix[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan)); mix[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))

def noise(d): return rng.standard_normal(int(d * SR))

def slam():
    n = int(0.9 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (70 - 30 * t) * t) * env(n, 0.002, 0.2) * 1.3 + bp(noise(0.9), 300, 3000) * env(n, 0.001, 0.04)

def chain(d=0.7, k=14):
    out = np.zeros(int(d * SR))
    for _ in range(k):
        i = int(rng.uniform(0, d - 0.1) * SR); n = int(0.08 * SR); t = np.arange(n) / SR; f0 = rng.uniform(1800, 4200)
        out[i:i + n] += (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.7 * t)) * env(n, 0.0005, 0.02) * 0.35
    return out

def click(f0=2500, d=0.03):
    n = int(0.15 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f0 * t) * env(n, 0.0003, d) + bp(noise(0.15), 1000, 6000) * env(n, 0.0003, 0.01)

def paper(d=0.5, lo=800, hi=7000):
    n = int(d * SR); t = np.arange(n) / SR
    return bp(noise(d), lo, hi) * np.sin(np.pi * t / d) ** 2

def rip():
    n = int(0.5 * SR); t = np.arange(n) / SR; grit = (rng.random(n) < 0.02) * rng.standard_normal(n)
    return bp(rng.standard_normal(n) * 0.6 + grit * 4, 1500, 9000) * np.sin(np.pi * t / 0.5) * 0.7

def thud(f0=110, d=0.07):
    n = int(0.5 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f0 * t) * env(n, 0.001, d) + bp(noise(0.5), 200, 1500) * env(n, 0.001, 0.03) * 0.6

def heartbeat():
    return np.concatenate([thud(55, 0.09), np.zeros(int(0.05 * SR))])[: int(0.35 * SR)] * 1.4

def step():
    n = int(0.12 * SR); return bp(noise(0.12), 150, 1200) * env(n, 0.001, 0.025)

def pour(d=3.0):
    n = int(d * SR); t = np.arange(n) / SR
    g = bp(noise(d), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t) ** 2)
    return g * np.minimum(1, np.minimum(t / 0.15, (d - t) / 0.4))

def swish(d=0.8):
    n = int(d * SR); t = np.arange(n) / SR; return bp(noise(d), 150, 700) * np.sin(np.pi * t / d) ** 3

def whoosh_spin(d=1.2):
    n = int(d * SR); t = np.arange(n) / SR
    return bp(noise(d), 400, 3000) * np.sin(np.pi * t / d) ** 2 * (0.5 + 0.5 * np.sin(2 * np.pi * (3 + 9 * t) * t))

def burn(d=0.8):
    n = int(d * SR); t = np.arange(n) / SR; cr = (rng.random(n) < 0.01) * rng.standard_normal(n) * 3
    return bp(noise(d) * 0.4 + cr, 800, 8000) * np.sin(np.pi * t / d)

def clock(d=0.9):
    out = np.zeros(int(d * SR))
    for k in range(int(d / 0.15)):
        c = click(3200, 0.01) * 0.6; i = int(k * 0.15 * SR); out[i:i + len(c)] += c[: len(out) - i]
    return out

def creak(d=0.6):
    n = int(d * SR); t = np.arange(n) / SR
    f = 180 + 120 * t / d; ph = np.cumsum(f) / SR
    s = np.sign(np.sin(2 * np.pi * ph)) * (rng.random(n) < 0.3)
    return lp(s, 1800) * np.sin(np.pi * t / d) * 0.6

def glitch_s(d=0.35):
    n = int(d * SR); t = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * 90 * t)) * 0.3 * (rng.random(n) < 0.5) + bp(noise(d), 2000, 9000) * 0.5

def buzz(d=0.5):
    n = int(d * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 160 * t) * (np.sin(2 * np.pi * 9 * t) > 0) * np.minimum(1, (d - t) / 0.05) * 0.6

def drawer():
    return thud(90, 0.06) + bp(noise(0.5), 400, 2500) * env(int(0.5 * SR), 0.01, 0.06) * 0.4


# projector rattle under the whole past (classic film), cut dead at «اليوم»
tp = np.arange(int(T_TODAY * SR)) / SR
rattle = bp(rng.standard_normal(len(tp)), 1500, 6000) * (np.sin(2 * np.pi * 24 * tp) > 0.6) * 0.05
rattle += lp(rng.standard_normal(len(tp)), 120) * 0.08
mix[: len(tp), 0] += rattle; mix[: len(tp), 1] += rattle
th = np.arange(N - int(T_TODAY * SR)) / SR                            # modern room: faint electric hum
hum = (np.sin(2 * np.pi * 50 * th) * 0.02 + bp(rng.standard_normal(len(th)), 2000, 8000) * 0.006)
mix[int(T_TODAY * SR):, 0] += hum; mix[int(T_TODAY * SR):, 1] += hum

add(1.9, slam(), 0.9); add(1.95, chain(), 0.6); add(2.15, click(900, 0.02), 0.35)
add(3.2, swish(1.0), 0.3)                                              # iris closes
add(5.6, thud(80, 0.12), 0.7)                                          # 1920 lands on the card
add(7.0, whoosh_spin(), 0.45); add(8.2, paper(0.25, 300, 3000), 0.5); add(8.6, thud(), 0.9)
add(10.0, rip(), 0.35)
for k in range(5): add(10.0 + 0.18 * k, step(), 0.5, pan=-0.3 + 0.12 * k)
for d in (0.0, 0.5, 1.05): add(12.2 + d, swish(1.1), 0.45, pan=0.4 - 0.3 * d)
for a, b in [(12.05, 0), (12.3, 0), (13.95, 0), (14.6, 0)]: add(a, click(600, 0.01), 0.25)   # lamp flicker
add(15.5, swish(0.5), 0.35)
for k, tt in enumerate(np.arange(15.8, 19.4, 0.62)): add(tt, heartbeat(), 0.55 + 0.04 * k)
add(16.0, pour(3.3), 0.35)
add(19.5, burn(0.9), 0.5)
add(25.0, thud(), 0.85)
add(28.0, rip(), 0.35); add(31.6, paper(0.6, 1500, 6000), 0.3)
add(33.0, clock(0.9), 0.5); add(33.9, chain(0.9, 18), 0.7); add(34.4, thud(70, 0.1), 0.6); add(34.6, paper(0.6), 0.25)
add(36.0, creak(0.7), 0.7)
add(37.5, swish(0.8), 0.3)
add(38.6, rip(), 0.35); add(42.6, swish(0.8), 0.3)
add(44.0, glitch_s(0.4), 0.5)
add(48.0, paper(0.4, 1500, 6000), 0.3)
add(50.2, buzz(0.6), 0.6)
add(51.0, rip(), 0.3); add(53.2, drawer(), 0.85)
add(55.4, paper(0.5, 1500, 6000), 0.3)
add(57.4, swish(1.2), 0.35); add(58.6, thud(60, 0.2), 0.6)
add(58.7, thud(70, 0.15), 0.6); add(59.25, click(1400, 0.02), 0.4); add(59.7, paper(0.6), 0.3); add(60.2, paper(0.6, 1500, 6000), 0.3)
if _W:
    for ts in _W["labels"]:
        for tt in ts: add(tt, paper(0.07, 2500, 8000), 0.1, raw=True)
mix /= max(1e-6, np.abs(mix).max()) / 0.85
os.makedirs(os.path.join(HERE, "proj"), exist_ok=True)
wavfile.write(os.path.join(HERE, "proj", "sfx_sync.wav" if _W else "foley_film.wav"), SR, (mix * 32767).astype(np.int16))
print("ok")
