"""Foley for «سمّوه البطل» (no music, as agreed): glass, scale, typewriter, machine, pouring
cigarettes, notifications, heartbeat, paper rips and stamps - all synthesized, all on the cues.

Writes foley.wav, and mix.wav = foley + narration/P1.* at 0 s + narration/P2.* at P2_START
(any format ffmpeg reads). Without the narration files, mix.wav is the foley alone.
"""
import os, sys, subprocess, glob, wave
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from cues import C, DUR, P2_START

SR = 44100
N = int((DUR + 0.5) * SR)
rng = np.random.default_rng(7)
out = np.zeros((N, 2))


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def put(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    sig = sig[: N - i]
    out[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    out[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))


def noise(sec):
    return rng.standard_normal(int(sec * SR))


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def tone(freq, sec, decay=0.3):
    t = np.arange(int(sec * SR)) / SR
    return np.sin(2 * np.pi * freq * t) * env(len(t), 0.001, decay)


def thud(sec=0.5, f0=70, decay=0.18):
    t = np.arange(int(sec * SR)) / SR
    return np.sin(2 * np.pi * f0 * t * (1 + 1.5 * np.exp(-t * 30))) * env(len(t), .001, decay) + lowpass(noise(sec), 30) * env(len(t), .001, .05) * .6


def rip(sec=0.5):
    n = noise(sec); n = n - lowpass(n, 6)
    crackle = (rng.uniform(size=len(n)) > 0.985) * rng.standard_normal(len(n)) * 3
    t = np.arange(len(n)) / SR
    return (n * 0.5 + crackle) * np.sin(np.pi * t / sec) ** 0.6 * 0.5


def glass_crack():
    s = np.zeros(int(0.9 * SR))
    for k in range(9):
        i = int(rng.uniform(0, 0.25) * SR)
        c = (noise(0.03) - lowpass(noise(0.03), 3)) * env(int(0.03 * SR), .0005, .006)
        s[i:i + len(c)] += c * rng.uniform(.5, 1)
    for fr in (2630, 3910, 5240):
        s += tone(fr, 0.9, 0.25) * 0.12
    return s


def click():
    c = noise(0.04); c = c - lowpass(c, 4)
    return c * env(len(c), .0005, .008) + tone(1800, 0.04, .01) * .3


def ping(freq=1320):
    return tone(freq, 0.35, 0.09) * .5 + tone(freq * 1.5, 0.35, 0.06) * .3


def clink():
    return sum(tone(f, 0.8, .2) * a for f, a in ((1890, .4), (2930, .25), (4410, .15)))


def creak(sec=0.6):
    t = np.arange(int(sec * SR)) / SR
    f = 180 + 90 * np.sin(2 * np.pi * 3 * t)
    saw = ((np.cumsum(f) / SR) % 1 - .5)
    return lowpass(saw, 8) * np.sin(np.pi * t / sec) * .5


def add(*xs):
    out_ = np.zeros(max(len(x) for x in xs))
    for x in xs: out_[:len(x)] += x
    return out_


def heartbeat():
    a = np.concatenate([thud(0.35, 52, 0.09), np.zeros(int(.11 * SR))])
    return a + np.concatenate([np.zeros(int(.16 * SR)), thud(0.3, 46, 0.08) * .7])[:len(a)]


# ---- scene rips (every cut except the dimming of the room)
def whoosh(sec=0.5, rise=True):
    n = noise(sec); t = np.arange(len(n)) / SR
    out_ = np.zeros_like(n); y = 0.0; a = 0.0
    for k in range(0, len(n), 64):                       # band-limited noise that swells
        out_[k:k + 64] = lowpass(n[k:k + 64 + 8], 3 + int(20 * (1 - k / len(n)) if rise else 3 + 20 * k / len(n)))[:len(out_[k:k + 64])]
    return out_ * np.sin(np.pi * t / sec) ** 2 * 0.8


def slats(sec=0.55):
    s = np.zeros(int(sec * SR))
    for k in range(14):
        i = int(k / 14 * (sec - 0.05) * SR); c = click()[:1500] * 0.7
        s[i:i + len(c)] += c
    return s


# ---- transitions: paper rips right-to-left, a page turn into 1880
for key in ("awakhir", "waadu", "ikhtaru", "lakin", "chem2", "insan", "yawm", "logo"):
    put(rip(), C[key], 0.35, rng.uniform(-.3, .3))
put(whoosh(0.7), C["qabl"], 0.35); put(rip(0.12) * .5, C["qabl"] + 0.55, 0.3)
put(thud(0.8, 44, .3), C["chem2"], 0.8)

# ---- part 1
put(tone(880, 1.4, .6) * .08 + tone(1320, 1.4, .5) * .05, 0.15)          # bottle chime under «سمّوه البطل»
put(glass_crack(), C["akhtar"], 0.7)
put(creak(0.6), C["akhaf"], 0.5)
for i in range(6): put(click(), C["heroin"] + i * 0.12, 0.8, -.2 + i * .08)
put(thud(0.4, 90, .12), C["shuja"], 0.6)
put(thud(0.9, 48, .3), C["akhaf2"], 1.0); put(clink() * .5, C["akhaf2"] + .02, .5)
put(heartbeat(), C["x2"], 0.8); put(heartbeat(), C["x5"], 1.0)
put(clink(), C["medal"] + 0.45, 0.6); put(clink() * .6, C["medal"] + 0.62, 0.4)

# ---- part 2
put(thud(0.4, 110, .1), C["y1880"], .6)
t = C["arba"]
while t < C["machine"]:                                                 # the clock
    put(click() * .6, t, .45, .4); t += 0.5
for i in range(4): put(add(click() * .8, thud(.15, 200, .03) * .3), C["arba"] + i * .4, .6, -.3)
put(thud(1.0, 40, .35), C["machine"] + 0.45, 1.0)
a, b = C["machine"] + 0.6, C["insan"]                                       # machine whirr
tt = np.arange(int((b - a) * SR)) / SR
whir = np.sin(2 * np.pi * (55 * tt + 4 * np.sin(2 * np.pi * 6 * tt))) * .25 + lowpass(rng.standard_normal(len(tt)), 20) * .4
whir *= np.minimum(1, tt / .3) * np.minimum(1, (b - a - tt) / .1) * (1 + 0.6 * (tt > C["ishrin"] - a))
put(whir, a, .5)
a, b = C["ishrin"], C["insan"] - 0.05                                       # cigarettes pouring
pour = np.zeros(int((b - a) * SR))
for k in range(1800):
    u = np.sqrt(rng.uniform())
    i = int(u * (len(pour) - 3000))
    c = click()[:1500] * rng.uniform(.2, .7)
    pour[i:i + len(c)] += c
pour *= np.linspace(.3, 1, len(pour))
put(pour, a, .5)
for key, f0 in (("aqwa", 60), ("asra", 64), ("akthar", 56)):
    put(add(thud(0.6, f0, .2), rip(.08) * .6), C[key], 1.0)

# ---- today
a, b = C["daqiqa"], C["fahal"] - 0.3
for k in range(60):
    u = (k / 60) ** 0.6
    put(ping(rng.choice([1175, 1320, 1568, 1760])), a + u * (b - a), .25, rng.uniform(-.6, .6))
t, gap = C["yawm"] + 0.6, 0.85
while t < C["logo"]:
    put(heartbeat(), t, .55 if t < C["fahal"] else .35); t += gap
    gap = 0.7 if t < C["fahal"] else 1.1
put(thud(1.6, 38, .7), C["logo"] + 0.1, .8)

foley = out / max(1e-6, np.abs(out).max()) * 0.6


def read_any(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)


def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


write(os.path.join(HERE, "foley.wav"), foley)
voice_f = os.path.join(HERE, "narration", "voice.wav")      # cleaned, tightened voice (tools/voice.py)
mix = foley.copy(); voice = os.path.exists(voice_f)
if voice:
    v = read_any(voice_f)[:N]
    v = np.pad(v, ((0, N - len(v)), (0, 0)))
    env_ = np.convolve(np.abs(v[:, 0]), np.ones(int(.15 * SR)) / int(.15 * SR), mode="same")
    duck = 1 - 0.55 * np.clip(env_ / 0.04, 0, 1)                # foley steps back under the voice
    mix = foley * duck[:, None] * 0.8 + v
    mix = mix / max(1, np.abs(mix).max() / 0.98)
write(os.path.join(HERE, "mix.wav"), mix)
print("mix.wav", "with the narration" if voice else "(foley only)")
