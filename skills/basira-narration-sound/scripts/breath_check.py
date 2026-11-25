"""breath_check.py - look for breath-like sounds left in an edited voice: unvoiced, noisy, quieter than speech,
longer than 0.12 s, and not silent. Prints their positions (video s) per part."""
import sys, numpy as np
from scipy.io import wavfile
from scipy import signal


def frames(x, sr, hop=0.01, win=0.03):
    h, w = int(sr * hop), int(sr * win)
    n = (len(x) - w) // h
    return np.stack([x[i * h:i * h + w] for i in range(max(0, n))]), hop


def analyse(path=None, x=None, sr=48000):
    if x is None:
        sr, x = wavfile.read(path); x = x.astype(np.float32)
    x16 = signal.resample_poly(x, 1, 3); sr16 = sr // 3
    F, hop = frames(x16, sr16)
    rms = 20 * np.log10(np.sqrt((F ** 2).mean(1)) + 1e-9)
    win = np.hanning(F.shape[1])
    spec = np.abs(np.fft.rfft(F * win, axis=1)) + 1e-9
    flat = np.exp(np.log(spec).mean(1)) / spec.mean(1)               # spectral flatness: breath ≈ noise
    lo, hi = int(70 / (sr16 / F.shape[1])), int(400 / (sr16 / F.shape[1]))
    ac = np.array([np.correlate(f, f, "full")[len(f) - 1:] for f in F * win])
    ac = ac / (ac[:, :1] + 1e-9)
    lag0, lag1 = int(sr16 / 400), int(sr16 / 70)
    voiced = ac[:, lag0:lag1].max(1) > 0.45
    speech = rms[voiced & (rms > -50)]
    ref = np.median(speech) if len(speech) else -20
    cand = (~voiced) & (rms > -60) & (rms < ref - 12) & (flat > 0.25)
    runs, i = [], 0
    while i < len(cand):
        if cand[i]:
            j = i
            while j < len(cand) and cand[j]: j += 1
            if (j - i) * hop >= 0.12:
                freqs = np.fft.rfftfreq(F.shape[1], 1 / sr16)
                cen = float((spec[i:j] * freqs).sum() / spec[i:j].sum())
                runs.append((round(i * hop, 2), round(j * hop, 2), round(float(rms[i:j].mean()), 1), round(cen)))
            i = j
        else: i += 1
    return ref, runs


def mute_breaths(x, sr=48000, floor_db=-33, max_centroid=4200):
    """mute breath-like runs (quiet, noisy, unvoiced, not a hissing س/ش) with short fades; returns (x, muted runs)"""
    _, runs = analyse(x=x, sr=sr)
    x = x.copy(); muted = []
    for a, b, db, cen in runs:
        if db > floor_db or cen > max_centroid: continue
        i, j = int((a - 0.02) * sr), int((b + 0.03) * sr); f = int(0.012 * sr)
        g = np.ones(j - i, np.float32) * 0.03
        g[:f] = np.linspace(1, 0.03, f); g[-f:] = np.linspace(0.03, 1, f)
        x[i:j] *= g; muted.append((a, b, db))
    return x, muted


if __name__ == "__main__":
    for n in sys.argv[1:]:
        ref, runs = analyse(f"proj/vo_{n}.wav")
        print(f"part {n}: speech {ref:.0f} dB, breath-like runs: {runs}")
