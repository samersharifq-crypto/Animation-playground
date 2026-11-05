# Animation Playground

## rainy-day/

A ~66-second looping motion graphic, drawn live on an HTML canvas with no images or libraries.
Open `rainy-day/index.html` in a browser.

1. **Coffee by the window**: rain streaks on the glass, city bokeh, steam rising from a mug
2. **The old street**: walking under a red umbrella, coffee in hand, past wet reflections and lamplight
3. **Nostalgia**: everything turns sepia and old polaroids drift in
4. **Strangers**: people run past to get out of the rain while you stand still and sip
5. **Going home**: you close the umbrella and a warm door opens
6. **In bed**: rain on the window, a blanket that breathes, the lamp dims. *goodnight.*

Controls: **space** plays or pauses, **m** turns the sound on or off (rain noise plus soft notes, made in the browser and muffled indoors), and clicking the bar jumps to a point.

**Video:** `rainy-day/rainy-day.mp4` is a 66-second 1080p 30fps video with rain sound. To render it again, run
`node rainy-day/tools/record.js` (needs Playwright and ffmpeg).

## beyond-the-familiar/ — «ما وراء المألوف»

A 65-second vertical (9:16) motion graphic based on the Arabic reflection *Beyond the Familiar*. It's drawn live on canvas in a flat editorial illustration style: solid shapes, a plum/teal/terracotta/cream palette, hard-edged rim light, cinematic backlight, and a print pass that snaps every pixel to the palette and stipples the gradients. The routine scenes are cool monochrome, and colour returns as his attention opens.
Open `beyond-the-familiar/index.html` to play it. Play/pause, replay and a scrubbable timeline sit below the artwork (space bar = play/pause).
`beyond-the-familiar/beyond-the-familiar.mp4` is a rendered 1080×1920 video. To render it again, run `node beyond-the-familiar/tools/record.js`.

Scenes: the familiar morning → walking without seeing (Najdi alley) → a small interruption (the door) → what was always there (the courtyard) → a different way of looking (book & window) → the same world, seen again.
Transitions: the cup rim becomes a patch of light, a beam of light widens across the frame, the opening door wipes into the courtyard, a floating leaf becomes a pressed leaf, and the courtyard window cuts to the room window.

## beyond-the-familiar-city/ — «ما وراء المألوف» (city)

A 60-second vertical (9:16) animated short, plus a 5-second title. A man walks through an unnamed, New York–inspired city without noticing it, until small discoveries change how he sees it.
It's drawn live on canvas: an elongated, backlit figure in a dark coat with a hard teal rim light, geometric façades, and a print pass that limits every frame to the palette (muted teal, charcoal, dusty rose, terracotta, warm ivory, a little sunlight) and stipples the gradients.

- `index.html`: the playable film. Play/pause, replay, sound (M) and a timeline sit below the artwork.
- `beyond-the-familiar-city.mp4`: the rendered 1080×1920 video with sound design.
- `beyond-the-familiar-city-sound.m4a`: the generated soundtrack. It has city ambience that hushes in the courtyard, footsteps synced to the walk cycle, cars, a subway train, leaves, paper and sparse piano.
- `narration-timing.srt`: the exact Arabic narration lines with their on-screen timings. Put a recorded voiceover at `narration.mp3` next to `index.html` and the player plays it in sync.
- `node beyond-the-familiar-city/tools/record.js` renders the MP4 again, and the soundtrack with it.
