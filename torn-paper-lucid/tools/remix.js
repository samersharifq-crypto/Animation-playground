// Rebuilds only the sound (soundtrack + optional narration.mp3) and swaps it into the three
// rendered videos without re-rendering the picture. Use it after editing tools/sound.py.
// usage: node torn-paper-lucid/tools/remix.js   (needs Playwright, ffmpeg, python3 + numpy)
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..');
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto('file://' + path.join(dir, 'index.html') + '?capture');
  await pg.waitForFunction(() => window.__ready, null, { timeout: 60000 });
  const cues = path.join(dir, '.cues.json'), wav = path.join(dir, '.sound.wav'), audio = path.join(dir, '.audio.wav');
  fs.writeFileSync(cues, JSON.stringify(await pg.evaluate(() => window.__CUES)));
  await b.close();
  execFileSync('python3', [path.join(__dirname, 'sound.py'), cues, wav], { stdio: 'inherit' });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '160k', path.join(dir, 'soundtrack.m4a')]);
  const voice = path.join(dir, 'narration.mp3');
  if (fs.existsSync(voice)) execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', wav, '-i', voice, '-filter_complex',
    '[0]volume=0.75[m];[1]volume=1.3[v];[m][v]amix=inputs=2:duration=first:normalize=0', audio]);
  else fs.copyFileSync(wav, audio);
  for (const name of ['torn-paper-lucid.mp4', 'torn-paper-lucid-16x9.mp4', 'torn-paper-lucid-1x1.mp4']) {
    const f = path.join(dir, name), tmp = path.join(dir, '.remix-' + name);
    if (!fs.existsSync(f)) continue;
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', f, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
      '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', tmp]);
    fs.renameSync(tmp, f);
    console.log('new sound in', name);
  }
  for (const f of [cues, wav, audio]) fs.unlinkSync(f);
})();
