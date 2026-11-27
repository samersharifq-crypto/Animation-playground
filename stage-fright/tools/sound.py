"""sound.py - synthesized paper-foley soundtrack for «رهبة» (no music library, numpy only)."""
import os, sys, wave
import numpy as np
from scipy import signal
sys.path.insert(0, os.path.dirname(__file__))
import film

SR, DUR = 44100, film.DUR
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(1)

def add(x, t, gain=1.0, pan=0.0):
    i = int(t * SR); x = x[: max(0, N - i)]
    L[i:i + len(x)] += x * gain * (1 - max(0, pan)); R[i:i + len(x)] += x * gain * (1 + min(0, pan))

def env(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)

def band(x, lo, hi):
    b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x)

def low(x, hi):
    b, a = signal.butter(2, hi / (SR / 2)); return signal.lfilter(b, a, x)

def noise(sec): return rng.standard_normal(int(sec * SR))

def rip(t, g=0.5):
    n = noise(0.45); e = env(len(n), 0.03, 0.18)
    crack = (rng.random(len(n)) < 0.004) * rng.standard_normal(len(n)) * 6
    add(band(n + crack, 900, 6000) * e, t, g, pan=0.3)
    add(band(n, 200, 900) * e, t + 0.05, g * 0.5, pan=-0.3)

def step_snd(t, g):
    n = noise(0.12); add(low(n, 400) * env(len(n), 0.002, 0.03) + band(n, 1500, 4000) * env(len(n), 0.001, 0.01) * 0.3, t, g)

def thump(t, g=0.9):
    for k, dt in ((1.0, 0), (0.6, 0.16)):
        n = int(0.3 * SR); tt = np.arange(n) / SR
        add(np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 30)) * tt) * env(n, 0.004, 0.09) * k, t + dt, g)

def pop(t, g=0.35, pan=0.0):
    n = noise(0.06); add(band(n, 600, 3500) * env(len(n), 0.001, 0.015), t, g, pan)

def tone(freq, sec, a=0.01, d=1.2):
    n = int(sec * SR); tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * freq * h * tt) / h ** 1.6 for h in (1, 2, 3, 4))
    return x * env(n, a, d)

# room tone / wind bed
bed = low(noise(DUR), 300) * 0.08
bed[: int(3 * SR)] += band(noise(3), 300, 1200)[: int(3 * SR)] * 0.05 * np.sin(np.linspace(0, np.pi, int(3 * SR)))
L += bed; R += np.roll(bed, 400)

# 1-2 footsteps (city, hallway getting quieter)
for i, t in enumerate(np.arange(0.2, 3.0, 0.5)): step_snd(t, 0.5)
for i, t in enumerate(np.arange(3.3, 7.4, 0.5)):
    step_snd(t, 0.55 * (1 - i / 11)); step_snd(t + 0.18, 0.12 * (1 - i / 11))   # corridor echo

# tears
for t in (2.95, 7.45, 16.95, 19.55, 22.35, 24.95, 27.45): rip(t)

# 3 door: knee bounce taps, creak, rush of light
for t in np.arange(7.7, 9.6, 0.25): pop(t, 0.15)
n = int(1.1 * SR); tt = np.arange(n) / SR
creak = np.sin(2 * np.pi * (180 + 90 * np.sin(tt * 9) + 60 * tt) * tt) * (1 + 0.6 * np.sign(np.sin(2 * np.pi * 34 * tt)))
add(band(creak, 150, 2500) * np.sin(np.linspace(0, np.pi, n)) * 0.25, 9.6)
n = int(1.4 * SR); sw = band(noise(1.4), 300, 5000) * np.linspace(0, 1, n) ** 2.5
add(sw * 0.5, 10.6)
add(tone(220, 2.0, 0.3, 1.5) * 0.25, 11.6); add(tone(330, 2.0, 0.3, 1.5) * 0.15, 11.6)

# 4 lecture: crowd murmur, heartbeat, eyes popping in
n = int(5 * SR); mur = band(noise(5), 250, 900) * (0.5 + 0.5 * np.sin(np.arange(n) / SR * 7)) * np.linspace(0.2, 1, n) * 0.12
add(mur, 12.0)
for b in film.BEATS: thump(b, 0.8)
for i, t in enumerate(film.EYE_T): pop(t, 0.4, pan=(i % 3 - 1) * 0.5)

# 5 orbit: heartbeat continues, rising ear ringing, glitch
t = 17.0
while t < 19.2: thump(t, 0.9); t += 0.32
n = int(2.4 * SR); tt = np.arange(n) / SR
ring = np.sin(2 * np.pi * (3800 + 300 * tt) * tt) * np.linspace(0, 1, n) ** 2 * 0.07
add(ring, 17.0); add(band(noise(0.35), 500, 8000) * 0.4, 19.25)
for t in np.arange(17.0, 19.4, 0.2): pop(t, 0.12, pan=np.sin(t * 5) * 0.8)

# 6 room: clock ticks, phone buzz, bottle rattle
for t in np.arange(19.8, 25.0, 1.0):
    n = noise(0.03); add(band(n, 2000, 6000) * env(len(n), 0.0005, 0.006), t, 0.25, pan=-0.4)
n = int(0.6 * SR); tt = np.arange(n) / SR
add(np.sign(np.sin(2 * np.pi * 150 * tt)) * band(np.ones(n), 100, 400) * 0 + low(np.sign(np.sin(2 * np.pi * 150 * tt)), 600) * env(n, 0.01, 0.3) * 0.08, 20.0)
for k in range(9): pop(23.3 + k * 0.045 + rng.uniform(0, 0.02), 0.18, pan=-0.5)

# 7 ending: a few soft notes toward the light (A minor -> C), leading back into the loop
for t, fq in ((25.2, 220.0), (25.9, 261.6), (26.6, 329.6), (27.3, 392.0)):
    add(tone(fq, 2.5, 0.01, 1.1) * 0.22, t, pan=0.2); add(tone(fq * 2, 2.0, 0.01, 0.6) * 0.06, t, pan=-0.2)

mx = max(np.abs(L).max(), np.abs(R).max())
st = np.stack([L, R], 1) / mx * 0.85
out = os.path.join(film.E.ROOT, "build", "mix.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print(out)
