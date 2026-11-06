# Builds the soundtrack: vinyl crackle, a slow retro piano/pad progression, and
# whooshes, thuds, counter ticks and hits placed on the cues the film exports.
# usage: python3 sound.py cues.json out.wav
import sys, json, wave, numpy as np

cues = json.load(open(sys.argv[1]))
SR, TOTAL = 44100, float(cues['total'])
N = int(SR * TOTAL)
t = np.arange(N) / SR
rng = np.random.default_rng(1976)
mix = np.zeros((N, 2))

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    sig = sig[: N - i]
    mix[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    mix[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))

def lowpass(x, cut):
    a = 1 - np.exp(-2 * np.pi * cut / SR); y = np.empty_like(x); s = 0.0
    for k in range(len(x)): s += a * (x[k] - s); y[k] = s
    return y

def env(n, a, d):
    e = np.ones(n); ai = max(1, int(a * SR)); e[:ai] = np.linspace(0, 1, ai)
    return e * np.exp(-np.arange(n) / SR / d)

def piano(f, dur, d=1.2):
    n = int(dur * SR); x = np.arange(n) / SR
    s = sum(amp * np.sin(2 * np.pi * f * h * x) for h, amp in [(1, 1), (2, .45), (3, .2), (4, .1)])
    return s * env(n, .004, d)

def pad(fs, dur):
    n = int(dur * SR); x = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * x + .3 * np.sin(2 * np.pi * .3 * x)) + .3 * np.sin(2 * np.pi * f * 2.003 * x) for f in fs)
    e = np.minimum(1, x / .8) * np.minimum(1, (dur - x) / .8)
    return s * e / len(fs)

def midi(m): return 440 * 2 ** ((m - 69) / 12)

# ---- music: minor, wistful until the fall, then a lift in the major for the comeback
sc = cues['scenes']
fall, comeback = sc[7] + 3.6, sc[8]
beat = 60 / 84
minor = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]     # Am F C G
major = [[48, 52, 55], [55, 59, 62], [57, 60, 64], [53, 57, 60]]     # C G Am F
bar = 4 * beat
tt, ci = 1.2, 0
while tt < TOTAL - 1:
    if fall <= tt < comeback:
        tt = comeback; ci = 0; continue
    chord = (minor if tt < fall else major)[ci % 4]
    dur = min(bar, (fall if tt < fall else TOTAL) - tt)
    if dur < .4: tt += dur; continue
    add(pad([midi(m) for m in chord], dur + .4), tt, .05)
    add(piano(midi(chord[0] - 12), 2.5, 1.6), tt, .16)
    arp = [chord[0], chord[1], chord[2], chord[1] + 12 if tt >= comeback else chord[1]]
    for j in range(8):
        at = tt + j * beat / 2
        if at - tt >= dur: break
        add(piano(midi(arp[j % 4] + 12), 1.2, .6), at, .07, pan=(-.3 if j % 2 else .3))
    tt += bar; ci += 1
# low drone under the fall
dn = int((comeback - fall) * SR); x = np.arange(dn) / SR
drone = (np.sin(2 * np.pi * 41.2 * x) + .4 * np.sin(2 * np.pi * 61.7 * x)) * np.minimum(1, x / .3) * np.minimum(1, (comeback - fall - x) / .5)
add(drone, fall, .22)
# resolve on the last card
add(pad([midi(m) for m in [48, 55, 64, 67]], 5.5), TOTAL - 6.0, .08)
add(piano(midi(36), 5, 2.5), TOTAL - 6.0, .2)

# ---- effects
def whoosh(dur=.6):
    n = int(dur * SR); x = np.arange(n) / SR
    s = rng.uniform(-1, 1, n); s = lowpass(s, 2200) - lowpass(s, 300)
    return s * np.sin(np.pi * x / dur) ** 2 * 2.2
def thud():
    n = int(.35 * SR); x = np.arange(n) / SR
    f = 90 * np.exp(-x * 9) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 11) + lowpass(rng.uniform(-1, 1, n), 900) * np.exp(-x * 40) * .8
def tick():
    n = int(.03 * SR); return rng.uniform(-1, 1, n) * np.exp(-np.arange(n) / SR * 260)
def hit():
    n = int(1.6 * SR); x = np.arange(n) / SR
    s = np.sin(2 * np.pi * 55 * x) * np.exp(-x * 3) * 1.1 + lowpass(rng.uniform(-1, 1, n), 1600) * np.exp(-x * 7) * 1.2
    return s
W1 = whoosh()
for at in cues['whoosh']: add(W1, at - .3, .22)
TH = thud()
for at in cues['thud']: add(TH, at, .4)
TK = tick()
for at, d in cues['ticks']:
    k = 0.0
    while k < d: add(TK, at + k, .16); k += .04 + .1 * (k / d) ** 2
HT = hit()
for at in cues['hit']: add(HT, at, .5)
# lamp flicker buzz
for at in cues['flicker']:
    n = int(.5 * SR); x = np.arange(n) / SR
    add(np.sign(np.sin(2 * np.pi * 120 * x)) * (np.sin(x * 70) > -.2) * np.exp(-x * 5) * .3, at, .12)

# ---- vinyl crackle bed
cr = np.zeros(N)
idx = rng.integers(0, N, int(TOTAL * 26)); cr[idx] = rng.uniform(-1, 1, len(idx)) * rng.uniform(.2, 1, len(idx))
cr = cr - lowpass(cr, 600)
hiss = lowpass(rng.uniform(-1, 1, N), 5000) * .02
bed = (cr * .35 + hiss)
mix[:, 0] += bed; mix[:, 1] += bed

fade = np.clip((TOTAL - t) / 1.4, 0, 1) * np.clip(t / .3, 0, 1)
mix *= fade[:, None]
mix = np.tanh(mix / max(1e-6, np.abs(mix).max()) * 1.3) * .85
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
