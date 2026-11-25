---
name: "basira-narration-sound"
description: "Clean a بصيرة narration so only the voice remains (breaths, clicks, noise and gaps removed), transcribe it with word timings, sync every animated event to the spoken words, add dramatic pauses, and build a no-music paper-foley sound design (tears, pops, thunder, wind, glitches), then mix and join the full video. Use whenever the user sends voice recordings (.m4a from the phone) for a بصيرة video or a part of it, asks to merge the voice with the video, or complains about breaths, gaps or the sound."
---

# بصيرة: narration, timing and sound design

Use when the user sends voice recordings (usually `Sp1.m4a`, `Sp2.m4a` … one per part, plus maybe `Short_s.m4a`) or asks to change the audio. Works with `basira-paper-animation`: every part script reads `proj/times_N.json` (key word → video second), so once the voice is timed, re-rendering the part re-syncs every label, cut and effect.

## What the user wants (decided, don't re-ask)

- **Only their voice.** No breaths, no lip smacks, no clicks, no room noise, no room-tone bed under the voice. They checked a first version and still heard inhales: be strict.
- **No gaps.** Shorten every pause to half its length, never longer than ~0.32 s. Extra pauses only where the part's notes ask for them (e.g. before and after the heart line, after «أتاه الموت», before the lightning), ~0.4–0.5 s.
- **Light processing** of the voice itself (`preset="light"`); the heavier «موزون» preset sounded over-processed.
- **No music.** Synthesized sound effects instead; one held warm tone is fine for "light", never a melody.
- Effects duck under the voice where they overlap.
- Missing recordings: say which part is missing right away (e.g. no `Sp9`), keep going with the others, and finish that part when it arrives.

## Pipeline (scripts in `scripts/`, run from the video folder)

1. Copy the recordings to `proj/rec/SpN.m4a`.
2. **Transcribe with word timings:** `pip install faster-whisper`, then `python3 asr.py 1 2 3 …` → `proj/asr/SpN.json` (large-v3, ~40 s per 30-s part on 4 CPU cores). Read the transcripts: they are also the narration text when the user's script isn't at hand.
   - Whisper invents «اشتركوا في القناة», «شكرا», «ترجمة …» on silences and can skip a first sentence; `asr.py` already uses `vad_filter=True` and `condition_on_previous_text=False`, and words with no speech under them are dropped later.
   - It mishears names and rare words (سيزف, ألم مارلات, خلق الامتناع, الفقه دقيق). Match on the misheard spelling; tell the user which words to double-check by ear, without claiming they mispronounced them.
3. **Map key words:** in `timing_all.py` write `MAP[N]`: the part script's `T` keys in speaking order, each with the word to find (`"word"` = contains, `"=word"` = exact, `"word#2"` = second match from here, `(other_key, ±s)` = offset for things with no word of their own, like a year shown after a name). Arabic is normalized (tashkeel, أإآ→ا, ى→ي, ة→ه). Prefer distinctive words; short ones (لا، من، في) need `=` and a good preceding key. Add `PAUSES[N]` only where asked.
4. **Edit the voice:** `python3 timing_all.py N …` →
   - `voice_edit.build`: cleans (`basira_sound.clean`, light), finds speech with the **Silero VAD** (it rejects breaths; plain silence detection kept inhales glued to words), keeps only spans with transcribed words, splits a span to place a pause exactly before its word, halves the gaps (0.08–0.32 s), short fades.
   - `breath_check.mute_breaths`: mutes breath-like runs inside phrases (unvoiced, noisy, quieter than ~−33 dB, not a hissing س/ش), then mutes anything noisy left **between** two words.
   - writes `proj/vo_N.wav` (voice placed at 0.5 s) and `proj/times_N.json` (with `_end` = end of voice). Prints keys out of order, dropped words and muted breaths.
5. **Check:** `python3 breath_check.py N …` lists what still looks like a breath. Only fricatives inside words should remain (أمس, زيوس, شربا, الصخرة); look up the word at that time if unsure.
6. **Sound design:** in `sound_all.py`, one `partN(m, P, T)` per part with its own moments; the generic layer adds a tear on every torn scene change and pop/tick for every label word automatically. `python3 sound_all.py N …` → `proj/mix_N.wav` (≈ −16 LUFS).
7. **Re-render every part** (timings changed), encode with the mix (`E.encode("proj/mix_N.wav", "…_vK.mp4", DUR, frames_dir=…)`), join with `ffmpeg -f concat -c copy`, check loudness (`ffmpeg -i full.mp4 -af ebur128=peak=true -f null -` → about −16 LUFS, peak < −1 dBFS). A 16-part video re-renders in ~35 min: run it in the background and check key frames of finished parts meanwhile.
8. Send the full video, say what changed, list the words to check by ear and the pauses kept, and invite "tell me the minute:second if you still hear something".

## Sound map (used and liked)

| Moment | Sound |
|---|---|
| every torn-paper scene change / screen split / a half falling | `tear()` |
| a label appears / each new word | `pop()` / `tick()` (automatic) |
| walking | `shuffle()` every ~0.34 s; heavy pushes: `thud()` + `shuffle()` every ~0.8 s |
| a god/threat appears early | `rumble(db=-27)` — distant; save the big one |
| lightning above the head | `crack()` at the strike + `big_thunder()` with `duck=True` |
| a rock rolling away | low rolling noise + `thud()`s on bounces |
| chains, banquet | `clink()` |
| something snatched / a flight | `whoosh()` (long for a plane) |
| underworld / lake | `water(dur)` |
| flicker into the modern room / a phone | `zap()` on each switch, `hum()` while there, `ding()` on the first |
| camera, scanner | low `hum()` |
| typewriter, chairs ticking in, day-squares | `tick()` |
| a number torn (٢٠% → ٥%), a good revelation | `tear()` + soft `ding()` |
| warm light, forgiveness, «نعم» | `warm(dur, f0)` held tone, low level |
| night desert | `wind(dur)` bed, louder gusts when sand is blown |
| ending / cliffhanger | `drone(dur)`; on the logo `ding()` then silence |

All effects are synthesized; say so honestly. If the user wants real samples (e.g. Pixabay Sound Effects), convert with `ffmpeg -i in.mp3 -ac 1 -ar 48000 -c:a pcm_f32le x.wav`, scale with `S.norm(x, -24)`, and `m.add(t, x)`.

## Delivery feedback (brief, when useful)

Phrases longer than ~6 s are hard to cut to; leave a short pause before key words; read like a حكواتي to one person, lower the voice when addressing the viewer, smile on hopeful lines; one file per part named by number; a quiet room, phone a hand-span from the mouth.

## Files

- `scripts/basira_sound.py`: cleanup presets, silence-detection speech segments, synthesized effects, `Timeline` (older single-part helper).
- `scripts/asr.py`, `scripts/voice_edit.py`, `scripts/breath_check.py`: transcription, voice editing, breath detection.
- `scripts/timing_all.py`, `scripts/sound_all.py`: templates with a worked example (Sisyphus part 12); fill `MAP`, `PAUSES` and one `partN` per part.
- The full Sisyphus video (16 parts) with its real maps and sound functions is in the user's repo `animation-playground`, folder `sisyphus/`.
