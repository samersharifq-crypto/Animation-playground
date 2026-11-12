"""Lay the recorded narration onto the tawba short: clean the voice, gate everything between
phrases, retime the picture + its sound effects piecewise so each label lands on its spoken phrase."""
import subprocess, json, sys, os
import numpy as np
from scipy.io import wavfile

SRC, RAW, OUT, TMP = sys.argv[1:5]
SR, FPS, W, H = 48000, 24, 1080, 1920
os.makedirs(TMP, exist_ok=True)

# spoken phrases: (recording start, recording end, output start)
PH = [(2.03, 3.27, 0.45), (3.92, 5.35, 2.34), (6.54, 7.86, 5.40), (8.64, 10.42, 7.90),
      (10.80, 12.08, 11.30), (12.90, 15.57, 13.10), (16.79, 18.40, 17.40), (19.26, 26.87, 19.86),
      (28.00, 31.16, 28.60), (31.85, 34.84, 32.45), (35.98, 38.51, 36.58), (38.90, 40.35, 39.50),
      (41.00, 43.20, 41.60), (43.77, 45.70, 45.30), (46.18, 47.35, 47.70), (47.82, 49.32, 49.80),
      (49.73, 51.01, 51.70)]
DUR = 55.8

# ---- voice: light cleanup, loudness, hard silence between phrases
CH = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=75,afftdn=nf=-58:nr=6:tn=1,"
      "equalizer=f=3200:t=q:w=1.5:g=1,acompressor=threshold=-22dB:ratio=1.6:attack=15:release=200:makeup=1")
p = subprocess.run(["ffmpeg", "-hide_banner", "-i", RAW, "-af", CH + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True)
m = json.loads(p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1])
ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", RAW, "-af", f"{CH},{ln},aresample=48000",
                "-ac", "1", "-c:a", "pcm_f32le", f"{TMP}/voice.wav"], check=True)
_, v = wavfile.read(f"{TMP}/voice.wav")
N = int(DUR * SR)
voice = np.zeros(N, np.float32)
for a, b, o in PH:
    i0, i1 = int((a - 0.07) * SR), int((b + 0.16) * SR)
    seg = v[i0:i1].copy()
    fi, fo = int(0.03 * SR), int(0.08 * SR)
    seg[:fi] *= np.linspace(0, 1, fi); seg[-fo:] *= np.linspace(1, 0, fo)
    d = int((o - 0.07) * SR); voice[d:d + len(seg)] += seg

# verse line starts inside the long phrase: quietest point near the letter-count estimate
a, b, o = PH[7]
def dip(t):
    ts = np.arange(t - 0.5, t + 0.5, 0.01)
    e = [np.mean(v[int(x * SR):int((x + 0.06) * SR)] ** 2) for x in ts]
    return ts[int(np.argmin(e))] + 0.05
L2 = dip(a + (b - a) * 0.31) - a + o
L3 = dip(a + (b - a) * 0.63) - a + o
print("verse lines 2/3 at", round(L2, 2), round(L3, 2))

# ---- picture retime: (source time, output time) anchors
A = [(0, 0), (0.4, 0.4), (2.0, 1.5), (2.4, 2.3), (4.1, 3.6), (5.95, 5.0), (6.35, 5.4), (7.6, 6.4), (9.0, 7.5),
     (9.4, 7.9), (10.6, 9.15), (13.2, 11.0), (14.8, 13.2), (17.85, 15.4), (19.95, 16.95), (20.4, 17.4),
     (21.3, 18.6), (23.1, 19.8), (25.05, L2), (27.0, L3), (28.95, 28.55), (30.95, 32.4), (32.9, 35.45),
     (33.55, 36.2), (33.95, 36.58), (35.6, 39.0), (36.45, 39.5), (37.6, 40.6), (38.95, 41.6), (41.2, 43.8),
     (43.15, 45.0), (43.45, 45.3), (44.7, 47.0), (45.4, 47.7), (46.6, 48.8), (47.95, 49.8), (49.45, 51.7),
     (50.2, 52.5), (53.5, 55.8)]
vs, os_ = np.array([x[0] for x in A]), np.array([x[1] for x in A])
BLEND = (21.3, 33.5)   # the verse card is slowed a lot: cross-blend frames there so the shimmer stays smooth

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", f"{TMP}/pic.mp4"],
                       stdin=subprocess.PIPE)
FS = W * H * 3
cur_i, cur, nxt = 0, dec.stdout.read(FS), dec.stdout.read(FS)
for n in range(int(DUR * FPS)):
    st = float(np.interp(n / FPS, os_, vs)); pos = st * FPS; k = int(pos)
    while cur_i < k and nxt and len(nxt) == FS:
        cur, nxt = nxt, dec.stdout.read(FS); cur_i += 1
    w = pos - k
    if BLEND[0] <= st <= BLEND[1] and 0.05 < w < 0.95 and nxt and len(nxt) == FS and cur_i == k:
        f = (np.frombuffer(cur, np.uint8) * (1 - w) + np.frombuffer(nxt, np.uint8) * w).astype(np.uint8).tobytes()
    else:
        f = cur
    enc.stdin.write(f)
enc.stdin.close(); enc.wait(); dec.kill()

# ---- sound effects from the original clip, retimed with the same anchors (pitch kept)
sfx = np.zeros(N, np.float32)
for (v0, o0), (v1, o1) in zip(A[:-1], A[1:]):
    r = (v1 - v0) / (o1 - o0)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{v0}", "-t", f"{v1 - v0}", "-i", SRC, "-vn", "-ac", "1", "-ar", str(SR),
                          "-af", f"atempo={r:.5f}", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy(); n = int(round((o1 - o0) * SR)); x = np.pad(x, (0, max(0, n - len(x))))[:n]
    k = int(0.003 * SR); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
    d = int(round(o0 * SR)); sfx[d:d + n] += x[:N - d]
env = np.convolve(np.abs(voice), np.ones(int(.15 * SR)) / int(.15 * SR), mode="same")
sfx *= 0.8 * (1 - 0.4 * np.clip(env / 0.05, 0, 1))          # effects sit under the voice
rng = np.random.default_rng(11); room = np.convolve(rng.standard_normal(N), np.ones(40) / 40, mode="same")
mix = voice + sfx + room / np.abs(room).max() * 10 ** (-54 / 20)
k = int(0.5 * SR); mix[-k:] *= np.linspace(1, 0, k)
mix = 0.95 * np.tanh(mix / 0.95)
wavfile.write(f"{TMP}/mix.wav", SR, mix.astype(np.float32))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{TMP}/pic.mp4", "-i", f"{TMP}/mix.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", OUT], check=True)
