# Builds the soundtrack for "Torn Paper Lucid" from the cues the film exports.
# The music follows the film's trip curve: a calm plucked lullaby at first, then the tape starts
# to wow and drift, a slow heartbeat comes in, detuned drones and a high glassy shimmer swell,
# reversed swells rise into each tear, and it all settles to one clear note at the end.
# Foley: footsteps land on each foot contact of the walk (with fainter echo steps for his ghosts),
# cars pass with engine doppler, tyre hiss and travelling stereo, plus a horn, bus air brakes, tram
# rail clacks and bell, wing beats, leaves and a city traffic bed under the street scenes.
# Between scenes a reversed swell pulls you in, air rushes through the tunnel and a low boom and open
# chord land as the next scene opens. Effects (slaps, swishes, taps, eyes, glitches, flashes...) sit on the cues.
# usage: python3 sound.py cues.json out.wav      (numpy only)
import sys, json, wave, numpy as np

# MUSIC = False leaves out the score (lullaby, drones, shimmer, closing note and the chords in the
# tunnel arrivals) and keeps only sound effects, foley and ambience. Set it to True to bring the music back.
MUSIC = False

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

mix = np.zeros((N, 2))
if MUSIC:
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
def glint():                                   # a light catching the sunglasses
    x = ts(.6); return sum(np.sin(2 * np.pi * midi(m) * x) for m in (93, 100)) * np.exp(-x * 7) * .4 * np.minimum(1, x / .01)
def riser():                                   # a reversed swell that pulls you toward the tunnel
    d = 1.5; x = ts(d)
    s = sum(np.sin(2 * np.pi * midi(m) * x * (1 + .04 * x)) for m in (62, 69, 74, 81)) / 4
    return ((s * .5 if MUSIC else 0) + filt(noise(d), 800, 9000) * .5) * (x / d) ** 2.5
def tunnel():                                  # rushing air and a falling doppler tone through the tunnel
    d = 1.9; x = ts(d); n = filt(noise(d), 150, 3500)
    f = 520 * np.exp(-x * 1.2) + 60
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * .35
    return (n + tone) * np.sin(np.pi * np.clip(x / d, 0, 1)) ** 1.5 * (1 + .5 * np.sin(2 * np.pi * 9 * x))
def arrive():                                  # a soft low boom and an open chord as the next scene opens
    x = ts(2.6)
    boom = np.sin(2 * np.pi * np.cumsum(42 + 30 * np.exp(-x * 6)) / SR) * np.exp(-x * 2.2)
    chord = sum(piano(midi(m), 2.6) for m in (62, 69, 74, 78)) / 4
    return boom * .8 + (chord * .6 if MUSIC else 0)
def flash():
    x = ts(.25); return (filt(noise(.25), 3000, 14000) + np.sin(2 * np.pi * 2200 * x) * .3) * np.exp(-x * 14)


# ---------- foley: footsteps, cars and the things that pass ----------
def put_move(buf, sig, at, gain, p0, p1):
    """place a sound that travels across the stereo field from pan p0 to p1"""
    i = int(at * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]; pan = np.linspace(p0, p1, len(sig))
    buf[i:i + len(sig), 0] += sig * gain * np.clip(1 - pan, 0, 1)
    buf[i:i + len(sig), 1] += sig * gain * np.clip(1 + pan, 0, 1)
def street_echo(x, d1=.045, d2=.11, g=.28):
    out = np.concatenate([x, np.zeros(int(.2 * SR))])
    for d, gg in ((d1, g), (d2, g * .55)):
        k = int(d * SR); out[k:k + len(x)] += filt(x, 200, 3000) * gg
    return out
def footstep(foot=0, soft=1.0):
    """a leather heel on pavement: heel strike, toe roll and a little grit"""
    rate = rng.uniform(.9, 1.1) * (1.04 if foot else .97)
    x = ts(.25)
    heel = filt(noise(.25), 120, 3200) * np.exp(-x * 75 * rate) + np.sin(2 * np.pi * 85 * rate * x) * np.exp(-x * 55) * .7
    toe = np.zeros(len(x)); k = int(rng.uniform(.05, .07) * SR)
    t2 = x[: len(x) - k]; toe[k:] = filt(rng.uniform(-1, 1, len(t2)), 500, 6500) * np.exp(-t2 * 110) * .45
    grit = filt(noise(.25), 2500, 9000) * np.exp(-x * 30) * .12
    return street_echo((heel + toe + grit) * soft)
def engine(d, f0, harm, tp, w, dopp=.07, rumble=0):
    x = ts(d); env = 1 / (1 + ((x - tp) / w) ** 2)
    ratio = 1 + dopp * np.tanh(-(x - tp) / (w * .6))           # higher coming in, lower going away
    ph = 2 * np.pi * np.cumsum(f0 * ratio) / SR
    s = sum(a * np.sin(h * ph + rng.uniform(0, 6)) for h, a in harm)
    s *= 1 + .35 * np.sin(ph * .5)                              # cylinders firing
    if rumble: s *= 1 + rumble * np.sin(2 * np.pi * 11 * x)
    hiss = filt(noise(d), 600, 7000) * .6
    far = filt(s, None, 400)
    return (s * env + far * (1 - env) * .25 + hiss * env ** 1.5) * np.minimum(1, x / .3) * np.minimum(1, (d - x) / .3)
