---
name: "basira-paper-animation"
description: "Animate a بصيرة video part by part: image prompts for Gemini, cut-outs, smudged faces, backgrounds, torn-paper stop-motion, collage on grid paper, word-by-word Arabic labels synced to the voice, lightning, drains, glitch flickers, phone-safe MP4, joined full video. Use whenever the user sends a بصيرة part (a PDF with narration, shots and image list), images for a part, or asks to change a scene, continue a بصيرة video, or join the parts."
---

# بصيرة: torn-paper stop-motion animation

Use when the user sends a part of a بصيرة video (usually a PDF: narration, shots with the key word for each, label strips, image list with prompts, sound notes), the images for it, or asks to change a scene. The script comes from `basira-story-script`; the real voice timing and the audio from `basira-narration-sound`. The user does not want to re-explain the style: apply everything below by default and only ask about real creative choices.

## How to talk to the user

- Short Arabic (Gulf/Saudi register is fine, the user writes that way).
- After every render: what happens at which second (one line per beat, tied to the spoken word), then the decisions you took on their behalf (extra strips, colours, anything that differs from their PDF), so they can veto them.
- When the voice is not there yet, say the timing is an estimate.

## 0. Setup (once per video)

1. Copy `scripts/basira_engine.py` (and `scripts/collage.py`, `scripts/faces.py`) next to the part scripts. `pip install scipy fonttools` if missing.
2. **Font:** Reem Kufi Bold (`font/ReemKufi-Bold.ttf`). If the project has none, ask the user for the Google Fonts ZIP. It has no Arabic «٪»: write «%» with Arabic digits (٢٠%).
3. `E.setup(project_dir, font_path)` creates `cut/ bg/ frames/`. Each part renders into its own `proj/framesN/`.
4. Keep a `HANDOFF.md` in the video folder: status, latest file of every part, decisions waiting for the user, file map, quick commands. Update it after every part and read it first in a new session. Work on the branch the user names.
5. **Git:** rendered frames are huge. Before the first commit add a `.gitignore` with `proj/frames*/`, `proj/keys*/`, `proj/*.wav`, `__pycache__/`. (A list of `frames1/ … frames10/` silently let part 11+ frames into the history once.) Commit scripts, cut-outs, sources, times, recordings and the MP4s.

## 1. Per-part workflow

1. Read the part's PDF. Reply with the **image prompts** it needs (only new images: check `src/` and `proj/cut/` for what exists), ready to paste into Gemini, then wait for the images.
2. Cut out → contact sheet on navy → smudge faces → write `part_N.py` → key-frame sheet → **look** → fix → full render → encode → join with the previous parts → send the part alone + the joined video + the key-frame sheet → update `HANDOFF.md` → commit and push.
3. The PDFs say "don't render fully before the user approves the key-frame sheet". The user accepted rendering fully and sending everything together; keep doing that and mention it among the decisions.

### Image prompts for Gemini

Take the PDF's prompt and add: «Isolated on a plain pure white background, no cast shadow, 16:9 landscape canvas, centred, nothing else in frame.» Add «no readable text» for anything that could carry writing (maps, books, cameras, planes: also «no logos»). Backgrounds are full-frame 16:9 and not isolated. Useful extras:
- A character pose: «The same character from the attached image …, same face, …» and ask the user to attach the reference (e.g. `sisyphus_walk.png`).
- Before/after of the same person (upright → slumped): attach the first image, ask for the same clothes, chair, camera angle and size in frame, so the swap reads as movement.
- A plane, arrow or hand: say which way it points (the story reads right→left; the hill rises to the right).
- If an image comes back in colour: «monochrome sepia only». Don't remove the white background yourself.
- Never ask for faces of the hadith people, scientists or angels (see style).

## 2. Assets

