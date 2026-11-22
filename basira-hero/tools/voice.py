"""Build the narration track for «سمّوه البطل» from narration/P1.m4a and P2.m4a.

- cleans both takes (noise reduction, light compression, -16 LUFS)
- deletes every breath / silent gap between phrases and replaces it with a short, controlled pause
  (≈0.22 s inside a sentence, ≈0.45 s between sentences, a little longer before the key beats)
- times every cue word with Whisper (word timestamps), snapped to the real speech onsets
- writes narration/voice.wav (the whole Short, voice only) and narration/cues.json (video seconds)

  HF_HUB_DISABLE_XET=1 python3 tools/voice.py
"""
import os, sys, json, subprocess
import numpy as np
from scipy.io import wavfile
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import basira_sound as S

SR = 48000
NAR = os.path.join(HERE, "narration")
P1_AT = 0.35            # video time of the first word
BETWEEN_PARTS = 1.8     # pause between the end of P1 and the start of P2
TAIL = 3.4              # logo after the last word

INSIDE, SENTENCE = 0.22, 0.45
SENT_END = {"P1": ["الإنسان", "محله", "الشجاع", "مرات"], "P2": ["الدقيقة", "ألف", "وأكثر", "عام"]}
BEFORE = {"P1": {"هيروين": 0.40, "إلى": 0.30, "لكن": 0.55}, "P2": {"الإنسان": 1.5, "أقوى": 0.35, "أم": 0.50, "فهل": 0.60, "واليوم": 0.55}}


def plain(w):
    return "".join(ch for ch in w if not ("ً" <= ch <= "ْ") and ch not in "،,.؟?!«»:").strip()


def transcribe(wav):
    from faster_whisper import WhisperModel
    m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    segs, _ = m.transcribe(np.frombuffer(raw, np.float32), language="ar", word_timestamps=True, beam_size=5)
    return [(w.start, w.end, plain(w.word)) for s in segs for w in s.words]


def build(part, words_cache):
    raw = os.path.join(NAR, part + ".m4a")
    clean = os.path.join(NAR, part + "_clean.wav")
    S.clean(raw, clean, "mawzoon")
    _, v = wavfile.read(clean); v = v.astype(np.float32)
    segs = S.speech_segments(raw, noise_db=-38, min_sil=0.12, min_len=0.15)
    words = words_cache.get(part) or transcribe(clean)
    words_cache[part] = words
    first, last = words[0][0], words[-1][1]
    segs = [(a, b) for a, b in segs if b > first - 0.3 and a < last + 0.4 and b - a > 0.2]
    # snap word starts into real speech
    def snap(t):
        for a, b in segs:
            if a - 0.02 <= t <= b: return t
            if t < a: return a
        return t
    words = [(snap(a), b, w) for a, b, w in words]
    # assemble with controlled gaps
    out, mapping, pos = [], [], 0.0
    pre, post = 0.05, 0.12
    for i, (a, b) in enumerate(segs):
        if i:
            pa, pb = segs[i - 1]
            gap = a - pb
            nxt = [w for w in words if w[0] >= a - 0.05]
            prv = [w for w in words if w[0] < a - 0.05]
            nw = nxt[0][2] if nxt else ""
            pw = prv[-1][2] if prv else ""
            want = INSIDE
            if any(pw.startswith(e) for e in SENT_END[part]): want = SENTENCE
            for k, d in BEFORE[part].items():
                if nw == k: want = max(want, d)
            g = min(gap, want) if gap < want else want
            pos += max(0.0, g - pre - post)
        seg = v[S.t2i(max(0, a - pre)):S.t2i(b + post)].copy()
        n = len(seg); fi, fo = S.t2i(0.012), S.t2i(0.06)
        seg[:fi] *= np.linspace(0, 1, fi); seg[-fo:] *= np.linspace(1, 0, fo)
        mapping.append((a - pre, b + post, pos))
        out.append((pos, seg)); pos += n / SR
    total = pos
    def m(t):
        for a, b, p in mapping:
            if t <= b: return p + max(0.0, t - a)
        return total
    return out, total, [(m(a), w) for a, b, w in words]


