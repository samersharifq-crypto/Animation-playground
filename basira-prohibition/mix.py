"""Voice on top, effects underneath: effects sit ~14 dB under the voice and duck a further 8 dB while it speaks."""
import os, json
import numpy as np
from scipy.io import wavfile
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, "proj")
SR = 48000
dur = json.load(open(os.path.join(P, "warp.json")))["dur"]; N = int(dur * SR)
v = wavfile.read(os.path.join(P, "voice.wav"))[1].astype(np.float32)
s = wavfile.read(os.path.join(P, "sfx_sync.wav"))[1].astype(np.float32)
if s.dtype != np.float32 or np.abs(s).max() > 2: s = s / 32768
v = np.pad(v, (0, max(0, N - len(v))))[:N]; s = np.pad(s, (0, max(0, N - len(s))))[:N]

def rms(x): return np.sqrt((x ** 2).mean() + 1e-12)
speech = np.abs(v) > 1e-4
vr = rms(v[speech]); sr_ = rms(s[s != 0]) if np.any(s) else 1
s *= (vr / sr_) * 10 ** (-14 / 20)
k = int(0.12 * SR)
envv = np.convolve(np.abs(v), np.ones(k) / k, mode="same")
duck = 1 - (1 - 10 ** (-8 / 20)) * np.clip(envv / (0.3 * np.abs(v).max() / 3), 0, 1)
duck = np.convolve(duck, np.ones(k) / k, mode="same")
room = np.random.default_rng(3).standard_normal(N).astype(np.float32)
from scipy.signal import butter, lfilter
b, a = butter(2, 900 / (SR / 2)); room = lfilter(b, a, room); room *= 10 ** (-56 / 20) / rms(room)
m = v + s * duck + room
m = 0.97 * np.tanh(m / 0.97)
st = np.stack([m, m], 1).astype(np.float32)
wavfile.write(os.path.join(P, "mix_sync.wav"), SR, st)
print("ok", round(dur, 2))
