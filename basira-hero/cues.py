"""Cue times (video seconds) for «سمّوه البطل».

These are ESTIMATES until the voice is recorded (P1 starts at 0.0, P2 at P2_START).
After recording, measure each word with the basira-narration-sound skill and replace
the numbers here; every scene, label and sound effect reads from this one table.
"""
P2_START = 30.0
DUR = 65.0

C = {
    # ---- part 1: البطل
    "batal":      0.9,   # سمّوه «البطل»
    "akhtar":     2.6,   # أخطر  -> glass cracks, light dims
    "awakhir":    4.3,   # في أواخر القرن التاسع عشر -> rip to the lab
    "almania":    6.6,   # كان الكيميائيون يبحثون عن مسكّن للألم -> camera pushes in
    "waadu":      9.2,   # أخفّ إدمانًا من المورفين -> the paper scale
    "akhaf":     9.5,   # أخفّ -> new bottle rises
    "min":       10.5,
    "morphin":   10.9,   # المورفين
    "ikhtaru":   12.5,   # فابتكروا مركّبًا جديدًا -> bottle close-up
    "heroin":    16.4,   # «هيروين» -> letters typed one by one
    "kalima":    16.6,   # من كلمة ألمانية
    "shuja":     18.7,   # «شجاع» -> HERO turns red, شجاع on top
    "lakin":     19.6,   # لكنّ البطل لم يكن أخفّ -> back to the scale
    "akhaf2":    20.9,   # أخفّ -> scale slams over
    "chem2":     21.4,   # cut to the chemist, hands on head
    "aqwa1":     22.2,   # بل كان أقوى
    "aqwa1b":    22.8,
    "aqwa1c":    23.2,
    "x2":        24.6,   # بمرّتين -> counter ×2
    "x5":        26.4,   # إلى خمس -> counter ×5
    "medal":     27.2,   # medal falls
    # ---- part 2: الجرعة
    "qabl":      30.0,   # وقبل ذلك بسنوات -> page flip to the factory
    "y1880":     37.4,   # سنة ألف وثمانمئة وثمانين -> 1880 stamped as the machine runs
    "arba":      33.0,   # أربع سجائر -> clock + four cigarettes
    "sajaer":    33.4,
    "machine":   35.3,   # ثمّ اختُرعت آلة لفّ السجائر -> machine drops
    "ishrin":    40.9,   # إلى عشرين ألفًا -> cascade, counter 4 -> 20,000
    "alfan":     41.3,
    "ismen":     14.4,   # واختاروا له اسمًا يليق بالأبطال
    "insan":     42.7,   # الإنسان لم يتغيّر -> cream page
    "lam":       43.2,
    "yataghayar":43.6,
    "alladhi":   44.5,   # الذي تغيّر هو الجرعة
    "taghayar":  44.9,
    "huwa":      45.2,
    "jura":      45.6,
    "aqwa":      46.6,   # أقوى  -> stamp
    "asra":      47.6,   # وأسرع -> stamp
    "akthar":    48.6,   # وأكثر -> stamp
    "yawm":      49.4,   # واليوم -> the navy room
    "daqiqa":    52.3,   # يعطيك في دقيقة -> notifications pour
    "am":        55.2,   # في عام
    "fahal":     56.5,   # فهل صرنا أضعف؟ -> scene fades
    "sirna":     57.0,
    "adaf":      57.5,
    "am2":       58.6,   # أم أنّ الجرعة... صارت أقوى؟
    "anna":      59.0,
    "jura2":     59.4,
    "sarat":     60.4,
    "aqwa2":     60.8,
    "logo":      61.8,   # logo
}

# Real timings from the recorded voice (tools/voice.py) override the estimates above.
import json as _json, os as _os
_f = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "narration", "cues.json")
if _os.path.exists(_f):
    _d = _json.load(open(_f))
    C.update(_d["C"]); DUR = _d["DUR"]; P2_START = _d["P2_START"]
