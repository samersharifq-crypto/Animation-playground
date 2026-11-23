"""Word timings for the narration (local faster-whisper, prompted with the script)."""
import json, sys
import numpy as np
from scipy.io import wavfile
from faster_whisper import WhisperModel
PROMPT = {
 "P1": "في ليلة واحدة… أغلقت كل حانات أمريكا. سنة ألف وتسعمئة وعشرين، صار بيع الخمر جريمة. غضب الناس، وظهر المهربون والعصابات. لكن حدث شيء لم يتوقعه كثيرون… أمراض الكبد التي تسببها الخمر… انخفضت إلى النصف.",
 "P2": "الناس لم يتغيروا… الذي تغير هو المسافة بينهم وبين الكأس. وحين رفع الحظر سنة ألف وتسعمئة وثلاث وثلاثين، وصارت الخمر في المتناول من جديد… عادت الأرقام ترتفع مع السنين. فالقاعدة بسيطة: كلما قرب الشيء… زاد استهلاكه. واليوم، أقرب ما يدمنه الناس لا يبعد عنك شبرا… إنه في جيبك. فإن أردت أن تقلل منه… فابدأ بالمسافة.",
}
m = WhisperModel(sys.argv[1] if len(sys.argv) > 1 else "small", device="cpu", compute_type="int8")
out = {}
for p in ("P1", "P2"):
    audio = wavfile.read(f"voice/{p}.16k.wav")[1].astype(np.float32) / 32768
    segs, _ = m.transcribe(audio, language="ar", word_timestamps=True, initial_prompt=PROMPT[p], vad_filter=False)
    out[p] = [(w.word.strip(), round(w.start, 2), round(w.end, 2)) for s in segs for w in s.words]
    print(p, " ".join(f"{w}[{a}-{b}]" for w, a, b in out[p]))
json.dump(out, open("voice/words.json", "w"), ensure_ascii=False, indent=0)
