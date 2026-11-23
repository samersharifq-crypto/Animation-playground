"""Sync the film to the recorded narration.
Scenes keep their original (script) timing; a piecewise-linear warp maps every video frame to script time,
anchored on the spoken words. Labels are rebuilt directly on the measured word times.
Usage: python3 film_sync.py warp            -> writes proj/warp.json
       python3 film_sync.py <first> <last>  -> renders frames into proj/film_sync/"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import film as F
import basira_engine as E

TM = json.load(open(os.path.join(F.E.ROOT, "timing.json")))
PH = TM["phrases"]


def w(word, n=1):
    """video time of the n-th occurrence of `word` in the narration"""
    k = 0
    for p in PH:
        for wd, t in p["words"]:
            if wd == word:
                k += 1
                if k == n: return t
    raise KeyError(word)


def end_of(text):
    return next(p["end"] for p in PH if p["text"] == text)


VEND = TM["voice_end"]
# (script time, video time): visual beats pinned to the spoken words
ANCHORS = [
    (0.0, 0.0), (1.9, w("أغلقت")), (4.2, w("سنة") - 0.85), (5.0, w("سنة")), (5.6, w("ألف")),
    (7.0, w("صار") - 0.4), (8.6, w("جريمة")),
    (10.0, w("غضب") - 0.3), (12.0, w("وظهر")), (13.3, w("والعصابات")),
    (15.5, w("لكن") - 0.35), (19.5, w("أمراض") - 0.6), (20.0, w("أمراض")), (23.2, w("انخفضت")), (24.3, w("النصف")),
    (28.0, w("الناس", 2) - 0.4), (31.6, w("المسافة")),
    (33.0, w("وحين") - 0.3), (33.9, w("رفع")), (34.6, w("سنة", 2)),
    (36.0, w("وصارت") - 0.1), (36.6, w("وصارت") + 0.5), (37.5, w("ترتفع")),
    (38.6, w("فالقاعدة") - 0.35), (40.6, w("كلما")), (42.0, end_of("كلما قرب الشيء")), (42.6, w("زاد")),
    (44.0, w("واليوم") - 0.15), (48.0, w("شبرا")), (50.2, w("جيبك")),
    (51.0, w("فإن") - 0.35), (52.4, w("تقلل")), (55.4, w("بالمسافة")),
    (57.4, VEND + 0.45),
]
ANCHORS.append((F.DUR, ANCHORS[-1][1] + (F.DUR - 57.4)))
OLD = np.array([a for a, _ in ANCHORS]); NEW = np.array([b for _, b in ANCHORS])
assert np.all(np.diff(NEW) > 0), "anchors must increase"
DUR = float(NEW[-1])


def to_old(T): return float(np.interp(T, NEW, OLD))
def to_new(t): return float(np.interp(t, OLD, NEW))


def L(text, reds, words, hide):
    return E.Label(text, reds, [w(*x) if isinstance(x, tuple) else w(x) for x in words], hide=hide)

LABELS = [
    L("في ليلة واحدة أُغلقت", ("أُغلقت",), ["في", "ليلة", "واحدة", "أغلقت"], w("سنة") - 1.0),
    L("غضب الناس", (), ["غضب", ("الناس", 1)], w("وظهر") - 0.12),
    L("وظهر المهربون والعصابات", ("العصابات",), ["وظهر", "المهربون", "والعصابات"], w("لكن") - 0.4),
    L("لكن حدث شيء", (), ["لكن", "حدث", "شيء"], w("لم") - 0.1),
    L("لم يتوقعه كثيرون", (), ["لم", "يتوقعه", "كثيرون"], w("أمراض") - 0.65),
    L("أمراض الكبد", (), ["أمراض", "الكبد"], w("انخفضت") - 0.12),
    L("انخفضت إلى النصف", ("إلى", "النصف"), ["انخفضت", "إلى", "النصف"], w("الناس", 2) - 0.45),
    L("الناس لم يتغيروا", (), [("الناس", 2), ("لم", 2), "يتغيروا"], w("الذي") - 0.12),
    L("الذي تغيّر هو المسافة", ("المسافة",), ["الذي", "تغير", "هو", "المسافة"], w("وحين") - 0.35),
    L("رُفع الحظر", (), ["رفع", "الحظر"], w("سنة", 2) - 0.1),
    L("سنة 1933", ("1933",), [("سنة", 2), ("ألف", 2)], w("وصارت") - 0.15),
    L("في المتناول من جديد", ("جديد",), [("في", 2), "المتناول", "من", "جديد"], w("عادت") - 0.12),
    L("عادت الأرقام ترتفع", ("ترتفع",), ["عادت", "الأرقام", "ترتفع"], w("فالقاعدة") - 0.4),
    L("القاعدة بسيطة", (), ["فالقاعدة", "بسيطة"], w("كلما") - 0.1),
    L("كلما قرب الشيء زاد", ("قرب", "زاد"), ["كلما", "قرب", "الشيء", "زاد"], w("واليوم") - 0.2),
    L("واليوم", (), ["واليوم"], w("أقرب") - 0.1),
    L("أقرب ما يدمنه الناس", (), ["أقرب", "ما", "يدمنه", ("الناس", 3)], w("لا") - 0.1),
    L("لا يبعد عنك شبرًا", ("شبرًا",), ["لا", "يبعد", "عنك", "شبرا"], w("إنه") - 0.1),
    L("إنه في جيبك", ("في", "جيبك"), ["إنه", ("في", 3), "جيبك"], w("فإن") - 0.4),
    L("فإن أردت أن تقلل منه", (), ["فإن", "أردت", "أن", "تقلل", "منه"], w("فابدأ") - 0.1),
    L("فابدأ بالمسافة", ("بالمسافة",), ["فابدأ", "بالمسافة"], VEND + 0.4),
]
OUT = os.path.join(F.E.ROOT, "film_sync"); os.makedirs(OUT, exist_ok=True)


def render_frame(f):
    T = f / F.FPS; t = to_old(T)
    i = F.scene_at(t); s = F.SCENES[i]
    cur = F.draw_scene(i, t, f)
    if i > 0 and s[3] and t - s[0] < s[4]:
        prev = F.draw_scene(i - 1, t, f)
        pf = F.FOCUS.get(F.SCENES[i - 1][2].__name__[3:], (F.W / 2, F.H / 2)); cf = F.FOCUS.get(s[2].__name__[3:], (F.W / 2, F.H / 2))
        cur = F.transition(s[3], prev, cur, (t - s[0]) / s[4], f, pf, cf)
    if not (4.2 <= t < 10.0):
        E.draw_labels(cur, LABELS, T, f)
    if F.IRIS_END[0] <= t < F.IRIS_END[1]:
        u = min(1, (t - F.IRIS_END[0]) / (F.IRIS_END[1] - F.IRIS_END[0]))
        cur = F.iris(cur, F.FOCUS.get("drawer", (F.W / 2, F.H / 2)), 1500 * (1 - u) ** 1.6)
    arr = np.asarray(cur.convert("RGB")).astype(float)
    if t < F.T_TODAY:
        arr = F.old_film(arr, f, 1.4 if 4.2 <= t < 7.0 else 1.0)
    if T < 0.25: arr *= T / 0.25
    arr = arr + np.random.default_rng(1000 + f).normal(0, 7 if t < F.T_TODAY else 4, (F.H, F.W, 1))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").save(os.path.join(OUT, f"{f:05d}.png"))


NFRAMES = int(round(DUR * F.FPS))

if __name__ == "__main__":
    if sys.argv[1] == "warp":
        json.dump(dict(old=OLD.tolist(), new=NEW.tolist(), dur=DUR,
                       labels=[L_.times for L_ in LABELS]), open(os.path.join(F.E.ROOT, "warp.json"), "w"))
        print("dur", round(DUR, 2), "frames", NFRAMES)
    else:
        a, b = int(sys.argv[1]), min(int(sys.argv[2]), NFRAMES)
        for f in range(a, b): render_frame(f)
