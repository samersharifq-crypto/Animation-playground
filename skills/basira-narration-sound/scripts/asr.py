"""asr.py - word-timed transcript of each recording with faster-whisper large-v3 (CPU, int8).
Usage (from the project dir): python3 asr.py 1 2 3 ...   reads proj/rec/SpN.m4a -> proj/asr/SpN.json
Needs: pip install faster-whisper (the model downloads from Hugging Face the first time, ~3 GB).
Audio goes in as a numpy array: passing the file path crashed with the installed PyAV version."""
import sys, os, json, subprocess, numpy as np
from faster_whisper import WhisperModel

m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
os.makedirs("proj/asr", exist_ok=True)
for n in sys.argv[1:]:
    f = f"proj/rec/Sp{n}.m4a"
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    audio = np.frombuffer(raw, np.float32)
    # vad_filter + no conditioning: without them whisper invents «اشتركوا في القناة» / «شكرا» / «ترجمة …» on silences
    # and can skip the first sentence of a recording
    segs, info = m.transcribe(audio, language="ar", word_timestamps=True, vad_filter=True,
                              condition_on_previous_text=False, beam_size=5,
                              vad_parameters=dict(min_silence_duration_ms=300))
    words, text = [], []
    for s in segs:
        text.append(s.text)
        for w in s.words: words.append((round(float(w.start), 2), round(float(w.end), 2), w.word.strip(), round(float(w.probability), 2)))
    json.dump({"text": " ".join(text), "words": words}, open(f"proj/asr/Sp{n}.json", "w"), ensure_ascii=False)
    print(n, " ".join(text), flush=True)
