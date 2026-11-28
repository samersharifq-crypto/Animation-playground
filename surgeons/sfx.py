"""Synthesised horror foley (no music) on the same timeline as short.py. Writes sfx.wav (stereo 44.1 kHz)."""
import sys, math
sys.argv = [sys.argv[0], "words"]
import numpy as np
from scipy import signal
from scipy.io import wavfile
import short as S

SR = 44100
N = int(S.DUR * SR)
rng = np.random.default_rng(1)
L = np.zeros(N); R = np.zeros(N)


def add(x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    x = x[:N - i] * gain
    L[i:i + len(x)] += x * (1 - max(0, pan))
    R[i:i + len(x)] += x * (1 + min(0, pan))


def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2))
    return signal.lfilter(b, a, x)


def bp(x, lo, hi):
    b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def thump(f0=52, d=0.16):
    n = int(0.5 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (f0 + 30 * np.exp(-t * 30)) * t) * env(n, 0.003, d)
    return lp(s + 0.3 * rng.standard_normal(n) * env(n, 0.002, 0.03), 300)


def heartbeat(t0, t1, gain):
    t = t0
    while t < t1:
        add(thump(), t, gain); add(thump(46, 0.13), t + 0.2, gain * 0.7)
        t += 0.75


def drone(t0, t1, gain, f0=41):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    s = 0.5 * np.sin(2 * np.pi * f0 * t) + 0.35 * np.sin(2 * np.pi * f0 * 1.498 * t + np.sin(t * 0.3))
    s += lp(rng.standard_normal(n), 180) * 2.5
    fade = np.minimum(1, np.minimum(t / 1.5, (t[-1] - t) / 1.0 + 1e-3))
    add(s * fade * (0.8 + 0.2 * np.sin(t * 0.7)), t0, gain)


def creak(t, gain=0.5, dur=0.7, f0=320):
    n = int(dur * SR); tt = np.arange(n) / SR
    pulses = (np.sin(2 * np.pi * (18 + 10 * tt) * tt) > 0.92).astype(float)
    s = bp(pulses + 0.2 * rng.standard_normal(n), f0, f0 * 4) * np.minimum(1, tt / 0.05) * np.exp(-tt / dur)
    add(s * 6, t, gain, pan=0.2)


def sting(t, gain=0.6):
    n = int(0.6 * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt) for f in (1480, 1567, 2217)) * env(n, 0.002, 0.18)
    s += bp(rng.standard_normal(n), 2000, 7000) * env(n, 0.001, 0.08) * 2
    add(s * 0.25, t, gain)


def boom(t, gain=1.0):
    n = int(2.5 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (35 + 60 * np.exp(-tt * 8)) * tt) * env(n, 0.002, 0.9)
    s += lp(rng.standard_normal(n), 900) * env(n, 0.001, 0.25) * 1.5
    add(s, t, gain)


def rattle(t0, t1, gain=0.4):
    t = t0
    while t < t1:
        n = int(0.03 * SR)
        add(bp(rng.standard_normal(n), 2500, 8000) * env(n, 0.001, 0.008), t, gain * rng.uniform(0.4, 1), pan=rng.uniform(-.5, .5))
        t += rng.uniform(0.01, 0.05)


def metal(t, gain=0.4):
    n = int(1.2 * SR); tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d) for f, a, d in ((2300, 1, .4), (3710, .6, .25), (5230, .4, .15)))
    add(s * 0.3, t, gain, pan=0.4)


def murmur(t0, t1, gain=0.25):
    n = int((t1 - t0) * SR); tt = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 250, 1100) * (0.6 + 0.4 * np.sin(tt * 3.1) * np.sin(tt * 1.3))
    add(s * np.minimum(1, np.minimum(tt / 0.6, (tt[-1] - tt) / 0.8)), t0, gain)


def hiss(t0, t1, gain=0.15):
    n = int((t1 - t0) * SR); tt = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 3000, 9000) * np.sin(np.pi * tt / tt[-1])
    add(s, t0, gain)


def hum(t0, t1, gain=0.12):
    n = int((t1 - t0) * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * 120 * k * tt) / k for k in range(1, 6))
    flick = (rng.random(n // 2000 + 1) > 0.08).repeat(2000)[:n]
    add(s * flick * np.minimum(1, tt / 0.3), t0, gain)


def paper(t, gain=0.3):
    n = int(0.25 * SR)
    add(bp(rng.standard_normal(n), 1500, 6000) * env(n, 0.01, 0.07), t, gain, pan=rng.uniform(-.6, .6))


T, SEG = S.T, S.SEG
drone(0, S.LOGO[0] + 1.5, 0.22)
heartbeat(0.0, S.SEG["s2"][0] + 3, 0.9)
metal(T("s0", "الجرّاح") + 1.2, 0.5)
sting(T("s0", "يرفض") + 0.45)
murmur(SEG["s1"][0], SEG["s1"][1], 0.22)
boom(T("s1", "ألف"), 0.5)
hiss(T("s1", "نام") - 0.3, T("s1", "نام") + 3.5, 0.18)
creak(SEG["s2"][0] + 0.3, 0.6, 1.3)
creak(T("s2", "الألم"), 0.7, 0.9)
for w in ("المناعة", "القلب", "الشفاء"):
    paper(T("s2", w), 0.35)
sting(T("s2", "دليل") + 0.5)
for i in range(3):
    paper(T("s2", "ولم") + 0.4 + 0.15 * i, 0.45)
paper(T("s3", "قدر"), 0.4)
creak(T("s3", "معتدل"), 0.4, 1.0)
creak(T("s3", "معتدل") + 1.5, 0.4, 0.8)
boom(T("s4", "انقلب"), 1.2)
creak(T("s4", "انقلب") + 0.25, 0.9, 1.2, f0=220)
rattle(T("s4", "انقلب") + 0.3, T("s4", "انقلب") + 1.9, 0.5)
for k in range(14):
    paper(T("s4", "فتدفّقت") + k * 0.12, 0.25)
hum(S.scene_t0("pharmacy"), SEG["s5"][0], 0.08)
sting(T("s4", "خطرًا") + 0.1)
boom(T("s4", "أربعة"), 0.5)
for k in range(6):
    creak(SEG["s5"][0] + k * 1.3, 0.35 * (0.8 ** k), 0.9)
sting(SEG["s5"][1] - 0.35, 0.8)
rattle(S.LOGO[0] + 0.3, S.LOGO[0] + 1.4, 0.25)

mix = np.stack([L, R], 1)
mix = mix / (np.abs(mix).max() + 1e-9) * 0.89
wavfile.write("sfx.wav", SR, (mix * 32767).astype(np.int16))
print("ok")
