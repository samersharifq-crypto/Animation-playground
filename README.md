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

## brain-rot/ — «تعفّن الدماغ»

A 64-second vertical (9:16) motion graphic in Arabic about *brain rot*. Each scene borrows the look of one reference image: a hypnotic spiral, an RGB contour tunnel around a head, a pink halftone wall of TVs, a giant glowing phone, a man in an armchair lit by an old set, and a warm dawn at the end. It's all drawn live on canvas, with no images.

1. **The spiral**: a man in a grey suit walks into a turning spiral. Title.
2. **What is it?**: a head in silhouette inside RGB rings that fray and glitch. The definition, adapted from Oxford.
3. **Word of the year**: TVs pop up on a pink halftone wall. Oxford's 2024 Word of the Year, and its 230% rise in use.
4. **Infinite scroll**: the feed speeds up on a giant phone. Variable rewards, and the 47-second attention span from Gloria Mark's research.
5. **Not a new word**: Thoreau's 1854 line from *Walden*, then the set switches off down to a dot.
6. **The way back**: the dot becomes a sunrise. Four habits to get your focus back.

Open `brain-rot/index.html` to play it (space = play/pause, M = sound, click the bar to seek). `brain-rot/brain-rot.mp4` is the rendered 1080×1920 30fps video with its synthesized soundtrack. To render it again, run `node brain-rot/tools/record.js` (needs Playwright, ffmpeg, python3 + numpy).

## steve-jobs/ — «من المرآب»

A 78-second vertical (9:16) motion graphic in Arabic about Steve Jobs and how Apple started. It borrows the look of a retro "museum wall" short: lamp-lit panelled walls, framed photographs that swing in and settle, word-by-word type, yellow torn-paper name tags, a red stamp over a smoky black-and-white collage, a green cutting mat, a blue spotlight and a white gallery wall. It uses real photographs of Jobs, Wozniak, the Los Altos garage and the early machines, all from Wikimedia Commons (credits in `steve-jobs/CREDITS.md`).

1. **The hook**: the garage through the fog. *What if a small garage made one of the world's most valuable companies?*
2. **1955**: born in San Francisco, adopted by the Jobs family.
3. **School**: Homestead High yearbook portraits from 1969 and 1972, Reed College for one semester, and the calligraphy classes.
4. **The friend**: Steve Wozniak, the engineer, and Jobs, who saw how to get it to people.
5. **1976**: Apple is founded on 1 April by Jobs, Wozniak and Ronald Wayne, with about $1,300 from a VW van and a calculator.
6. **Apple I**: the first order for 50 units from the Byte Shop, at $666.66 each.
7. **Apple II and the IPO**: 1977, then 1980, worth over $200 million at 25.
8. **1984 → 1985**: the Macintosh, then he is forced out of his own company.
9. **NeXT, Pixar and the return** in 1997.
10. **The products that followed**: Macworld 2005, iPhone 2007, MacBook Air 2008, iPad 2010.
11. **Stanford 2005**: *Stay hungry, stay foolish.*
12. **End card**: 1955–2011. *From a small garage, he changed the world.*

Open `steve-jobs/index.html` to play it (space = play/pause, M = sound, click the bar to seek). `steve-jobs/steve-jobs.mp4` is the rendered 1080×1920 30fps video with its generated soundtrack (vinyl crackle, a slow piano progression, and whooshes and thuds on the cuts), which is also saved as `steve-jobs/soundtrack.m4a` for the player. To render it again, run `node steve-jobs/tools/record.js` (needs Playwright, ffmpeg, python3 + numpy).

## stranger-at-the-window/ — *The Stranger at the Window*

A 74-second vertical (9:16) cut-paper collage thriller, made as a stop-motion movie. The whole picture moves on twelves, with gate weave, exposure flicker and paper grain. It borrows from the reference collages:
- a night city built from torn newsprint, crosswords, stock pages, brick and blue-and-white tiles, with warm lit windows
- torn navy skies with paper stars and a mustard moon
- spotlight street lamps and cobbles of torn scraps
- a torn hole in a face, a giant hand from above, and halftone cut-outs with white scissor borders

**The hero** is a paper puppet built from a real photo (`img/hero.png`, supplied by the author). The head, shoulders and chest are the photo. The sleeves and cloak are cut from the photo's own black bisht cloth (`img/bisht.jpg`), and the trim from its gold zari (`img/gold.jpg`). He wears a white paper thobe and leather shoes, and every joint is a brass split pin.

**The stranger** has a drawn, noir-lit face: a fedora brim shadow over the eyes, stubble, a moustache and halftone print.

1. **Intro**: a film-leader countdown, then a torn *HAVE YOU SEEN THIS MAN?* poster on a brick wall under a lamp, whose eyes follow you. The title strips are slapped on, and the cast appears: The Reader, The Stranger, The Constable.
2. **Café Rosa**: he sips coffee and reads *How to Spot a Spy*. The stranger's face rises at the glass, hangs upside down from the top, then slides in behind a newspaper with eye-holes. Freeze frame: SUSPECT / WITNESS.
3. **The evidence board**: polaroids, red string, a typed index card and a WANTED (for staring) stamp. It tears open in a hole to reveal the street.
4. **Following the clues**: magnifier in hand, he follows glowing footprints and croissant crumbs to the stranger under a street lamp, who dives into a taxi (SLAM!). A police car screeches up: *HOP IN!*
5. **The car chase**: sirens through the collage city, with the stranger leaning out of the taxi and the hero leaning out of the police car, coffee in hand.
   - The police car hits a thrown banana peel and spins.
   - Both cars launch off a newspaper ramp over the oncoming No. 7 bus (*sip.*, coffee spilled: 0).
   - The taxi skids to a stop at a cardboard staircase.
6. **The stairs**: up to a dead end.
7. **Caught**: a giant police hand plucks him off a brick rooftop under the moon. *GOTCHA*.
8. **Mugshot**: CAUGHT. The placard flips: he was only trying to return the wallet. *oh.* CASE CLOSED (awkwardly).
9. **The end**: back in the café with two newspapers at the window, *…or is it?*, and closing credits.

Open `stranger-at-the-window/index.html` to play it (space = play/pause, M = sound, click the bar to seek). `stranger-at-the-window/stranger-at-the-window.mp4` is the rendered 1080×1920 video.

The generated soundtrack is also saved as `soundtrack.m4a` for the player. It has:
- a countdown beep, spy-jazz bass and café piano
- a dread drone and heartbeat, and a ticking clock
- a comic xylophone chase with a siren, tyre screeches, a horn and passing cars
- a sad trombone
- rips, stamps, boings and handcuffs on cue

To render it again, run `node stranger-at-the-window/tools/record.js` (needs Playwright, ffmpeg, python3 + numpy).
