"""Draft paper-foley for part 1 (no music). Synthesised placeholders until the real voice + SFX."""
import os, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import part_1 as P

SR = 44100
N = int(P.DUR * SR)
mix = np.zeros((N, 2))
rng = np.random.default_rng(1)


def bp(x, lo, hi):
    b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)


def add(t, sig, gain=1.0, pan=0.0):
    i = int(t * SR); sig = sig[: max(0, N - i)]
    mix[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    mix[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))


def env(n, a, d):
    t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)


def slam():
    n = int(0.9 * SR); t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (70 - 30 * t) * t) * env(n, 0.002, 0.18)
    crack = bp(rng.standard_normal(n), 300, 3000) * env(n, 0.001, 0.04)
    return thud * 1.2 + crack * 0.8


def chain():
    out = np.zeros(int(0.7 * SR))
    for k in range(14):
        i = int(rng.uniform(0, 0.6) * SR); n = int(0.08 * SR); t = np.arange(n) / SR
        f0 = rng.uniform(1800, 4200)
        out[i:i + n] += (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 2.7 * t)) * env(n, 0.0005, 0.02) * 0.35
    return out


def click(f0=2500, d=0.03):
    n = int(0.15 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f0 * t) * env(n, 0.0003, d) + bp(rng.standard_normal(n), 1000, 6000) * env(n, 0.0003, 0.01)


def paper(d=0.5, lo=800, hi=7000):
    n = int(d * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), lo, hi) * np.sin(np.pi * t / d) ** 2 * (0.6 + 0.4 * np.abs(np.sin(t * 60)))


def rip():
    n = int(0.5 * SR); t = np.arange(n) / SR
    grit = (rng.random(n) < 0.02) * rng.standard_normal(n)
    return bp(rng.standard_normal(n) * 0.6 + grit * 4, 1500, 9000) * np.sin(np.pi * t / 0.5) * 0.7


def stamp_thud():
    n = int(0.4 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 110 * t) * env(n, 0.001, 0.07) + bp(rng.standard_normal(n), 200, 1500) * env(n, 0.001, 0.03) * 0.6


def step():
    n = int(0.12 * SR); return bp(rng.standard_normal(n), 150, 1200) * env(n, 0.001, 0.025)


def pour(d=3.0):
    n = int(d * SR); t = np.arange(n) / SR
    g = bp(rng.standard_normal(n), 300, 2500) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t) ** 2)
    bub = np.zeros(n)
    for _ in range(60):
        i = rng.integers(0, n - 4000); m = 3000; tt = np.arange(m) / SR
        bub[i:i + m] += np.sin(2 * np.pi * rng.uniform(300, 900) * (1 + 3 * tt) * tt) * env(m, 0.001, 0.015)
    return (g + bub * 0.4) * np.minimum(1, np.minimum(t / 0.15, (d - t) / 0.4))


def swish(d=0.6):
    n = int(d * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 200, 900) * np.sin(np.pi * t / d) ** 3


# night air bed (very low)
air = bp(rng.standard_normal(N), 80, 500) * 0.04
mix[:, 0] += air; mix[:, 1] += bp(rng.standard_normal(N), 80, 500) * 0.04

add(P.T_SLAM, slam(), 0.9)
add(P.T_CHAIN, chain(), 0.6)
add(P.T_CHAIN + 0.55, click(1800, 0.05), 0.6)       # padlock
add(P.T_OFF, click(900, 0.02), 0.35)                # light switch
add(P.T_CAL - 0.1, paper(0.7), 0.25)
add(P.T_CAL_OUT, paper(0.5), 0.2)
add(P.T_STAMP, stamp_thud(), 0.8)
for t in (P.S3, P.S4, P.S5): add(t, rip(), 0.35)
for k in range(5): add(P.T_MAN + 0.18 * k, step(), 0.5, pan=-0.3 + 0.12 * k)
for d in (0.0, 0.45, 0.95): add(P.T_GANG + d + 0.3, swish(0.9), 0.35, pan=0.4)
add(P.T_TIP, stamp_thud() * 0.6, 0.5)               # barrel knocked over
add(P.T_POUR, pour(2.9), 0.35)
add(P.T_HALF, stamp_thud(), 0.8)
for lab in P.LABELS:                                  # tiny paper tick on each new word
    for t in lab.times: add(t, paper(0.08, 2000, 8000), 0.12)

mix /= max(1e-6, np.abs(mix).max()) / 0.8
wavfile.write(os.path.join(HERE, "proj", "foley_1.wav"), SR, (mix * 32767).astype(np.int16))
print("ok")
