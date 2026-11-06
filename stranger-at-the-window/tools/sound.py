# Builds the soundtrack for "The Stranger at the Window" from the cues the film exports:
# spy-jazz bass and brushes for the title, café piano, a dread drone and heartbeat while the
# stranger watches, a ticking clock for the evidence board, a fast comic chase, tiptoe plucks
# for the newspaper disguise, a sad trombone for the twist, and a jazz resolve at the end.
# Effects (rips, stamps, whistles, boings, shutters, handcuffs...) sit on the film's cues.
# usage: python3 sound.py cues.json out.wav      (numpy only)
import sys, json, wave, numpy as np

cues = json.load(open(sys.argv[1]))
SR, TOTAL = 44100, float(cues['total'])
N = int(SR * TOTAL)
rng = np.random.default_rng(707)
mix = np.zeros((N, 2))
SC = cues['scenes']

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]
    mix[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    mix[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))

def filt(x, lo=None, hi=None):
    """FFT band filter: keep lo..hi Hz with soft edges."""
    n = len(x); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); g = np.ones_like(f)
    if hi: g *= 1 / (1 + (f / hi) ** 4)
    if lo: g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(X * g, n)

def ts(d): return np.arange(int(d * SR)) / SR
def env(n, a, d):
    e = np.ones(n); ai = max(1, int(a * SR)); e[:ai] = np.linspace(0, 1, ai)
    return e * np.exp(-np.arange(n) / SR / d)
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def noise(d): return rng.uniform(-1, 1, int(d * SR))

# ---------------- instruments ----------------
def pluck(f, d=.5, dec=.18, bright=1.0):          # upright bass / pizzicato
    x = ts(d); s = np.sin(2 * np.pi * f * x) + .5 * bright * np.sin(4 * np.pi * f * x) + .2 * bright * np.sin(6 * np.pi * f * x)
    return s * env(len(x), .004, dec)
def piano(f, d=1.6, dec=.9):
    x = ts(d); s = sum(a * np.sin(2 * np.pi * f * h * x) * np.exp(-x * h * .6) for h, a in [(1, 1), (2, .5), (3, .25), (4, .12), (5, .06)])
    return s * env(len(x), .003, dec)
def xylo(f, d=.35):
    x = ts(d); s = np.sin(2 * np.pi * f * x) + .35 * np.sin(2 * np.pi * f * 3.9 * x) * np.exp(-x * 30)
    return s * env(len(x), .001, .08)
def brass(fs, d=.5, bright=1.0):
    x = ts(d); s = np.zeros(len(x))
    for f in fs:
        ph = 2 * np.pi * f * x + .002 * np.sin(2 * np.pi * 5.5 * x) * f
        s += sum(np.sin(ph * h) / h ** (1.3 / bright) for h in range(1, 8))
    e = np.minimum(1, x / .03) * np.minimum(1, (d - x) / .06)
    return s * e / len(fs) * .5
def pad(fs, d, att=.8):
    x = ts(d); s = sum(np.sin(2 * np.pi * f * x + .3 * np.sin(2 * np.pi * .25 * x)) + .25 * np.sin(2 * np.pi * f * 2.004 * x) for f in fs)
    return s * np.minimum(1, x / att) * np.minimum(1, (d - x) / att) / len(fs)
def kick(): x = ts(.3); return np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-x * 30)) / SR) * np.exp(-x * 12)
def snare(): x = ts(.2); return filt(noise(.2), 900, 7000) * np.exp(-x * 22) * 1.3 + np.sin(2 * np.pi * 190 * x) * np.exp(-x * 30) * .5
_BR = filt(noise(.25), 3000, 12000)
def brush(d=.12): x = ts(d); return _BR[:len(x)] * np.exp(-x * 30)
def hat(): x = ts(.05); return _BR[:len(x)] * np.exp(-x * 90)

