"""timing_all.py (template) - for every recorded part: edit the voice (breaths and noise removed, gaps shortened, dramatic pauses
added), find the key words in the transcript and write proj/times_N.json (video seconds) + proj/vo_N.wav.
Run: python3 timing_all.py [N ...]"""
import sys, os, json
import numpy as np
from scipy.io import wavfile
import voice_edit as V
import basira_sound as S

HERE = os.path.dirname(os.path.abspath(__file__))

# key -> word in the recording, in speaking order. '=w' exact word, 'w#k' k-th match. Numbers in a tuple = offset (s) from a key.
MAP = {
    # worked example from the Sisyphus video, part 12 («لا تجعل الذنب يهزم توبتك»). One list per part.
    12: [("farq", "الفقه"), ("daqiq", "دقيق"), ("shuur", "الشعور"), ("bidhanb", "بالذنب"), ("khizy", "الخزي"),
         ("sakhra", "الصخرة"), ("qaa", "القاع"), ("lihadha", "ولهذا"), ("la", "=لا"), ("tajal", "تجعل"),
         ("dhanb", "الذنب"), ("yahzim", "يهزم"), ("tawbatak", "توبتك"), ("laysat", "وليست"), ("haqiqatuk", "حقيقتك")],
    # a key with no word of its own: (other_key, offset seconds) - e.g. «٢٠١٣» shown just after «البريطانية»
    # 11: [..., ("britaniya", "بريطانية"), ("sana", ("britaniya", 0.45)), ...],
}

# dramatic pauses: (word to pause before, seconds)
PAUSES = {
    3: [("زيوس", 0.4)],                                  # lightning above his head
    12: [("=لا", 0.5), ("الصقطة", 0.5)],                 # the heart of the video (asked for in the part's notes)
    15: [("=لم", 0.5)],                                  # silence after «أتاه الموت» (asked for in the part's notes)
}



def word_index(vw_raw, tok):
    exact = tok.startswith("=")
    t = V.norm(tok.lstrip("="))
    for i, (_, _, w) in enumerate(vw_raw):
        nw = V.norm(w)
        if (nw == t) if exact else (t in nw): return i
    raise KeyError(tok)


def run(n):
    words = V.load_words(n)
    pauses = {}
    for tok, sec in PAUSES.get(n, []):
        pauses[word_index(words, tok)] = sec
    voice, vw, end = V.build(n, pauses)
    T = {}
    seq = []
    for key, tok in MAP[n]:
        if isinstance(tok, tuple): continue
        seq.append((key, tok))
    found = V.find_exact(vw, seq)
    for key, tok in MAP[n]:
        T[key] = found[key] if key in found else round(found[tok[0]] + tok[1], 3)
    keys = [k for k, _ in MAP[n]]
    vals = [T[k] for k in keys]
    bad = [keys[i] for i in range(1, len(vals)) if vals[i] < vals[i - 1]]
    if bad: print(f"  part {n}: out of order: {bad}")
    T["_end"] = round(end, 3)
    json.dump(T, open(os.path.join(HERE, "proj", f"times_{n}.json"), "w"), ensure_ascii=False, indent=1)
    wavfile.write(os.path.join(HERE, "proj", f"vo_{n}.wav"), S.SR, voice)
    print(f"part {n}: voice {end:.1f}s, last key {keys[-1]}={T[keys[-1]]:.2f}")


if __name__ == "__main__":
    for n in [int(x) for x in sys.argv[1:]] or sorted(MAP):
        run(n)
    for d in V.DROPPED: print("  dropped (no speech under it):", d)
    for n, m in V.MUTED: print(f"  part {n}: breaths muted inside phrases: {len(m)}")
