"""voice_edit.py - turn a raw narration into the edited voice of a part:
light cleanup, breaths and noise between phrases removed (only spans that contain transcribed words are kept),
long gaps shortened, optional dramatic pauses inserted. Gives word times in video seconds."""
import os, json, re
import numpy as np
from scipy.io import wavfile
import basira_sound as S

HERE = os.path.dirname(os.path.abspath(__file__))
PLACE_AT = 0.5                                          # video time of the first word
GAP_MAX, GAP_MIN = 0.5, 0.16                            # pauses between phrases after editing (s)

_AR = str.maketrans("أإآٱىة", "اااايه")


def norm(w):
    w = re.sub(r"[ً-ْـٰ]", "", w)     # tashkeel, tatweel
    w = re.sub(r"[^\w%٪]", "", w)
    return w.translate(_AR)


def load_words(n):
    d = json.load(open(os.path.join(HERE, "proj", "asr", f"Sp{n}.json")))
    return [(a, b, w) for a, b, w, _ in d["words"]]


def build(n, pauses=None, gap_max=GAP_MAX, noise_db=-38):
    """pauses: {word_index: extra seconds inserted before that word}. Returns (voice array, words in video time)."""
    raw = os.path.join(HERE, "proj", "rec", f"Sp{n}.m4a")
    wav = os.path.join(HERE, "proj", f"voice_{n}.wav")
    if not os.path.exists(wav): S.clean(raw, wav, "light")
    _, v = wavfile.read(wav); v = v.astype(np.float32)
    segs = S.speech_segments(raw, noise_db=noise_db)
    words = load_words(n)
    for wi in sorted((pauses or {})):                    # a pause lands exactly before its word: split the span there
        cut = words[wi][0] - 0.04
        for k, (sa, sb) in enumerate(segs):
            if sa + 0.15 < cut < sb - 0.1:
                segs[k:k + 1] = [(sa, cut), (cut, sb)]; break
    # snap each word into the speech span it overlaps most (whisper starts words early, inside the silence)
    snapped = []
    for wi, (a, b, w) in enumerate(words):
        best, ov = None, 0
        for i, (sa, sb) in enumerate(segs):
            o = min(b, sb) - max(a, sa)
            if o > ov: best, ov = i, o
        if best is None:                                 # no speech under it: a hallucinated word, drop it
            continue
        sa, sb = segs[best]
        snapped.append((max(a, sa), min(max(b, sa + 0.05), sb), w, best, wi))
    keep = sorted({s[3] for s in snapped})               # spans without any word = breaths, clicks, noise
    pauses = pauses or {}
    pause_before_seg = {}
    by_word = {s[4]: s[3] for s in snapped}
    for wi, sec in pauses.items():
        sg = by_word[wi]
        pause_before_seg[sg] = pause_before_seg.get(sg, 0) + sec
    out, pos, seg_map = [], PLACE_AT, {}
    pre, post, fade = 0.07, 0.13, S.t2i(0.015)
    prev_end = None
    for i in keep:
        sa, sb = segs[i]
        if prev_end is not None:
            gap = sa - prev_end
            pos += float(np.clip(gap, GAP_MIN, gap_max))
        pos += pause_before_seg.get(i, 0.0)
        a, b = max(0.0, sa - pre), min(len(v) / S.SR, sb + post)
        chunk = v[S.t2i(a):S.t2i(b)].copy()
        if len(chunk) > 2 * fade:
            chunk[:fade] *= np.linspace(0, 1, fade); chunk[-fade:] *= np.linspace(1, 0, fade)
        seg_map[i] = (pos - (sa - a), a)                 # video time of recording time a
        out.append((pos - (sa - a), chunk))
        pos += sb - sa
        prev_end = sb
    total = pos + 0.3
    voice = np.zeros(S.t2i(total + 1), np.float32)
    for t0, ch in out:
        i = S.t2i(t0); voice[i:i + len(ch)] += ch
    vw = []
    for a, b, w, i, _ in snapped:
        if i not in seg_map: continue
        v0, r0 = seg_map[i]
        vw.append((round(v0 + a - r0, 3), round(v0 + b - r0, 3), w))
    return voice, vw, pos


def find_exact(vw, seq):
    """seq: [(key, token)] in speaking order -> {key: video time}. '=w' exact word, 'w#k' k-th match from here."""
    T, i = {}, 0
    for key, tok in seq:
        k = 1
        if "#" in tok: tok, k = tok.split("#"); k = int(k)
        exact = tok.startswith("="); t = norm(tok.lstrip("="))
        j, hits = i, 0
        while j < len(vw):
            nw = norm(vw[j][2])
            if (nw == t) if exact else (t in nw):
                hits += 1
                if hits == k: break
            j += 1
        if j >= len(vw): raise KeyError(f"{key}: «{tok}» not found after word {i} ({vw[i][2] if i < len(vw) else '-'})")
        T[key] = vw[j][0]; i = j + 1
    return T


def find(vw, seq):
    """seq: [(key, token)] in speaking order -> {key: video time}. token may be 'word' or 'word#k' (k-th match from here)."""
    T, i = {}, 0
    for key, tok in seq:
        k = 1
        if "#" in tok: tok, k = tok.split("#"); k = int(k)
        t = norm(tok); j = i; hits = 0
        while j < len(vw):
            if t in norm(vw[j][2]) or norm(vw[j][2]) in t and len(norm(vw[j][2])) > 2:
                hits += 1
                if hits == k: break
            j += 1
        if j >= len(vw): raise KeyError(f"{key}: «{tok}» not found after word {i}")
        T[key] = vw[j][0]; i = j + 1
    return T
