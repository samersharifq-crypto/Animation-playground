# Builds the soundtrack for "Torn Paper Lucid" from the cues the film exports.
# The music follows the film's trip curve: a calm plucked lullaby at first, then the tape starts
# to wow and drift, a slow heartbeat comes in, detuned drones and a high glassy shimmer swell,
# reversed swells rise into each tear, and it all settles to one clear note at the end.
# Effects (slaps, rips, swishes, taps, eyes popping open, glitches, flashes...) sit on the cues.
# usage: python3 sound.py cues.json out.wav      (numpy only)
import sys, json, wave, numpy as np

data = json.load(open(sys.argv[1]))
SR, TOTAL = 44100, float(data['total'])
N = int(SR * TOTAL)
rng = np.random.default_rng(1966)
T = np.arange(N) / SR
keys = np.array(data['trip'])
trip = np.interp(T, keys[:, 0] + .7, keys[:, 1])          # trip intensity over time
trip = np.convolve(trip, np.ones(SR) / SR, 'same')         # smooth it over a second

def ts(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.uniform(-1, 1, int(d * SR))
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def filt(x, lo=None, hi=None):
    n = len(x); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); g = np.ones_like(f)
    if hi: g *= 1 / (1 + (f / hi) ** 4)
    if lo: g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(X * g, n)
def put(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]
    buf[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    buf[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))

def piano(f, d=2.6):
    x = ts(d)
    s = sum(a * np.sin(2 * np.pi * f * h * x) * np.exp(-x * h * .8) for h, a in [(1, 1), (2, .4), (3, .18), (4, .07)])
    return s * np.minimum(1, x / .004) * np.exp(-x * 1.1)
def drone(fs, d):
    x = ts(d); s = np.zeros(len(x))
    for f in fs:
        for det in (-.35, 0, .4):
            s += np.sin(2 * np.pi * (f + det) * x + rng.uniform(0, 6))
    return s / (3 * len(fs)) * np.minimum(1, x / 2) * np.minimum(1, (d - x) / 2)

# ---------- music bus (gets tape wow later) ----------
music = np.zeros((N, 2))
beat = 60 / 66
prog = [[50, 57, 62, 65, 69], [46, 53, 58, 62, 65], [43, 50, 55, 58, 62], [45, 52, 57, 61, 64]]  # Dm Bb Gm A
bar = beat * 4; t = .3; k = 0
while t < TOTAL - 2:
    ch = prog[k % 4]
    put(music, drone([midi(ch[0] - 12), midi(ch[1] - 12)], bar + 2), t, .09)
    put(music, piano(midi(ch[0] - 12), 3.5), t, .16)
    for j, st in enumerate([2, 3, 4, 3, 2, 4, 3, 1]):
        if rng.random() < .8:
            put(music, piano(midi(ch[st] + 12)), t + j * beat / 2, .07, pan=rng.uniform(-.5, .5))
    t += bar; k += 1
# glassy shimmer that grows with the trip
sh = np.zeros(N)
for f in [midi(86), midi(89), midi(93), midi(98)]:
    sh += np.sin(2 * np.pi * f * T + 3 * np.sin(2 * np.pi * .13 * T)) * (.5 + .5 * np.sin(2 * np.pi * rng.uniform(.05, .2) * T + rng.uniform(0, 6)))
sh *= trip ** 1.5 * .035
music[:, 0] += sh; music[:, 1] += np.roll(sh, 900)
# tape wow + flutter, deeper as the trip deepens: read the bus with a wobbling delay
wow = .0025 + .012 * trip
delay = wow * (1 + np.sin(2 * np.pi * .55 * T)) + .0006 * np.sin(2 * np.pi * 7 * T) * trip
idx = np.clip(T - delay, 0, None) * SR
mix = np.zeros((N, 2))
for c in (0, 1):
    mix[:, c] = np.interp(idx + (c * 40 * trip), np.arange(N), music[:, c])
# a single clear note at the very end, after the drift has gone
put(mix, piano(midi(62), 5) * .9 + piano(midi(74), 5) * .4, TOTAL - 5.5, .22)
mix *= np.clip((TOTAL - T) / 2.0, 0, 1)[:, None]

# ---------- heartbeat while things come unstuck ----------
def thud(f0=58):
    x = ts(.28); return np.sin(2 * np.pi * np.cumsum(f0 + 50 * np.exp(-x * 30)) / SR) * np.exp(-x * 13)
hb = 60 / 58; t = 0
while t < TOTAL - 2:
    g = float(np.interp(t, T[::441], trip[::441]))
    if g > .4:
        put(mix, thud(), t, .55 * g); put(mix, thud(52), t + .28, .38 * g)
    t += hb

# ---------- room tone ----------
bed = filt(noise(TOTAL), 300, 3000) * .006
cr = np.zeros(N); i = rng.integers(0, N, int(TOTAL * 9)); cr[i] = rng.uniform(-.3, .3, len(i))
bed += filt(cr, 1500, 8000) * .5
mix += np.stack([bed, np.roll(bed, 300)], 1)

# ---------- effects ----------
def slap():
    x = ts(.12); return filt(noise(.12), 400, 5000) * np.exp(-x * 45) * .9 + np.sin(2 * np.pi * 120 * x) * np.exp(-x * 40) * .6
def rip():
    d = .55; x = ts(d); n = filt(noise(d), 1200, 9000)
    am = (rng.random(len(x)) < .02).astype(float); am = np.convolve(am, np.ones(300) / 30, 'same')
    return n * (0.4 + am) * np.minimum(1, x / .02) * np.exp(-x * 3)
def whoosh(d=1.1):
    x = ts(d); return filt(noise(d), 200, 2500) * np.sin(np.pi * np.clip(x / d, 0, 1)) ** 2
def swell():                                   # reversed piano rising into a tear
    s = piano(midi(74), 1.6) + piano(midi(81), 1.6) * .6
    return s[::-1] * .8
def swish():
    d = .3; x = ts(d); return filt(noise(d), 1500, 7000) * np.sin(np.pi * x / d) ** 3
def thump(): return thud(70)
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
def eye():                                     # a soft wet click as an eye opens
    x = ts(.09); return np.sin(2 * np.pi * (1400 - 6000 * x) * x) * np.exp(-x * 50)
def shift():                                   # tape-stop glitch for the sliding slices
    d = .35; x = ts(d); f = 300 * np.exp(-x * 6)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .3 + filt(noise(d), 800, 6000) * .4
    return s * (np.sin(2 * np.pi * 24 * x) > 0) * np.exp(-x * 4)
def flash():
    x = ts(.25); return (filt(noise(.25), 3000, 14000) + np.sin(2 * np.pi * 2200 * x) * .3) * np.exp(-x * 14)

FX = {'slap': (slap, .3), 'rip': (rip, .55), 'whoosh': (whoosh, .3), 'swish': (swish, .18), 'thump': (thump, .45),
      'tap': (tap, .6), 'pop': (pop, .45), 'step': (step, .16), 'creak': (creak, .14), 'unroll': (unroll, .22),
      'pass': (whoosh, .15), 'blink': (blink, .3), 'eye': (eye, .22), 'shift': (shift, .4), 'flash': (flash, .35)}
for c in data['cues']:
    fn, g = FX[c['type']]
    put(mix, fn(), c['t'], g * rng.uniform(.85, 1.1), pan=rng.uniform(-.35, .35))
    if c['type'] == 'rip':
        put(mix, swell(), c['t'] - 1.6, .16)

mix /= max(1e-9, np.abs(mix).max()) / .85
out = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('sound', TOTAL, 's')
