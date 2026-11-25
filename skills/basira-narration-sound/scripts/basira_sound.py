"""basira_sound.py - narration cleanup, timing and paper-foley sound design for بصيرة videos (no music)."""
import subprocess, json
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(11)

PRESETS = {
    "light": "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=75,afftdn=nf=-58:nr=6:tn=1,"
             "equalizer=f=3200:t=q:w=1.5:g=1,acompressor=threshold=-22dB:ratio=1.6:attack=15:release=200:makeup=1",
    "mawzoon": "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,afftdn=nf=-52:nr=12:tn=1,"
               "agate=threshold=0.006:ratio=3:attack=8:release=250:range=0.2,equalizer=f=250:t=q:w=1.2:g=-1.5,"
               "equalizer=f=3500:t=q:w=1.5:g=2,acompressor=threshold=-24dB:ratio=2.5:attack=10:release=150:makeup=2,deesser=i=0.3",
}

def clean(raw, out_wav, preset="light", lufs=-16):
    """Two-pass loudnorm to -16 LUFS, mono 48 kHz float wav."""
    ch = PRESETS[preset]
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", f"{ch},loudnorm=I={lufs}:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1])
    ln = (f"loudnorm=I={lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f"{ch},{ln},aresample=48000",
                    "-ac", "1", "-c:a", "pcm_f32le", out_wav], check=True)

def speech_segments(wav, noise_db=-38, min_sil=0.25, min_len=0.15):
    """Speech spans (recording seconds). Analysis runs through the gated "mawzoon" chain + loudness boost
    so pauses are found reliably even when the delivered voice uses the lighter preset.
    Very short blips (clicks, breaths) are dropped. Pass the RAW recording or any cleaned copy."""
    an = PRESETS["mawzoon"] + ",dynaudnorm=f=150:g=15"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", f"{an},silencedetect=noise={noise_db}dB:d={min_sil}",
                        "-f", "null", "-"], capture_output=True, text=True)
    starts, ends = [], []
    for line in p.stderr.splitlines():
        if "silence_start:" in line: starts.append(float(line.split("silence_start:")[1].split()[0]))
        if "silence_end:" in line: ends.append(float(line.split("silence_end:")[1].split("|")[0]))
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                               capture_output=True, text=True).stdout)
    edges = [0.0] + ends; stops = starts + [dur]
    if starts and starts[0] < 0.01: edges, stops = ends, starts[1:] + [dur]
    return [(a, b) for a, b in zip(edges, stops) if b - a >= min_len]

def word_times(seg_start, seg_end, words):
    """Estimate when each word in a phrase starts, by letter count (good to ~0.2 s; the user corrects outliers)."""
    lens = [len(w) + 1 for w in words]; tot = sum(lens); out, acc = [], 0
    for L in lens:
        out.append(seg_start + (seg_end - seg_start) * acc / tot); acc += L
    return out

def t2i(t): return int(t * SR)
def env(n, att, dec, shape=3.0):
    a = int(att * SR); e = np.ones(n)
    if a: e[:a] = np.linspace(0, 1, a)
    e[a:] *= np.exp(-np.linspace(0, shape, n - a)); return e
def bandnoise(n, lo, hi, order=2):
    return signal.lfilter(*signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band"), rng.standard_normal(n))
def lownoise(n, hi, order=2):
    return signal.lfilter(*signal.butter(order, hi / (SR / 2), "low"), rng.standard_normal(n))
def norm(x, db): return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (db / 20)
def _fade(n, dur, a=0.4, b=0.3):
    tt = np.arange(n) / SR; return np.minimum(1, np.minimum(tt / a, (dur - tt) / b))

def tear(dur=0.55):
    n = t2i(dur); base = bandnoise(n, 900, 7000) * env(n, 0.04, dur, 2.0)
    cr = np.zeros(n); idx = rng.integers(0, int(n * .85), 260); cr[idx] = rng.uniform(-1, 1, len(idx))
    cr = signal.lfilter(*signal.butter(2, [1500 / (SR / 2), 9000 / (SR / 2)], "band"), cr)
    return norm(base * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 40, n)))) + cr * 3, -20)
def pop(db=-27):
    n = t2i(0.12); return norm(lownoise(n, 1800) * env(n, .002, .12, 6) + bandnoise(n, 2500, 6000) * env(n, .001, .03, 9) * .3, db)
def tick(db=-34):
    n = t2i(0.05); return norm(bandnoise(n, 1500, 5000) * env(n, .001, .05, 8), db)
def shuffle(db=-31):
    n = t2i(0.16); return norm(bandnoise(n, 600, 4000) * env(n, .02, .16, 4), db)
def rumble(dur=2.6, db=-27):
    n = t2i(dur); return norm(lownoise(n, 140, 3) * env(n, .05, dur, 2.2) + lownoise(n, 400) * env(n, .01, .4, 6) * .5, db)
def crack(db=-5):
    n = t2i(0.7); x = np.zeros(n); t0 = 0
    for _ in range(9):
        L = t2i(rng.uniform(.03, .09)); seg = bandnoise(L, 300, 10000) * np.exp(-np.linspace(0, 5, L)) * rng.uniform(.5, 1)
        x[t0:t0 + L] += seg[:max(0, min(L, n - t0))]; t0 += t2i(rng.uniform(.02, .07))
    return norm(x + bandnoise(n, 1500, 9000) * env(n, .001, .7, 6) * .6, db)