def car_sound(kind, d):
    tp = d / 2; x = ts(d)
    if kind == 'taxi': return engine(d, 42, [(1, 1), (2, .6), (3, .35), (4, .2), (6, .1)], tp, .38) * .9
    if kind == 'bus':
        s = engine(d, 27, [(1, 1), (2, .8), (3, .5), (5, .3), (7, .15)], tp, .6, dopp=.05, rumble=.5) * 1.1
        k = int((tp + .5) * SR); air = filt(noise(.7), 2500, 9000) * np.exp(-ts(.7) * 4) * .5   # air brakes
        s[k:k + len(air)] += air[: len(s) - k]; return s
    if kind == 'tram':
        s = engine(d, 600, [(1, .25), (2, .1)], tp, .55, dopp=.04) * .4
        for c in np.arange(.1, d - .2, .42):                                                   # wheels over rail joints
            for o in (0, .09):
                k = int((c + o) * SR); cl = filt(noise(.05), 800, 6000) * np.exp(-ts(.05) * 90)
                s[k:k + len(cl)] += cl * (1 / (1 + ((c - tp) / .6) ** 2)) * .9
        for o in (tp - .7, tp - .45):                                                          # the bell, twice
            k = int(o * SR); b = ts(1.2)
            bell = (np.sin(2 * np.pi * 1320 * b) + .5 * np.sin(2 * np.pi * 1320 * 2.76 * b)) * np.exp(-b * 4)
            s[k:k + len(bell)] += bell[: len(s) - k] * .35
        return s
    if kind == 'bird':
        s = np.zeros(len(x))
        for c in np.arange(tp - .5, tp + .5, .11):                                             # wing beats
            k = int(c * SR); fl = filt(noise(.06), 300, 3000) * np.sin(np.pi * ts(.06) / .06)
            s[k:k + len(fl)] += fl * .5
        k = int((tp - .2) * SR); ch = ts(.18)
        s[k:k + len(ch)] += np.sin(2 * np.pi * np.cumsum(3200 + 1800 * np.sin(2 * np.pi * 14 * ch)) / SR) * np.exp(-ch * 9) * .3
        return s
    if kind == 'umbrella':
        e = 1 / (1 + ((x - tp) / .3) ** 2); return filt(noise(d), 200, 2500) * e * (1 + .6 * np.sin(2 * np.pi * 6 * x)) * .7
    if kind == 'tree':
        e = 1 / (1 + ((x - tp) / .45) ** 2); am = np.convolve(rng.random(len(x)) < .004, np.ones(600) / 60, 'same')
        return filt(noise(d), 1500, 9000) * e * (.3 + am) * .7
    return np.zeros(len(x))
def horn():
    x = ts(.42); tone = np.sign(np.sin(2 * np.pi * 415 * x)) * .5 + np.sign(np.sin(2 * np.pi * 523 * x)) * .5
    gate = ((x < .14) | ((x > .2) & (x < .38))).astype(float)
    return filt(tone, 300, 2500) * gate * .5
def city(d):
    x = ts(d); s = filt(noise(d), 40, 260) * .9 + filt(noise(d), 300, 1800) * .25
    s *= .7 + .3 * np.sin(2 * np.pi * .13 * x + 1)
    return s * np.minimum(1, x / 1.2) * np.minimum(1, (d - x) / 1.2)

for c in data['cues']:
    ty = c['type']
    if ty in ('step', 'ghoststep', 'farstep'):
        sig = footstep(c.get('foot', 0), 1.0)
        if ty == 'ghoststep': sig = street_echo(filt(sig, 150, 2500), .09, .2, .5)
        if ty == 'farstep': sig = filt(sig, 150, 1800)
        put(mix, sig, c['t'] - .005, 1.5 * c.get('g', 1), pan=c.get('pan', 0) + (.12 if c.get('foot') else -.12))
    elif ty == 'car':
        d = c.get('d', 2.6); put_move(mix, car_sound(c['kind'], d), c['t'] - d / 2, .5, c.get('from', 1), c.get('to', -1))
    elif ty == 'horn': put(mix, horn(), c['t'], .35, pan=c.get('pan', 0))
    elif ty == 'city': put(mix, city(c['d']), c['t'], .12 * c.get('g', 1))

FX = {'slap': (slap, .3), 'rip': (rip, .55), 'whoosh': (whoosh, .3), 'swish': (swish, .18), 'thump': (thump, .45),
      'tap': (tap, .6), 'pop': (pop, .45), 'creak': (creak, .14), 'unroll': (unroll, .22),
      'pass': (whoosh, .15), 'blink': (blink, .3), 'eye': (eye, .22), 'shift': (shift, .4), 'flash': (flash, .35), 'glint': (glint, .14), 'riser': (riser, .18), 'tunnel': (tunnel, .42), 'arrive': (arrive, .4)}
for c in data['cues']:
    if c['type'] not in FX: continue
    fn, g = FX[c['type']]
    put(mix, fn(), c['t'], g * rng.uniform(.85, 1.1), pan=rng.uniform(-.35, .35))

mix /= max(1e-9, np.abs(mix).max()) / .85
out = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('sound', TOTAL, 's')
