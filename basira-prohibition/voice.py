"""Clean the narration (P1, P2), drop breaths and every sound between phrases, and lay the phrases on a
tight video timeline with chosen pauses. Writes proj/voice.wav (48 kHz mono) and proj/timing.json
(phrase + word times in VIDEO seconds)."""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from scipy.io import wavfile
import basira_sound as S

SR = S.SR
P = os.path.join(HERE, "proj"); V = os.path.join(HERE, "voice")
# slightly stronger denoise than "light" (the user asked for a cleaner voice), same gentle EQ/compression
S.PRESETS["clean"] = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=80,afftdn=nf=-55:nr=10:tn=1,"
                      "equalizer=f=3200:t=q:w=1.5:g=1,acompressor=threshold=-22dB:ratio=1.8:attack=15:release=200:makeup=1,"
                      "deesser=i=0.2")

# phrases: (recording, start, end, words, gap BEFORE this phrase in the video)
PHRASES = [
    ("P1", 2.08, 3.31, "في ليلة واحدة", 0.35),
    ("P1", 3.63, 5.72, "أغلقت كل حانات أمريكا", 0.45),
    ("P1", 6.92, 9.47, "سنة ألف وتسعمئة وعشرين", 1.0),
    ("P1", 9.62, 11.36, "صار بيع الخمر جريمة", 0.35),
    ("P1", 12.19, 15.5, "غضب الناس وظهر المهربون والعصابات", 0.6),
    ("P1", 16.78, 19.68, "لكن حدث شيء لم يتوقعه كثيرون", 0.8),
    ("P1", 19.87, 22.61, "أمراض الكبد التي تسببها الخمر", 0.5),
    ("P1", 22.76, 24.52, "انخفضت إلى النصف", 0.5),
    ("P2", 2.48, 4.05, "الناس لم يتغيروا", 0.8),
    ("P2", 4.31, 7.55, "الذي تغير هو المسافة بينهم وبين الكأس", 0.35),
    ("P2", 9.14, 13.7, "وحين رفع الحظر سنة ألف وتسعمئة وثلاث وثلاثين", 0.6),
    ("P2", 14.07, 16.81, "وصارت الخمر في المتناول من جديد", 0.3),
    ("P2", 18.04, 20.5, "عادت الأرقام ترتفع مع السنين", 0.45),
    ("P2", 21.61, 22.94, "فالقاعدة بسيطة", 0.6),
    ("P2", 23.52, 24.91, "كلما قرب الشيء", 0.4),
    ("P2", 25.4, 26.58, "زاد استهلاكه", 0.4),
    ("P2", 28.33, 29.08, "واليوم", 0.8),
    ("P2", 29.27, 31.15, "أقرب ما يدمنه الناس", 0.25),
    ("P2", 31.3, 32.93, "لا يبعد عنك شبرا", 0.3),
    ("P2", 33.34, 34.6, "إنه في جيبك", 0.45),
    ("P2", 36.21, 38.29, "فإن أردت أن تقلل منه", 0.7),
    ("P2", 38.68, 39.84, "فابدأ بالمسافة", 0.45),
]
PRE, POST = 0.06, 0.14


def strip(w):
    return "".join(ch for ch in w if ch not in "…،.,:؛!؟ً")


def breath_mask(x):
    """1 = keep. Mutes 20-ms frames that are quiet AND hiss-like (breaths, lip noise) inside a phrase."""
    from scipy import signal
    hop = int(0.02 * SR); n = len(x) // hop; keep = np.ones(n)
    bl, al = signal.butter(2, [80 / (SR / 2), 400 / (SR / 2)], "band"); bh, ah = signal.butter(2, [2000 / (SR / 2), 7000 / (SR / 2)], "band")
    lo = signal.lfilter(bl, al, x); hi = signal.lfilter(bh, ah, x)
    for i in range(n):
        s = slice(i * hop, (i + 1) * hop)
        rms = 20 * np.log10(np.sqrt((x[s] ** 2).mean()) + 1e-9)
        ratio = 10 * np.log10(((lo[s] ** 2).mean() + 1e-12) / ((hi[s] ** 2).mean() + 1e-12))
        if rms < -42 and ratio < 6: keep[i] = 0
    keep = np.repeat(keep, hop); keep = np.pad(keep, (0, len(x) - len(keep)), constant_values=1)
    k = int(0.015 * SR); return np.convolve(keep, np.ones(k) / k, mode="same")


def main():
    words_json = json.load(open(os.path.join(V, "words.json")))
    clean = {}
    for r in ("P1", "P2"):
        out = os.path.join(P, f"voice_{r}.wav")
        S.clean(os.path.join(V, f"{r}.m4a"), out, "clean")
        clean[r] = wavfile.read(out)[1].astype(np.float32)
    t = 0.0; pieces = []; timing = []
    for i, (r, a, b, text, gap) in enumerate(PHRASES):
        t += gap
        seg = clean[r][int((a - PRE) * SR):int((b + POST) * SR)].copy()
        seg *= breath_mask(seg)
        f = int(0.02 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
        start_v = t + PRE                                   # video time of the first word
        pieces.append((t, seg))
        words = text.split()
        est = S.word_times(a, b, words)
        wt = []
        wj = [(strip(w), s0) for w, s0, _ in words_json[r] if a - 0.6 <= s0 <= b]
        j = 0
        for k, w in enumerate(words):
            rec = est[k]
            if k == 0: rec = a
            else:
                for jj in range(j, len(wj)):
                    if wj[jj][0] and (wj[jj][0] in strip(w) or strip(w) in wj[jj][0]) and a < wj[jj][1] < b:
                        rec = 0.5 * wj[jj][1] + 0.5 * est[k] if abs(wj[jj][1] - est[k]) < 0.6 else est[k]
                        rec = max(rec, wt[-1][1] - start_v + a + 0.12) if wt else rec
                        j = jj + 1; break
            wt.append((w, round(rec - a + start_v, 3)))
        timing.append(dict(rec=r, text=text, start=round(start_v, 3), end=round(start_v + (b - a), 3), words=wt))
        t += (b - a) + PRE + POST
    dur = t + 0.2
    out = np.zeros(int(dur * SR) + SR, np.float32)
    for t0, seg in pieces:
        i = int(t0 * SR); out[i:i + len(seg)] += seg
    wavfile.write(os.path.join(P, "voice.wav"), SR, out[: int(dur * SR)])
    json.dump(dict(voice_end=round(dur, 3), phrases=timing), open(os.path.join(P, "timing.json"), "w"), ensure_ascii=False, indent=1)
    for ph in timing: print(f"{ph['start']:6.2f}-{ph['end']:6.2f} {ph['text']}")
    print("voice end", round(dur, 2))


if __name__ == "__main__":
    main()
