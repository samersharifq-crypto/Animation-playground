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
    "almania":    6.9,   # في ألمانيا
    "waadu":      9.2,   # ووعدوا -> the paper scale
    "akhaf":     10.4,   # أخفّ -> new bottle rises
    "min":       10.9,
    "morphin":   11.4,   # المورفين
    "ikhtaru":   12.5,   # واختاروا له اسمًا -> bottle close-up
    "heroin":    15.2,   # «هيروين» -> letters typed one by one
    "kalima":    16.6,   # من كلمة ألمانية
    "shuja":     18.2,   # «الشجاع» -> HERO turns red, الشجاع on top
    "lakin":     19.3,   # لكنّ البطل لم يكن أخفّ -> back to the scale
    "akhaf2":    20.6,   # أخفّ -> scale slams over
    "chem2":     21.1,   # cut to the chemist, hands on head
    "aqwa1":     21.9,   # بل كان أقوى
    "aqwa1b":    22.5,   # من
    "aqwa1c":    23.0,   # المورفين
    "x2":        24.4,   # بمرّتين -> counter ×2
    "x5":        26.2,   # إلى خمس -> counter ×5
    "medal":     27.0,   # medal falls
    # ---- part 2: الجرعة
    "qabl":      30.0,   # وقبل ذلك بسنوات -> page flip to the factory
    "y1880":     31.9,   # سنة ألف وثمانمئة وثمانين
    "arba":      35.2,   # أربع سجائر -> clock + four cigarettes
    "sajaer":    35.6,
    "machine":   37.3,   # ثم جاءت آلة لفّ السجائر -> machine drops
    "ishrin":    40.3,   # عشرين ألفًا -> cascade, counter 4 -> 20,000
    "alfan":     40.8,
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
