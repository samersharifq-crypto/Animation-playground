"""timing_all.py - for every recorded part: edit the voice (breaths and noise removed, gaps shortened, dramatic pauses
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
    1: [("qabl", "قبل"), ("korintha", "كورنثا"), ("aash", "عاش"), ("sisyphus", "سيزف"), ("makran", "مكر"), ("wahina", "وحين"),
        ("mawt", "الموت"), ("lam_yahrub", "=لم"), ("ibtasam", "ابتسم"), ("arini", "أرني"), ("famadda", "فمد"),
        ("faaghlaqaha", "فأغلقها"), ("lakin", "=لكن"), ("fasakhra", "فصخرة"), ("ilal_yawm", "=إلى"), ("warubbama", "وربما"),
        ("dahrajtaha", "حرجتها"), ("anta", "أنت"), ("ams", "أمس")],
    2: [("quyyid", "قيد"), ("fatawaqqaf", "فتوقف"), ("almawt", "الموت"), ("ashaykh", "شيخ"), ("wala_jarih", "جريح"),
        ("ghadibat", "غضبت"), ("ilah_alharb", "=اله"), ("qaydahu", "قيده"), ("waakhadh", "وأخذ"), ("marratan", "مرة"),
        ("ukhra", "أخر"), ("yawman", "يوما"), ("faad", "فعاد"), ("walam", "=ولم"), ("yadhak", "يضحك"), ("ala", "=على"),
        ("almawt2", "الموت")],
    3: [("lakin", "=لكن"), ("maat", "سيزف"), ("zeus", "زيوس"), ("bilnar", "بالنار"), ("wala", "=ولا"), ("sakhra", "صخرة"),
        ("watall", "وتلا"), ("hatta", "=حتى"), ("alqimma", "القمة"), ("alaysa", "أليس"), ("fawada", "فوضع"), ("yadfa", "يدفع")],
    4: [("khutwa", "خطوة"), ("thumma", "=ثم"), ("araq", "العرق"), ("yaqtarib", "يقترب"), ("ala", "=على"), ("bud", "=بعد"),
        ("dhira", "ذراع"), ("intasar", "انتصر"), ("aflatat", "تت"), ("alqa", "القاع"), ("saqat", "وسقط"), ("ala2", "=على"),
        ("wajhih", "وجهه")],
    5: [("nahad", "نعض"), ("min_jadid", "=من"), ("wafi", "=وفي"), ("iqab", "العقاب"), ("awda", "العودة"), ("ila", "=إلى"),
        ("bidaya", "البداية"), ("akhbirni", "أخبرني"), ("hadhihi", "=هذه"), ("akhir", "=آخر"), ("marra", "=مرة"),
        ("aadat", "عادت"), ("sakhra", "الصخرة")],
    6: [("sijara", "سجار"), ("shasha", "شاشة"), ("aada", "عادة"), ("intikasa", "الانتكاسة"), ("fashilna", "فشلنا"),
        ("duafa", "ضعف"), ("lan", "=ولن"), ("ilm", "العلم"), ("tariqa", "بطريقة"), ("mukhtalifa", "مختلفة"), ("tamaman", "تماما")],
    7: [("yaqul", "يقول"), ("arbain", "أربعين"), ("wasittin", "ستين"), ("bilmia", "بالمئة"), ("daght", "الضغط"), ("rabw", "والر"),
        ("anta", "=أنت"), ("fashil", "فاشل"), ("la", "=لا"), ("tani", "تعني"), ("an", "=أن"), ("ilaj", "العلاج"),
        ("fashal", "=فشل"), ("tadil", "تعديلا")],
    8: [("fidyo", "فيديو"), ("laysa", "=ليس"), ("ladha", "لذة"), ("bal", ("raghba", -0.35)), ("raghba", "الرغبة"), ("makan", "بمكان"),
        ("waqt", "وبوقت"), ("shuur", "وبشعور"), ("tamurr", "=تمر"), ("malal", "بالملل"), ("tashtail", "لتشتعل"),
        ("qimma", "القمة"), ("back", "=ليس"), ("damaghak", "دماغك"), ("yatadhakkar", "يتذكر")],
    9: [("khabar", "خبر"), ("aam", "=عام"), ("nura", "نورا"), ("folko", "فولكو"), ("ashhur", "أشهر"), ("jadid", "جديد"),
        ("sana", "=سنة"), ("irtafaat", "ارتفعت"), ("yastati", "يستطيع"), ("an", ("yataafa", -0.28)), ("yataafa", "تعاف"),
        ("lakinnahu", "لكنه"), ("waqtan", "وقتا")],
    10: [("alan", "=ألم"), ("marlat", "مارلات"), ("khata", "الخط"), ("yaquluna", "يقولونه"), ("sijara", "سجار"),
         ("shahrayn", "شهرين"), ("khalas", "خلاص"), ("kharabt", "خربت"), ("kull", "=كل"), ("shay", "شيء"), ("faukmil", "=فلا"),
         ("athar", "=أثر"), ("khark", "خلق"), ("imtina", "الامتناع"), ("inhiyar", "انهيار"), ("fikra", "فكرة"), ("wahida", "واحدة")],
    11: [("am", "=عام"), ("sawwar", "=صور"), ("jamia", "جامعة"), ("kulumbiya", "كولوم"), ("britaniya", "بريطانية"),
         ("sana", ("britaniya", 0.45)), ("sitta", "46"), ("arbain", ("sitta", 0.4)), ("mutaafin", "متعافي"), ("kuhul", "الكحول"),
         ("yatahaddathun", "يتحدثون"), ("lam", "=ولم"), ("ajsad", "أجسادهم"), ("aktaf", "الأكتاف"), ("munhaniya", "المنحنية"),
         ("sadr", "والصدر"), ("munkamish", "المنكمش"), ("alamat", "علامات"), ("khizy", "الخزي"), ("baad", "وبعد"),
         ("ashhur", "أشهر"), ("akthar", "=أكثر"), ("intikasan", "انتكاسا"), ("akthar2", "وأكثر"), ("shurban", "شربا"),
         ("intakasu", "انتكس")],
    12: [("farq", "الفقه"), ("daqiq", "دقيق"), ("yughayyir", "يغير"), ("shuur", "الشعور"), ("bidhanb", "بالذنب"),
         ("faalt", "فعلت"), ("falusliha", "فلأصلحه"), ("amma", "=أما"), ("khizy", "الخزي"), ("ana", "=أنا"), ("sayyi", "=سيء"),
         ("amal", "=أمل"), ("awwal", "الأول"), ("yuiduk", "يعيدك"), ("sakhra", "الصخرة"), ("thani", "والثاني"),
         ("yujlisuk", "يجلسك"), ("qaa", "القاع"), ("lihadha", "ولهذا"), ("la", "=لا"), ("tajal", "تجعل"), ("dhanb", "الذنب"),
         ("yahzim", "يهزم"), ("tawbatak", "توبتك"), ("saqta", "الصقطة"), ("fil", "=فعل"), ("hadath", "=حدث"),
         ("laysat", "وليست"), ("haqiqatuk", "حقيقتك")],
    13: [("hunak", "وهناك"), ("dars", "درس"), ("harb", "=حرب"), ("vietnam", "فتنام"), ("adman", "أدمن"), ("ishrin", "20"),
         ("bilmia", ("ishrin", 0.45)), ("heroin", "الهيروين"), ("khaf", "وخاف"), ("awdatihim", "عودتهم"), ("lakin", "=لكن"),
         ("alima", "عالمة"), ("li", "=لي"), ("robins", "روبينز"), ("tabaat", "تابعتهم"), ("fawajadat", "فوجدت"),
         ("khamsa", "5"), ("bilmia2", ("khamsa", 0.4)), ("intakasu", "انتكسوا"), ("sana", "السنة"), ("ard", "الأرض"),
         ("rifaq", "الرفاق"), ("muthirat", "المثيرات"), ("fataghayyar", "فتغير"), ("insan", "الإنسان"), ("yara", "ويرى"),
         ("min", "=من#2"), ("aqwa", "أقوى"), ("durus", "دروس"), ("taafi", "التعافي")],
    14: [("hadha", "وهذا"), ("hadith", "حديث"), ("qabl", "=قبل"), ("qarnan", "قرن"), ("rajul", "=رجل"), ("qatala", "=قتل"),
         ("tisa", "تسعة"), ("tisin", "وتسعين"), ("nafsan", "نفسا"), ("rahiban", "راهبا"), ("hal", "=هل"), ("tawba", "توبة"),
         ("la", "=لا"), ("faatamma", "فأتم"), ("mia", "المئة"), ("thumma", "=ثم"), ("alim", "عالما"), ("naam", "نعم"),
         ("waman", "=ومن"), ("yahul", "يحول"), ("baynahu", "بينه"), ("wabayn", "وبين"), ("tawba2", "التوبة"),
         ("intaliq", "انطلق"), ("ard", "=أرض"), ("kadha", "=كذا"), ("unasan", "أناس"), ("latarji", "ترجع"),
         ("ardik", "أرضك"), ("ardu", "=أرض"), ("su", "سوء")],
    15: [("fakharaj", "فخرج"), ("muntasaf", "منتصف"), ("tariq", "الطريق"), ("atahu", "أتاه"), ("mawt", "الموت"),
         ("lam", "=لم"), ("yasil", "يصل"), ("ikhtasamat", "فاختصمت"), ("malaika", "ملائكة"), ("rahma", "الرحمة"),
         ("adhab", "العذاب"), ("faqila", "فقيل"), ("qisu", "قيس"), ("ardayn", "الأرضين"), ("fawajaduh", "فوجدوه"),
         ("salih", "الصالحة"), ("aqrab", "أقرب"), ("shibr", "بشبر"), ("faghufir", "فغفر"), ("lahu", "=له"), ("lam2", "=لم"),
         ("yutlab", "يطلب"), ("yasil2", "يصل"), ("bal", "=بل"), ("an", "=أن"), ("yattajih", "يتجه"), ("yatruk", "يترك"),
         ("ard3", "الأرض"), ("tasna", "تصنع"), ("suqut", "سقوطه")],
    16: [("sizif", "سيزف"), ("khiyar", "خيارا"), ("hakamat", "حكمت"), ("yaud", "يعود"), ("qaa", "القاع"), ("abad", "الأبد"),
         ("amma", "=أما"), ("anta", "=أنت"), ("falasta", "فلست"), ("sizif2", "سيزف"), ("kull", "=كل"), ("khatta", "خط"),
         ("khayr", "وخير"), ("khattain", "خطائين"), ("tawwabun", "التوابون"), ("fain", "فإن"), ("aflata", "أفلتت"),
         ("sakhra", "الصخرة"), ("latajlis", "=لا"), ("qaa2", "القاع"), ("da", "=ضع"), ("yadayk", "يديك"), ("jadid", "جديد"),
         ("waghayyir", "وغير"), ("tariq", "الطريق"), ("tasad", "تصعد"), ("akhbirni", "أخبرني"), ("taaliqat", "التعليقات"),
         ("saadak", "ساعدك"), ("nuhud", "النهوض"), ("suqut", "سقوط"), ("basira", "صير"), ("nara", "نرى"), ("wara", "ورا"),
         ("hikaya", "الحكاية")],
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