def main():
    cache_f = os.path.join(NAR, "words.json")
    cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
    p1, d1, w1 = build("P1", cache)
    p2, d2, w2 = build("P2", cache)
    json.dump(cache, open(cache_f, "w"), ensure_ascii=False, indent=0)
    p2_at = P1_AT + d1 + BETWEEN_PARTS
    dur = p2_at + d2 + TAIL
    track = np.zeros(S.t2i(dur + 0.5), np.float32)
    for off, parts in ((P1_AT, p1), (p2_at, p2)):
        for pos, seg in parts:
            i = S.t2i(off + pos); track[i:i + len(seg)] += seg
    wavfile.write(os.path.join(NAR, "voice.wav"), SR, track)
    W1 = [(P1_AT + t, w) for t, w in w1]; W2 = [(p2_at + t, w) for t, w in w2]

    def at(words, word, n=1, shift=0.0):
        k = 0
        for t, w in words:
            if w.startswith(word):
                k += 1
                if k == n: return round(t + shift, 2)
        raise KeyError(word)
    end2 = p2_at + d2
    C = {
        "batal": at(W1, "البطل"), "akhtar": at(W1, "أخطر"), "awakhir": at(W1, "في", 1, -0.12),
        "almania": at(W1, "كان", 1), "waadu": at(W1, "مسكن", 1, -0.1), "akhaf": at(W1, "أخف"),
        "min": at(W1, "من", 2), "morphin": at(W1, "المورفين"), "ikhtaru": at(W1, "فابتكروا", 1, -0.12),
        "ismen": at(W1, "اسما"), "heroin": at(W1, "هيروين"), "kalima": at(W1, "كلمة"), "shuja": at(W1, "الشجاع"),
        "lakin": at(W1, "لكن", 1, -0.12), "akhaf2": at(W1, "أخف", 2), "chem2": at(W1, "بل", 1, -0.05),
        "aqwa1": at(W1, "أقوى"), "aqwa1b": at(W1, "من", 4), "aqwa1c": at(W1, "المورفين", 2),
        "x2": at(W1, "بمر"), "x5": at(W1, "خمس"), "medal": at(W1, "مرات", 1, 0.3),
        "qabl": round(p2_at - 0.45, 2), "arba": at(W2, "أربع"), "sajaer": at(W2, "سجائر"),
        "machine": at(W2, "ثم"), "y1880": at(W2, "1880"), "ishrin": at(W2, "عشرين"), "alfan": at(W2, "ألف"),
        "insan": at(W2, "الإنسان", 1, -0.12), "lam": at(W2, "لم"), "yataghayar": at(W2, "يتغير"),
        "alladhi": at(W2, "الذي"), "taghayar": at(W2, "تغير"), "huwa": at(W2, "هو"), "jura": at(W2, "الجرعة"),
        "aqwa": at(W2, "أقوى"), "asra": at(W2, "وأسرع"), "akthar": at(W2, "وأكثر"),
        "yawm": at(W2, "واليوم", 1, -0.12), "daqiqa": at(W2, "دقيقة"), "am": at(W2, "عام"),
        "fahal": at(W2, "فهل", 1, -0.08), "sirna": at(W2, "صر"), "adaf": at(W2, "أضعف"),
        "am2": at(W2, "أم"), "anna": at(W2, "أن", 1), "jura2": at(W2, "الجرعة", 2), "sarat": at(W2, "صارت"),
        "aqwa2": at(W2, "أقوى", 2), "logo": round(end2 + 0.6, 2),
    }
    json.dump({"C": C, "DUR": round(dur, 2), "P2_START": round(p2_at, 2),
               "words": {"P1": W1, "P2": W2}}, open(os.path.join(NAR, "cues.json"), "w"), ensure_ascii=False, indent=1)
    print(f"P1 {d1:.2f}s  P2 {d2:.2f}s  -> Short {dur:.2f}s")
    for k, t in C.items(): print(f"  {k:11s} {t:6.2f}")


if __name__ == "__main__":
    main()
