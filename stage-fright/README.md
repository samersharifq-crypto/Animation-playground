# stage-fright/ — «رهبة»

A 28-second vertical (1080×1920) 3D paper short with no narration. It is built from the 16 paper cut-out images in `src/`: torn-paper stop-motion at 12 fps, depth layers (parallax), camera moves, and a 3D door swing.

1. **City** (0–3 s): he walks home. The rooftops and the sky move at different speeds.
2. **Hallway** (3–7.5 s): he walks deeper into the corridor and gets smaller as the camera moves forward.
3. **The door** (7.5–12 s): he waits on a chair with his knee bouncing. The paper door swings open in 3D and the camera rushes into the light.
4. **Lecture hall** (12–17 s): eyes pop out of the seats one by one, each at a different depth, while his heartbeat speeds up.
5. **Close-up** (17–19.6 s): the eyes circle his head in 3D, ending in a glitch.
6. **Room at night** (19.6–25 s): a phone call, then he sits on the floor. The focus shifts from him to the pill bottle.
7. **Toward the light** (25–28 s): a close-up of his face in the lamp light, then a tear back to the first frame so the short loops.

To render it again, run:
```
pip install scipy
python3 tools/cutouts.py
for r in "0 84" "84 168" "168 252" "252 336"; do python3 tools/film.py $r & done; wait
python3 tools/sound.py
python3 -c "import sys; sys.path.insert(0,'tools'); import engine as E; E.encode('build/mix.wav','stage-fright.mp4',28.0)"
```
