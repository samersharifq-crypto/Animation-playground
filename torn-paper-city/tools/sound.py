# Builds the soundtrack for "Torn Paper City" from the cues the film exports:
# a slow plucked-piano lullaby over a paper-and-vinyl room tone, with paper slaps for every word,
# rips and whooshes on the tears, swishes for the sliding slices, a knock for the finger tap,
# soft pops for the magnifier rings, footsteps, a shutter creak and an eye blink.
# usage: python3 sound.py cues.json out.wav      (numpy only)
import sys, json, wave, numpy as np

data = json.load(open(sys.argv[1]))
SR, TOTAL = 44100, float(data['total'])
N = int(SR * TOTAL)
rng = np.random.default_rng(2026)
mix = np.zeros((N, 2))

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]
    mix[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    mix[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))

def filt(x, lo=None, hi=None):
    n = len(x); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); g = np.ones_like(f)
    if hi: g *= 1 / (1 + (f / hi) ** 4)
    if lo: g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(X * g, n)
def ts(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.uniform(-1, 1, int(d * SR))
def midi(m): return 440 * 2 ** ((m - 69) / 12)

def piano(f, d=2.2):
    x = ts(d)
    s = sum(a * np.sin(2 * np.pi * f * h * x) * np.exp(-x * h * .9) for h, a in [(1, 1), (2, .45), (3, .2), (4, .08)])
    return s * np.minimum(1, x / .004) * np.exp(-x * 1.3)
def pad(fs, d):
    x = ts(d); s = sum(np.sin(2 * np.pi * f * x + .4 * np.sin(2 * np.pi * .2 * x)) for f in fs) / len(fs)
    return s * np.minimum(1, x / 1.2) * np.minimum(1, (d - x) / 1.2)

# ---- music: 76 bpm, Dm - Bb - F - C (i - VI - III - VII), soft arpeggios ----
beat = 60 / 76
prog = [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64]]
bar = beat * 4; t = 0.4; k = 0
while t < TOTAL - 1:
    ch = prog[k % 4]
    add(pad([midi(m - 12) for m in ch[:2]] + [midi(ch[2])], bar + .8), t, .05)
    add(piano(midi(ch[0] - 12), 3), t, .16)
    for j, step in enumerate([1, 2, 3, 2, 1, 3, 2, 3]):
        if rng.random() < .85:
            add(piano(midi(ch[step] + 12)), t + j * beat / 2, .07 + .03 * (j == 0), pan=rng.uniform(-.4, .4))
    t += bar; k += 1
# fade the music out at the end
x = np.arange(N) / SR
mix *= np.clip((TOTAL - x) / 2.5, 0, 1)[:, None]

# ---- room tone: paper rustle + soft vinyl crackle ----
bed = filt(noise(TOTAL), 300, 3000) * .006
cr = np.zeros(N); idx = rng.integers(0, N, int(TOTAL * 9)); cr[idx] = rng.uniform(-.3, .3, len(idx))
bed += filt(cr, 1500, 8000) * .5
mix += np.stack([bed, np.roll(bed, 300)], 1)

# ---- effects ----
def slap():
    x = ts(.12); return filt(noise(.12), 400, 5000) * np.exp(-x * 45) * .9 + np.sin(2 * np.pi * 120 * x) * np.exp(-x * 40) * .6
def rip():
    d = .55; x = ts(d); n = filt(noise(d), 1200, 9000)
    am = (rng.random(len(x)) < .02).astype(float); am = np.convolve(am, np.ones(300) / 30, 'same')
    return n * (0.4 + am) * np.minimum(1, x / .02) * np.exp(-x * 3)
def whoosh(d=1.1):
    x = ts(d); n = filt(noise(d), 200, 2500); e = np.sin(np.pi * np.clip(x / d, 0, 1)) ** 2
    return n * e
def swish():
    d = .3; x = ts(d); return filt(noise(d), 1500, 7000) * np.sin(np.pi * x / d) ** 3
def thump():
    x = ts(.25); return np.sin(2 * np.pi * np.cumsum(70 + 60 * np.exp(-x * 25)) / SR) * np.exp(-x * 14)
def tap():
    x = ts(.15); return (np.sin(2 * np.pi * 900 * x) * .6 + np.sin(2 * np.pi * 520 * x)) * np.exp(-x * 45)
def pop():
    x = ts(.4); return np.sin(2 * np.pi * (700 + 500 * x) * x) * np.exp(-x * 9) * .5 + piano(midi(81), .4) * .4
def step():
    x = ts(.09); return filt(noise(.09), 150, 1500) * np.exp(-x * 60)
def creak():
    d = .7; x = ts(d); f = 180 + 60 * np.sin(2 * np.pi * 3 * x)
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * filt(noise(d), 300, 2000) * .5 * np.sin(np.pi * x / d)
def unroll():
    d = 1.0; x = ts(d); return filt(noise(d), 600, 4000) * np.sin(np.pi * x / d) * (0.6 + .4 * np.sin(2 * np.pi * 18 * x))
def blink():
    x = ts(.12); return filt(noise(.12), 2000, 9000) * np.exp(-x * 40) * .5

FX = {'slap': (slap, .32), 'rip': (rip, .55), 'whoosh': (whoosh, .32), 'swish': (swish, .2), 'thump': (thump, .45),
      'tap': (tap, .6), 'pop': (pop, .45), 'step': (step, .18), 'creak': (creak, .14), 'unroll': (unroll, .22),
      'pass': (whoosh, .16), 'blink': (blink, .3)}
for c in data['cues']:
    fn, g = FX[c['type']]
    add(fn(), c['t'], g * rng.uniform(.85, 1.1), pan=rng.uniform(-.35, .35))

mix /= max(1e-9, np.abs(mix).max()) / .85
out = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('sound', TOTAL, 's')