# ---------------- music ----------------
end_t = SC[8]
# 1) title: spy-jazz bass line in D minor with brushes (0 .. café)
bpm = 112; b = 60 / bpm
line = [50, 50, 53, 55, 56, 55, 53, 50]
tt = .4
while tt < SC[1] - .2:
    for k, m in enumerate(line):
        at = tt + k * b / 2
        if at >= SC[1] - .2: break
        add(pluck(midi(m - 12), .45, .16), at, .5)
        add(brush(), at, .09 if k % 2 else .05, pan=.3)
    tt += 4 * b
add(brass([midi(62), midi(65), midi(69), midi(72)], 1.2, .8), 4.9, .12)   # stab under the title
# 2) café: soft jazz piano until the first peek, then the dread
cafe0, dread0, dread1 = SC[1], cues['dread'][0], cues['dread'][1]
chords = [[50, 53, 57, 60, 64], [55, 59, 62, 65, 69], [48, 52, 55, 59, 62], [57, 61, 64, 67]]
tt = cafe0 + .5; ci = 0
while tt < dread0:
    ch = chords[ci % 4]
    for j, m in enumerate(ch): add(piano(midi(m), 2.2, 1.1), tt + j * .03, .06, pan=-.2 + j * .1)
    add(pluck(midi(ch[0] - 24), .9, .4), tt, .35)
    tt += 2.2; ci += 1
# dread: low drone + heartbeat from the first peek to the end of the board
d = dread1 - dread0; x = ts(d)
drone = (np.sin(2 * np.pi * 36.7 * x) + .5 * np.sin(2 * np.pi * 55.0 * x * 1.004) + .25 * np.sin(2 * np.pi * 77.8 * x)) * np.minimum(1, x / 1.5) * np.minimum(1, (d - x) / .6)
add(drone, dread0, .18)
hb = SC[2] - 1.0
k = dread0 + .4
while k < dread1 - .3:
    rate = .9 if k < SC[1] + 8.9 else .7
    add(kick(), k, .35); add(kick(), k + .22, .22)
    k += rate
# freeze-frame: sustained cluster
add(pad([midi(50), midi(51), midi(56), midi(57)], 2.6, .05), cues['freeze'][0], .14)
# 3) board: ticking clock + bass pulse
tk = SC[2] + .2
while tk < SC[3] - .4:
    x = ts(.03); add(filt(noise(.03), 2000, 9000) * np.exp(-x * 160), tk, .25, pan=-.4 if int(tk * 2) % 2 else .4); tk += .5
for k2 in range(int((SC[3] - SC[2]) / 1.0)):
    add(pluck(midi(38), .8, .35), SC[2] + k2 * 1.0 + .1, .4)
add(brass([midi(50), midi(53), midi(56)], .6), SC[2] + 7.3, .18)    # WANTED
add(brass([midi(57), midi(62), midi(66)], .8), SC[2] + 8.1, .16)    # I'm on it (major lift)
# 4) the chase: fast comic oom-pah with a running xylophone melody
c0, c1 = cues['chase']
hush0, hush1 = cues.get('hush', [0, 0])
bpm = 168; b = 60 / bpm
mel = [62, 64, 65, 67, 69, 67, 65, 64, 62, 65, 69, 74, 73, 69, 65, 61,
       62, 64, 65, 67, 69, 70, 69, 67, 65, 67, 69, 65, 62, 61, 62, 0]