- `E.cutout(name, path, border=10, min_hole=…, hole_margin=…, white_min=228)`:
  - things with see-through gaps (chair slats, tripod, chain links, a seated man's legs): `min_hole=150, hole_margin=3`.
  - pictures on an off-white background (Gemini's "white" is often ~244): `white_min=236`; a **white object on white** (a jet): `white_min=249`.
  - photo-like images (an old print, a map) come out as a torn paper print with a cream border: fine for the collage.
- Sheets with several objects → `E.pieces(name)` / `E.piece_h(name, i, h)`.
- Look at every new cut-out on a navy contact sheet with a pixel ruler (also how you find faces, windows, palms, feet in cut-out pixels).
- **Faces are smudged** ("ink rubbed by a thumb") on every person, as the user asked. Add each new cut-out to `FACES` in `faces.py` (centre and radii in cut-out px, several per picture is fine), run `python3 faces.py`; originals are kept in `proj/cut_orig/`. Mirrored copies (`*_l`) are made after the smudge. Back-of-head and very small faces need no entry.
- Backgrounds (16:9) → `bg/<name>.png`, used with `E.image_bg(name, f, pan, zoom, blur, sat, ox, center)`.
- A logo the user sends: keep it exactly as sent (colours, proportions), don't boil it; you may split mark and wordmark to animate them in.

## 3. Look & motion rules (agreed with the user)

- 1920×1080 at **12 fps** (stop-motion), encoded at 24 fps. Every placed piece boils (`seed`/`f`). Paper grain + vignette on every frame.
- Palette: navy (24,34,54), cream (244,236,220), ink (22,30,48), brick red (178,62,42) for highlighted words, gold.
- **Worlds by chapter** (the video's style note decides; Sisyphus used):
  - Myth: brown/sepia engraving characters on cream paper, navy night, clay-coloured hill, cream moon. (Older videos used orange red-figure characters and `match_orange`; don't use it on sepia engravings.)
  - Science: collage of old 1950s black-and-white photos on light grid paper (`collage.grid_bg`), red rubber stamps (`collage.impression`).
  - Prophetic/hadith story: night desert in engraving style; the man only from behind or as a shadow; **no angels drawn** (two lights only, warm and cold); scholars/monks shown only by their places and light; scientists only as a name strip, never a picture.
- Scene changes: torn-paper rip right→left, 0.5 s (`E.Scene(..., rip=True)`). A vertical torn seam can split the screen in two (two worlds side by side); one half can then tear off and fall.
- **Labels:** cream torn strip, words ink in **one by one exactly when the narrator says them**, highlighted words brick red; pop 0.6→1.08→0.97 and a jolt on each word. Move a strip sideways (`x=`) or down when it would cover a face or a key object. Big single words (الخزي, الانتكاسة) can sit mid-screen at size 150–190. Strips the PDF doesn't list are welcome when they carry the key fact (a name, a year, a number) — list them as decisions.
- **Pose swaps:** draw every image of the same character at one scale and with the feet on the same point, so a swap (fallen → kneeling → standing; upright → slumped) reads as movement. Compute crowns, feet, palms, windows from the cut-out's alpha or from a gridded sheet, never guess.
- Key actions land on spoken words (walk-in on the line that introduces him, a stamp on «فاشل», a number torn from ٢٠% to ٥% on «خمسة»).
- Fall/turning point: pause in the voice, lightning above the head (`E.lightning`), `E.drain` to navy.
- Myth ↔ modern flicker: 2–4-frame flashes of the modern room on key words, `E.glitch` on switches.
- Effects that worked: numbers written in the sand and erased by wind (noise-mask erosion), a shadow growing on the wall and morphing into the rock (signed-distance-field blend of two silhouettes), a measuring rope that swings over the other rope to show «أقرب بشبر», a paper ocean in torn bands with a dashed flight path and a two-screen-wide world the camera pans across, a camera viewfinder overlay (REC, timecode), 46 chairs ticking into rows, a speech bubble that rips in two, dominoes of day-squares.
- Endings that lead into the next part: a push-in toward a light, or a tear into the next world (e.g. collage → night desert).

## 4. Building a part

```python
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import basira_engine as E
HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(os.path.join(HERE, "proj"), os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
OUT = os.path.join(HERE, "proj", "framesN"); os.makedirs(OUT, exist_ok=True)
# key words in video seconds: estimates until the voice arrives, then basira-narration-sound writes proj/times_N.json
T = dict(hunak=0.0, harb=2.0, ishrin=5.0, ...)
_tj = os.path.join(HERE, "proj", "times_N.json")
if os.path.exists(_tj): T.update(json.load(open(_tj)))
DUR = T["last_key"] + 2.6
DUR = max(DUR, T.get("_end", 0) + 1.2)                 # never cut the recorded voice
def scene_a(t, f, c): ...                              # everything derives from T, never from fixed seconds
SCENES = [E.Scene(0, T["x"] - 0.4, scene_a, bg=None), ...]
LABELS = [E.Label("عشرين بالمئة", ("عشرين", "بالمئة"), [T["ishrin"], T["bilmia"]], hide=...)]
def post(arr, t, f, idx): return arr
if __name__ == "__main__":
    if sys.argv[1] == "keys":                          # python3 part_N.py keys 1.0,5.0,... sheet.png
        ts = [float(x) for x in sys.argv[2].split(",")]
        out = os.path.join(HERE, "proj", "keysN"); os.makedirs(out, exist_ok=True)
        for tt in ts: E.frame(int(round(tt * E.FPS)), SCENES, LABELS, DUR, post, out)
        E.contact_sheet(ts, sys.argv[3], out_dir=out)
    else:                                              # python3 part_N.py a b
        a, b = int(sys.argv[1]), int(sys.argv[2])
        E.render(SCENES, LABELS, DUR, frames=range(a, min(b, int(round(DUR * E.FPS)))), post=post, out_dir=OUT)
```

Every time and boundary comes from a `T` key (a word), so when the real voice arrives the whole part re-times itself. Parts can import each other (the same hill, the grid paper). Keep one key per event, in speaking order.

## 5. Render loop (always look before rendering everything)

1. Key-frame sheet (8–12 beats) → **Read it and look**: covered faces, labels over key elements, a hand not touching the rock, floating objects, cut ends of arms showing, something hidden by another layer, a number too faint, a world showing where it shouldn't (an ocean over Vietnam).
2. Fix and re-check, then render in 4 parallel processes:
   `N=$(python3 -c "import part_N as p;print(int(round(p.DUR*12)))"); Q=$(( (N+3)/4 )); (for i in 0 1 2 3; do python3 part_N.py $((i*Q)) $(((i+1)*Q)) & done; wait)`
3. Without a voice: `ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t DUR -c:a pcm_f32le proj/silenceN.wav`, then `E.encode(wav, out_mp4, DUR, frames_dir=OUT)` (phone-safe: main profile, CRF 30, AAC stereo 44.1 kHz; ~3–6 MB per 30 s).
4. Join: a `concat.txt` of the part MP4s → `ffmpeg -f concat -safe 0 -i concat.txt -c copy full.mp4` (all parts share codec settings, so no re-encode).
5. Send with `SendUserFile(display="attach")`, a new filename per version (`_v2`, `_v3`).

If a video won't open on the phone: check with ffprobe, resend smaller (stereo, main profile).

## 6. Vertical Shorts (1080×1920)

Recompose, don't letterbox: `E.W, E.H = 1080, 1920`, recompute `E.VIG`; backgrounds scaled to height with a stepped travel; characters in y ≈ 600–1500; labels at y ≈ 360, ≤ 960 px wide (bottom 25% and right edge are covered by YouTube). Lead with the promise in the voice within 3–4 s, tighten the story to ~25 s (viewers stay 2–3 s, ~75% leave between 3 and 12 s). Loop: end on a tear back into the first frame; no fades. Upload tips: title = the promise; `#shorts` + story tags, never the hidden topic; "not made for kids"; a 1080×1920 cover from the strongest frame; custom Shorts thumbnails are changed on studio.youtube.com (desktop site).

## 7. Publishing help

When asked for a title/description: 2–3 title options with one recommended (story first, a question that touches the viewer, don't spoil the reveal), a description with a hook, the viewer question from the ending, chapters computed from the real part lengths, sources from the part PDFs (only what they state), the channel line «بصيرة… نرى ما وراء الحكاية / تاريخ · علوم · وثائقيات · تأملات», a few hashtags. Save it as `YOUTUBE.md` in the video folder.

## Engine and helpers

- `scripts/basira_engine.py`: cut-outs, textures, paste/walk/drop/pivot, word-by-word labels, tear transitions, drain, lightning, glitch, render loop, contact sheet, encode.
- `scripts/collage.py`: grid paper and rubber-stamp impressions for the science chapters.
- `scripts/faces.py`: the thumb-smudge for faces.
- A complete worked video (16 parts, every effect above) lives in the user's repo `animation-playground`, folder `sisyphus/` (`part_1.py` … `part_16.py`, `HANDOFF.md`).
