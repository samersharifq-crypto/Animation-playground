import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
for n in sys.argv[1:]:
    f = f"proj/rec/Sp{n}.m4a"
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    audio = np.frombuffer(raw, np.float32)
    segs, info = m.transcribe(audio, language="ar", word_timestamps=True, vad_filter=True, condition_on_previous_text=False, beam_size=5,
                              vad_parameters=dict(min_silence_duration_ms=300))
    words, text = [], []
    for s in segs:
        text.append(s.text)
        for w in s.words: words.append((round(w.start, 2), round(w.end, 2), w.word.strip(), round(w.probability, 2)))
    json.dump({"text": " ".join(text), "words": words}, open(f"proj/asr/Sp{n}.json", "w"), ensure_ascii=False)
    print(n, " ".join(text), flush=True)
    print([w for w in words[-6:]], flush=True)
