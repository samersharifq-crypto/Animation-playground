# Builds the soundtrack: the same drone, TV hiss and warm chord the player synthesizes live.
# usage: python3 sound.py out.wav
import sys, wave, numpy as np
SR, TOTAL = 44100, 64.0
t = np.arange(int(SR * TOTAL)) / SR
starts = [0, 10, 20, 31, 42, 52]
def scene(x): return max(i for i, s in enumerate(starts) if x >= s)
ctrl = np.arange(0, TOTAL, 0.01)
dr, hs, wm = [], [], []
glitches = [(3.9, 4.15), (6.6, 6.85), (8.3, 8.6), (9.2, 9.45)]
for x in ctrl:
    i = scene(x); lt = x - starts[i]
    d = [.32, .3, .2, .26, .24, 0][i]; h = [.008, .03, .025, .015, .05, 0][i]
    w = .32 * np.clip((lt - .6) / 2.4, 0, 1) if i == 5 else 0
    if i == 1 and any(a < lt < b for a, b in glitches): h = .14
    if i == 4 and lt > 8.6: d = h = 0
    dr.append(d); hs.append(h); wm.append(w)
def follow(v, tau):  # one-pole smoothing like setTargetAtTime
    v = np.interp(t, ctrl, v); a = 1 - np.exp(-1 / (SR * tau)); out = np.empty_like(v); y = 0.0
    step = 64
    for k in range(0, len(v), step):
        y += (v[k] - y) * (1 - (1 - a) ** step); out[k:k + step] = y
    return out
D, Hh, Wm = follow(dr, .25), follow(hs, .08), follow(wm, .6)
f0 = np.where(np.array([scene(x) for x in t[::441]]) == 3, 49, 55).astype(float)
f0 = np.interp(t, t[::441], f0); ph = 2 * np.pi * np.cumsum(f0) / SR
saw = lambda p: 2 * ((p / (2 * np.pi)) % 1) - 1
drone = .6 * np.sin(ph) + .12 * saw(ph * 82.4 / 55) + .12 * saw(ph * 110.3 / 55)
# soften the saws with a moving lowpass (cutoff ~ 340..700 Hz)
cut = 520 + 180 * np.sin(2 * np.pi * .18 * t)
y = np.empty_like(drone); s = 0.0
al = 1 - np.exp(-2 * np.pi * cut / SR)
for k in range(len(drone)): s += al[k] * (drone[k] - s); y[k] = s
drone = y
rng = np.random.default_rng(3); n = rng.uniform(-1, 1, len(t))
hiss = np.convolve(n, np.array([1, -1.6, 1]) * .3, 'same')
tri = lambda p: 2 * np.abs(2 * ((p / (2 * np.pi)) % 1) - 1) - 1
warm = sum(.16 * tri(2 * np.pi * f * t) for f in [196, 246.9, 293.7, 392])
warm = np.convolve(warm, np.ones(12) / 12, 'same')
mix = .55 * (D * drone + Hh * hiss + Wm * warm)
fade = np.clip((TOTAL - t) / 1.5, 0, 1); mix *= fade
mix = np.clip(mix / max(1e-6, np.abs(mix).max()) * .8, -1, 1)
st = np.stack([mix, mix], 1)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