def big_thunder(dur=5.5):
    n = t2i(dur); tt = np.arange(n) / SR
    boom = lownoise(n, 110, 3) * env(n, .01, dur, 3.2) + .5 * np.sin(2 * np.pi * 42 * tt) * np.exp(-tt * 2.5)
    roll = np.interp(np.arange(n), np.linspace(0, n, int(dur * 6) + 2), rng.uniform(.2, 1, int(dur * 6) + 2))
    return norm(boom, -6) + norm(lownoise(n, 320) * roll * env(n, .25, dur, 1.6), -11)
def clink(db=-26):
    n = t2i(1.2); tt = np.arange(n) / SR
    return norm(sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in [(2210, 1, 5), (3480, .6, 7), (5230, .35, 10), (6900, .2, 13)]), db)
def whoosh(dur=0.6, db=-29):
    n = t2i(dur); x = np.zeros(n); nz = rng.standard_normal(n)
    for s in range(0, n, 512):
        fc = 500 + 2500 * s / n
        x[s:s + 512] = signal.lfilter(*signal.butter(2, [fc * .6 / (SR / 2), fc * 1.4 / (SR / 2)], "band"), nz[s:s + 512])
    return norm(x * np.sin(np.linspace(0, np.pi, n)) ** 2, db)
def water(dur, db=-33):
    n = t2i(dur); tt = np.arange(n) / SR
    x = lownoise(n, 700) * (.55 + .45 * np.sin(2 * np.pi * .45 * tt + 1)) + bandnoise(n, 1500, 5000) * (.3 + .3 * np.sin(2 * np.pi * .9 * tt)) * .15
    return norm(x * _fade(n, dur, .6, .6), db)
def hum(dur, db=-36):
    n = t2i(dur); tt = np.arange(n) / SR
    x = (.6 * np.sin(2 * np.pi * 110 * tt) + .3 * np.sin(2 * np.pi * 220 * tt) + .15 * np.sin(2 * np.pi * 330 * tt)) * (.8 + .2 * np.sin(2 * np.pi * 6 * tt))
    return norm(x * _fade(n, dur, .02, .02), db)
def ding(db=-30):
    n = t2i(0.9); tt = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * 1318 * tt) * np.exp(-tt * 6) + .5 * np.sin(2 * np.pi * 1975 * tt) * np.exp(-tt * 8), db)
def zap(db=-24):
    n = t2i(0.09); tt = np.arange(n) / SR
    return norm(bandnoise(n, 800, 8000) * env(n, .001, .09, 4) + .6 * np.sign(np.sin(2 * np.pi * 60 * tt)) * env(n, .001, .09, 3), db)
def drone(dur, db=-32):
    n = t2i(dur); tt = np.arange(n) / SR
    return norm((lownoise(n, 220, 3) + .4 * np.sin(2 * np.pi * 55 * tt)) * np.minimum(1, tt / (dur * .6)), db)
def room(dur, db=-52):
    return norm(lownoise(t2i(dur), 900), db)

class Timeline:
    def __init__(self, dur, voice, segments, start, place_at=0.5, pauses=None, pre=0.07, post=0.14):
        """voice: cleaned wav. segments: speech spans (recording s). start: recording time where the part begins.
        place_at: video time of `start`. pauses: {recording_time: extra_seconds} inserted silences."""
        self.dur, self.start, self.place_at = dur, start, place_at
        self.pauses = sorted((pauses or {}).items())
        _, v = wavfile.read(voice); v = v.astype(np.float32)
        g = np.zeros_like(v)
        for a, b in segments: g[max(0, t2i(a - pre)):t2i(b + post)] = 1
        k = t2i(0.03); g = np.convolve(g, np.ones(k) / k, mode="same")
        v = v * g
        self.voice = np.zeros(t2i(dur), np.float32)
        cuts = [start] + [p for p, _ in self.pauses] + [len(v) / SR]
        for i in range(len(cuts) - 1):
            a, b = cuts[i], cuts[i + 1]
            seg = v[t2i(a):t2i(b)]; d0 = t2i(self.v(a))
            seg = seg[:max(0, len(self.voice) - d0)]; self.voice[d0:d0 + len(seg)] += seg
        self.sfx = np.zeros_like(self.voice)
        self.add(0, room(dur))

    def v(self, rec_t):
        """recording time -> video time"""
        return rec_t - self.start + self.place_at + sum(d for p, d in self.pauses if rec_t >= p)

    def add(self, t, x, duck=False):
        i = t2i(t); j = min(len(self.sfx), i + len(x))
        if i >= len(self.sfx): return
        x = x[:j - i]
        if duck:
            e = np.convolve(np.abs(self.voice), np.ones(t2i(.15)) / t2i(.15), mode="same")[i:j]
            x = x * (1 - 0.7 * np.clip(e / 0.05, 0, 1))
        self.sfx[i:j] += x

    def labels(self, times):
        for ts in times:
            self.add(ts[0] - 0.08, pop())
            for t in ts[1:]: self.add(t, tick())

    def mix(self, out_wav):
        m = self.voice + self.sfx
        n = t2i(0.6); m[-n:] *= np.linspace(1, 0, n)
        m = 0.95 * np.tanh(m / 0.95)
        wavfile.write(out_wav, SR, m.astype(np.float32))
