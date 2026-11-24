# فيديو سيزيف (بصيرة): وين وصلنا

اقرأ هذا الملف أولًا في أي جلسة جديدة، ثم كمّل على نفس الفرع `claude/clever-fermat-y9e0jc`.

## الحالة
- **الأجزاء ١–٨ جاهزة**، كلها بدون صوت والتوقيت تقديري من ملفات PDF.
- آخر نسخة من كل جزء: `sisyphus_part1_v3` و`part2_v2` و`part3_v1` … `part8_v1`.
- النسخة المتصلة: `sisyphus_parts1-8_v1.mp4`، طولها 3:55.
- **الجاي:** الجزء ٩ ثم الباقي لين ١٥. المستخدم يرسل ملف PDF لكل جزء. نعطيه برومبتات الصور اللي يحتاجها، يولّدها في Gemini ويرسلها، ثم نبني المشهد ونرندره.
- **الصوت:** ما وصل لأي جزء. لما يوصل نشغّل مهارة `basira-narration-sound`، ونكتب `proj/times_N.json`. كل `part_N.py` يقرأ هذا الملف ويحدّث التوقيت تلقائيًا.

## طريقة الشغل
- المهارتان `basira-paper-animation` و`basira-narration-sound` تمشيان على كل شي.
- **الرد:** بالعربي ومختصر. بعد كل رندر نقول وش يصير في كل ثانية، والقرارات اللي أخذناها عنه.
- **الترتيب:** ورقة إطارات مفتاحية للفحص، بعدها رندر كامل، ثم نرسل الجزء لحاله + النسخة المتصلة + الورقة.
- **الوجوه:** كل الوجوه ممسوحة بتأثير «حبر ممسوح بالإبهام». المستخدم طلبها كذا.
  - نضيف كل شخصية جديدة إلى `FACES` في `faces.py`. نحدد مكان الوجه على شبكة، ثم نشغّل `python3 faces.py`.
  - النسخ الأصلية محفوظة في `proj/cut_orig/`.
- **برومبتات الصور:** نضيف لكل برومبت: «Isolated on a plain pure white background, no cast shadow, 16:9 landscape canvas, centred». ولأي شي ممكن يطلع عليه كتابة: «no readable text».
- **الأسلوب:**
  - الأجزاء ١–٥ (عالم الأسطورة): شخصيات نقش بني على ورق كريمي، ليل كحلي، وتل بلون الطين.
  - من الجزء ٦ لين ١٣ (كولاج): صور أبيض وأسود من الخمسينات على ورق مربعات فاتح. الدالة `grid_bg` في `part_6.py`، والختم `impression` في نفس الملف.
  - الجزءان ١٤–١٥: صحراء ليلية بأسلوب النقش، بدون رسم ملائكة.
- **الخط:** `font/ReemKufi-Bold.ttf`. ما فيه «٪» العربية، فنستخدم «%» مع الأرقام العربية.

## الملفات
- `basira_engine.py`: المحرك. عدّلناه: `cutout` صار يقبل `hole_margin` و`min_hole`.
- `prep*.py`: قصّ الصور من `src/` إلى `proj/cut/`.
- `part_N.py`: المشهد. الأوامر:
  - `python3 part_N.py keys 1.0,5.0,… out.png` يطلّع ورقة إطارات.
  - `python3 part_N.py a b` يرندر الإطارات من a إلى b، وكل جزء يكتب في `proj/framesN/`.
- الجزء ٥ يستورد التل ومسار الصعود من `part_4.py`، والجزءان ٧ و٨ يستوردان ورق المربعات من `part_6.py`.
- الجزء ٨: تانتالوس (`tantalus_reach`) مقصوص قطعتين بـ`E.pieces`: الرجل والغصن. وصلت معه صور زيادة ما استعملناها: `src/tantalus_stand.png` و`src/pomegranate_tree.png`.
- الصامت والدمج: `ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t DUR -c:a pcm_f32le proj/silenceN.wav`، بعدها `E.encode(..., frames_dir='proj/framesN')`، ثم `ffmpeg -f concat -safe 0 -i proj/concat.txt -c copy`.

## أوامر سريعة
```bash
pip install scipy fonttools        # if missing
cd sisyphus
N=$(python3 -c "import part_9 as p;print(int(round(p.DUR*12)))"); Q=$(( (N+3)/4 ))
(for i in 0 1 2 3; do python3 part_9.py $((i*Q)) $(((i+1)*Q)) & done; wait)
# encode with silence, then concat all parts (see git history of part 7 for the exact lines)
```
