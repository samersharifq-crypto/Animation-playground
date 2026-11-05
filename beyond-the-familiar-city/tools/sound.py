"""Builds the soundtrack for «ما وراء المألوف» (city) from the film's cue list.

usage: python3 sound.py events.json out.wav

The animation exports its cues (footsteps synced to the walk cycle, cars crossing
frame, page turns) as JSON; everything here is synthesised with numpy:
city ambience that hushes in the courtyard, footsteps, passing cars, a subway
train under the grate, leaves, paper, and a sparse piano that leaves room for
narration.
"""
import json, sys, wave
import numpy as np

SR = 48000
DUR = 65.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR


def band(x, lo=None, hi=None, order=2):
    """Zero-phase band filter applied in the frequency domain."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    h = np.ones_like(f)
    if hi:
        h *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        h *= 1 - 1 / np.sqrt(1 + (f / max(lo, 1e-3)) ** (2 * order))
    return np.fft.irfft(X * h, len(x))


def env(points):
    """Piecewise-linear envelope over the whole film: [(time, value), ...]."""
    ts, vs = zip(*points)
    return np.interp(t_all, ts, vs)


def place(buf, sig, at, pan=0.0, gain=1.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(sig)] += sig * gain * l
    buf[1, i:i + len(sig)] += sig * gain * r


def reverb(x, secs=1.8, wet=0.25):
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * secs / 6))
    ir = band(ir, 200, 6000)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[: len(x)]
    return x * (1 - wet) + y * wet


def noise(n):
    return rng.standard_normal(n)


out = np.zeros((2, N))
events = json.load(open(sys.argv[1]))

# --- city ambience: rumble + air; hushes in the courtyard, returns softer after ---
city = env([(0, 0), (1.2, 1), (29.6, 1), (31, .2), (40, .24), (41, .3), (50, .32), (54, .55), (60, .6), (63.5, .12), (65, 0)])
rumble = band(np.cumsum(noise(N)) * .02, 25, 260)
rumble /= np.abs(rumble).max()
air = band(noise(N), 400, 2600) * .18
air2 = band(noise(N), 400, 2600) * .18
out[0] += (rumble * .5 + air) * city * .55
out[1] += (np.roll(rumble, 900) * .5 + air2) * city * .55

# --- the subway train under the grate (scene 2) ---
tr = env([(11.0, 0), (12.6, 1), (14.8, 1), (16.8, 0)])
train = band(noise(N), 30, 180) * 1.4 + band(noise(N), 300, 900) * .25
clack = np.zeros(N)
for k in np.arange(11.6, 16.6, .16):
    i = int(k * SR); m = int(.05 * SR)
    clack[i:i + m] += np.exp(-np.arange(m) / (SR * .012)) * np.sin(2 * np.pi * 70 * np.arange(m) / SR)
out += (train * .35 + clack * .5) * tr * .5

# --- leaves rustling: faint at the passage, clear in the courtyard ---
lv = env([(20, 0), (21, .25), (29.5, .35), (31, .9), (39.5, .9), (40.5, .1), (54, .1), (56, .3), (60, .25), (62, 0)])
gust = band(noise(N), .05, .6, 1)
gust = (gust - gust.min()) / (gust.max() - gust.min())
leaves = band(noise(N), 2200, 9000) * gust ** 2
out[0] += leaves * lv * .22
out[1] += np.roll(leaves, 4000) * lv * .22

# --- footsteps synced to the walk cycle ---
def step_sound(bright=1.0):
    m = int(.14 * SR); tt = np.arange(m) / SR
    thump = np.sin(2 * np.pi * 85 * tt) * np.exp(-tt / .022)
    scuff = band(noise(m), 600, 3500) * np.exp(-tt / .03) * .5 * bright
    return thump * .9 + scuff

for e in events:
    if e['type'] == 'step':
        courtyard = e['scene'] == 3
        g = e['g'] * (.32 if courtyard else .22)
        place(out, step_sound(1.4 if courtyard else 1.0) * (1 + rng.uniform(-.15, .15)), e['t'], pan=rng.uniform(-.15, .15), gain=g)

# --- cars passing on the avenue (scene 2) ---
for e in events:
    if e['type'] != 'car':
        continue
    m = int(2.4 * SR); tt = np.arange(m) / SR - 1.2
    sh = np.exp(-(tt / .55) ** 2)
    sweep = band(noise(m), 120, 1800) * sh + band(noise(m), 40, 140) * sh * .8
    pan = np.clip(tt * e['dir'] * 1.2, -1, 1)
    i0 = int((e['t'] - 1.2) * SR)
    if i0 < 0:
        sweep = sweep[-i0:]; pan = pan[-i0:]; i0 = 0
    n = min(len(sweep), N - i0)
    g = .32 * e['near']
    out[0, i0:i0 + n] += sweep[:n] * g * np.cos((pan[:n] + 1) * np.pi / 4)
    out[1, i0:i0 + n] += sweep[:n] * g * np.sin((pan[:n] + 1) * np.pi / 4)

# --- paper: page turns, the note lifted, the book closing ---
def swish(d=.4, lo=1200, hi=7000):
    m = int(d * SR); tt = np.arange(m) / m
    return band(noise(m), lo, hi) * np.sin(np.pi * tt) ** 1.5

for e in events:
    if e['type'] == 'page':
        place(out, swish(.45), e['t'], pan=-.2, gain=.32)
    if e['type'] == 'note':
        place(out, swish(.7, 2500, 9000), e['t'], pan=.2, gain=.16)
    if e['type'] == 'close':
        place(out, swish(.35), e['t'], gain=.3)
        m = int(.2 * SR); tt = np.arange(m) / SR
        place(out, np.sin(2 * np.pi * 70 * tt) * np.exp(-tt / .04), e['t'] + .3, gain=.5)

# --- a few small courtyard sounds, now audible: birds ---
for at, f0, pan in [(32.4, 3400, -.4), (34.9, 4100, .5), (37.6, 3700, -.2)]:
    for k in range(3):
        m = int(.09 * SR); tt = np.arange(m) / SR
        f = f0 + 900 * np.sin(np.pi * tt / tt[-1])
        place(out, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]), at + k * .14, pan=pan, gain=.05)

# --- sparse piano (leaves the voice room) ---
NOTE = {'A3': 220.0, 'B3': 246.94, 'D3': 146.83, 'D4': 293.66, 'E4': 329.63, 'F#4': 369.99, 'A4': 440.0, 'B4': 493.88, 'D5': 587.33}
def piano(f, d=4.5):
    m = int(d * SR); tt = np.arange(m) / SR
    s = sum(a * np.sin(2 * np.pi * f * k * tt) * np.exp(-tt / (1.6 / k ** .7)) for k, a in [(1, 1), (2, .45), (3, .2), (4, .08)])
    return s * np.minimum(1, tt / .006)

mus = np.zeros(N)
seq = [(1.5, 'D4'), (4.2, 'A4'), (7.0, 'F#4'), (9.8, 'E4'), (12.6, 'D4'), (15.4, 'A3'), (18.2, 'B3'), (21.0, 'D4'), (23.6, 'E4'),
       (26.2, 'F#4'), (28.8, 'A4'), (31.5, 'D5'), (33.2, 'A4'), (35.0, 'B4'), (36.8, 'F#4'), (38.6, 'E4'), (41.2, 'D4'), (43.8, 'B3'),
       (46.4, 'A3'), (49.0, 'D4'), (51.6, 'F#4'), (54.2, 'A4'), (56.8, 'B4'), (59.4, 'A4')]
for at, n in seq:
    p = piano(NOTE[n]); i = int(at * SR); mus[i:i + len(p)] += p[: N - i] * .9
for n in ['D3', 'A3', 'F#4', 'D5']:
    p = piano(NOTE[n], 5.0); i = int(61.6 * SR); mus[i:i + len(p)] += p[: N - i] * .7
pad = (np.sin(2 * np.pi * 73.42 * t_all) + .5 * np.sin(2 * np.pi * 110 * t_all)) * env([(29, 0), (32, .18), (39, .18), (42, 0), (60, 0), (61.6, .15), (65, 0)])
mus = reverb(mus + pad, 2.2, .35)
out[0] += mus * .07
out[1] += np.roll(mus, 240) * .07

out = reverb(out[0], 1.2, .12), reverb(out[1], 1.2, .12)
out = np.vstack(out)
fade = env([(0, 0), (.6, 1), (64.0, 1), (65, 0)])
out *= fade
out *= .9 / np.abs(out).max()
pcm = (out.T * 32767).astype('<i2')
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', sys.argv[2], f'{DUR:.0f}s')