bass = [38, 45, 38, 45, 38, 45, 37, 45, 34, 41, 34, 41, 33, 40, 33, 45]
k = 0; tt = c0
while tt < c1:
    if hush0 <= tt < hush1: tt += b / 2; k += 1; continue
    if k % 2 == 0:
        add(pluck(midi(bass[(k // 2) % 16]), .3, .1, .6), tt, .5)
        add(kick(), tt, .25)
    else:
        add(pluck(midi(bass[(k // 2) % 16] + 12) * 1.0, .2, .06), tt, .2)
        add(snare(), tt, .16, pan=.2)
    m = mel[k % 32]
    if m: add(xylo(midi(m + 12)), tt, .2, pan=-.25)
    add(hat(), tt + b / 4, .07, pan=.35)
    tt += b / 2; k += 1
# tiptoe plucks under the disguise
for i, m in enumerate([62, 0, 65, 0, 62, 0, 69, 68, 67, 0, 62, 0]):
    if m: add(pluck(midi(m + 12), .25, .05, .3), hush0 + .15 + i * .17, .3)
# stairs: the chase keeps going but the melody climbs; at the top, a hanging tremolo
for i in range(14):
    add(xylo(midi(62 + i * 2)), SC[5] + .2 + i * .28, .2, pan=.3)
tr0 = SC[5] + 4.3
x = ts(1.6); add(np.sin(2 * np.pi * midi(74) * x) * (0.6 + .4 * np.sin(2 * np.pi * 14 * x)) * np.minimum(1, x / .1) * np.minimum(1, (1.6 - x) / .2), tr0, .08)
# 5) caught: dangling xylophone flurries, then a GOTCHA brass chord (D major)
for i in range(16):
    add(xylo(midi([74, 77, 81, 77][i % 4])), SC[6] + 1.9 + i * .12, .14, pan=(-.3 if i % 2 else .3))
add(brass([midi(50), midi(54), midi(57), midi(62)], 1.6, 1.2), SC[6] + 4.9, .2)
add(kick(), SC[6] + 4.9, .5)
# 6) mugshot: stab on CAUGHT, sad trombone on the twist
add(brass([midi(50), midi(53), midi(56), midi(59)], .7), SC[7] + 1.6, .2)
def trombone(f, d, vib=0):
    x = ts(d); fm = f * (1 + vib * .02 * np.sin(2 * np.pi * 6 * x) * np.minimum(1, x / .3))
    ph = 2 * np.pi * np.cumsum(fm) / SR; s = sum(np.sin(ph * h) / h ** 1.1 for h in range(1, 9))
    return filt(s * np.minimum(1, x / .04) * np.minimum(1, (d - x) / .1), None, 1800) * .4
t0 = cues['trombone'][0]
for i, (m, dd) in enumerate([(46, .42), (45, .42), (44, .42), (43, 1.4)]):
    add(trombone(midi(m), dd, vib=1 if i == 3 else 0), t0 + i * .46, .5)
add(pluck(midi(31), 1.2, .6), t0 + 1.38, .35)
# closing jazz chord + final sting
for j, m in enumerate([50, 57, 60, 64, 65, 69]): add(piano(midi(m), 4.0, 2.0), end_t + .3 + j * .05, .07, pan=-.25 + j * .1)
add(pad([midi(50), midi(57), midi(64), midi(65)], 4.6, 1.0), end_t + .3, .05)
add(brass([midi(50), midi(53), midi(56), midi(61)], .9), end_t + 3.9, .15)
add(pluck(midi(38), 1.2, .6), end_t + 3.9, .4)

# ---------------- effects ----------------
def whoosh(dd=.6):
    x = ts(dd); return filt(noise(dd), 300, 2600) * np.sin(np.pi * x / dd) ** 2 * 2.0
def rip(dd=.5):
    x = ts(dd); s = filt(noise(dd), 1200, 9000)
    gate = (rng.uniform(0, 1, len(x)) > .55).astype(float); gate = filt(gate, None, 400)
    return s * gate * 3.0 * np.minimum(1, x / .02) * np.exp(-x * 2.5)
def pop():
    x = ts(.08); return (np.sin(2 * np.pi * 420 * x * (1 - x * 3)) * .6 + filt(noise(.08), 800, 5000) * .5) * np.exp(-x * 60)
def click():
    x = ts(.025); return filt(noise(.025), 1500, 9000) * np.exp(-x * 220)
def thud():
    x = ts(.4); return np.sin(2 * np.pi * np.cumsum(50 + 80 * np.exp(-x * 25)) / SR) * np.exp(-x * 9) + filt(noise(.4), 100, 1200) * np.exp(-x * 30) * .9
def bell():
    x = ts(1.0); return (np.sin(2 * np.pi * 2093 * x) + .4 * np.sin(2 * np.pi * 5230 * x)) * np.exp(-x * 4)
def boing(dd=.6):
    x = ts(dd); f = 180 + 260 * x / dd + 40 * np.sin(2 * np.pi * 18 * x)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 4)
def zip_(dd=.35):
    x = ts(dd); f = 300 + 2600 * (x / dd) ** 2
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * .5 * np.exp(-x * 3) + filt(noise(dd), 2000, 8000) * np.sin(np.pi * x / dd) * .8
def whistle(dd=.34):
    x = ts(dd); f = 2700 + 120 * np.sign(np.sin(2 * np.pi * 28 * x))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, x / .01) * np.minimum(1, (dd - x) / .03) + filt(noise(dd), 2500, 6000) * .2
def slide(dd=.9, up=True):
    x = ts(dd); f = (400 + 1400 * (x / dd)) if up else (1500 - 1200 * (x / dd))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, x / .02) * np.minimum(1, (dd - x) / .1) * .7
def skid(dd=.45):
    x = ts(dd); return filt(noise(dd), 1800, 4000) * np.sin(np.pi * x / dd) * 1.8 + np.sin(2 * np.pi * (900 - 400 * x) * x) * .2
def shutter():
    x = ts(.2); s = filt(noise(.2), 1200, 9000)
    return s * (np.exp(-x * 80) + np.exp(-np.maximum(0, x - .07) * 80) * (x > .07)) * 1.2 + np.sin(2 * np.pi * 3000 * x) * np.exp(-x * 40) * .15
def cuffclick():
    out = np.zeros(int(.35 * SR))
    for i, tt2 in enumerate([0, .06, .11, .15, .18]):
        c = filt(noise(.03), 2500, 10000) * np.exp(-ts(.03) * 160) * (1.4 if i == 4 else .7)
        j = int(tt2 * SR); out[j:j + len(c)] += c[:len(out) - j]
    return out
def chime():
    out = np.zeros(int(1.4 * SR))
    for i, m in enumerate([84, 88, 91, 96]):
        s = xylo(midi(m), .9); j = int(i * .07 * SR); out[j:j + len(s)] += s[:len(out) - j]
    return out
def step():
    x = ts(.09); return (np.sin(2 * np.pi * 110 * x) * .7 + filt(noise(.09), 200, 2500) * .6) * np.exp(-x * 45)
def sting():
    x = ts(1.6); f = [midi(m) for m in [62, 63, 68, 69]]
    s = sum(np.sin(2 * np.pi * ff * x) + .4 * np.sin(4 * np.pi * ff * x) for ff in f) / 4
    return s * np.minimum(1, x / .01) * np.exp(-x * 1.6) + filt(noise(1.6), 2000, 8000) * np.exp(-x * 6) * .3
def sip():
    x = ts(.5); return filt(noise(.5), 600, 3000) * (np.sin(np.pi * x / .5) ** 3) * (0.6 + .4 * np.sin(2 * np.pi * 9 * x)) * .8

W = whoosh()
for a in cues['whoosh']: add(W, a - .25, .3)
for a in cues['rip']: add(rip(), a - .05, .35, pan=.2)
PO = pop()
for a in cues['pops']: add(PO, a, .22, pan=float(rng.uniform(-.4, .4)))
CL = click()
for a, dd in cues['type']:
    k = 0.0
    while k < dd:
        add(CL, a + k, .3, pan=float(rng.uniform(-.2, .2))); k += .045 + rng.uniform(0, .04)
    add(bell(), a + dd + .05, .08)
ST = sting()
for a in cues['sting']: add(ST, a, .22)
for a in cues['peekDuck']: add(slide(.25, False), a, .22); add(PO, a, .3)
for a in cues['freeze']:
    add(thud(), a, .6); add(shutter(), a, .4)
for a in cues['sip']: add(sip(), a, .3)
TH = thud()
for a in cues['stamp']: add(TH, a, .7)
for a in cues['bam']: add(TH, a, .8); add(filt(noise(.6), 200, 6000) * np.exp(-ts(.6) * 7), a, .5)
for a in cues['boing']: add(boing(), a, .3)
for a in cues['zip']: add(zip_(), a, .35)
for a in cues['whistle']: add(whistle(), a, .14, pan=-.4)
for a in cues['slip']: add(slide(.9, True), a, .3); add(filt(noise(.3), 400, 3000) * np.exp(-ts(.3) * 8), a, .3)
for a in cues['crash']: add(TH, a, .8); add(filt(noise(1.0), 300, 8000) * np.exp(-ts(1.0) * 4), a, .35)
for a in cues['skid']: add(skid(), a, .35)
for a in cues['moon']:
    for i in range(4): add(pluck(midi(74 - i * 2), .15, .04), a + i * .14, .2)
for a in cues['click']: add(cuffclick(), a, .6)
for a in cues['shutter']: add(shutter(), a, .45)
for a in cues['chime']: add(chime(), a, .3, pan=.4)
def honk(dd=.22):
    x = ts(dd); s = np.sign(np.sin(2 * np.pi * 410 * x)) * .5 + np.sign(np.sin(2 * np.pi * 515 * x)) * .5
    return filt(s, 200, 2500) * np.minimum(1, x / .01) * np.minimum(1, (dd - x) / .02)
for a in cues.get('honk', []): add(honk(), a, .22, pan=.3)
def carby(dd=1.6):
    x = ts(dd); s = filt(noise(dd), 60, 600) * 1.5 + np.sin(2 * np.pi * np.cumsum(70 + 20 * np.sin(np.pi * x / dd)) / SR) * .4
    return s * np.sin(np.pi * x / dd) ** 2
for i, a in enumerate(cues.get('cars', [])): add(carby(), a, .3, pan=(-.5 if i % 2 else .5))
for a in cues.get('beep', []): x = ts(.18); add(np.sin(2 * np.pi * 1000 * x) * np.minimum(1, (0.18 - x) / .02), a, .12)
def siren(dd):
    x = ts(dd); f = 950 + 350 * np.sign(np.sin(2 * np.pi * .9 * x))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * .35 * np.minimum(1, x / .4) * np.minimum(1, (dd - x) / .6)
sr = cues.get('siren')
if sr: add(filt(siren(sr[1] - sr[0]), 300, 4000), sr[0], .1, pan=-.3)
def screech(dd=.55):
    x = ts(dd); f = 2400 - 600 * x / dd
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .4 + filt(noise(dd), 1500, 5000) * .9) * np.sin(np.pi * x / dd) ** .5
for a in cues.get('screech', []): add(screech(), a, .25)
STP = step()
for a, b2 in cues['steps']:
    k = a; i = 0
    while k < b2:
        add(STP, k, .16, pan=-.2 if i % 2 else .2); k += .17; i += 1

# ---------------- room tone ----------------
hiss = filt(rng.uniform(-1, 1, N), 200, 6000) * .012
cr = np.zeros(N); idx = rng.integers(0, N, int(TOTAL * 18)); cr[idx] = rng.uniform(-1, 1, len(idx)) * rng.uniform(.2, 1, len(idx))
cr = filt(cr, 900, None) * .25
bed = hiss + cr
mix[:, 0] += bed; mix[:, 1] += bed

t = np.arange(N) / SR
fade = np.clip((TOTAL - t) / 1.2, 0, 1) * np.clip(t / .3, 0, 1)
mix *= fade[:, None]
mix = np.tanh(mix / max(1e-6, np.abs(mix).max()) * 1.4) * .9
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
