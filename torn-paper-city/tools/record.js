// Renders the film frame by frame (12 fps stop-motion, written out at 24 fps), builds the
// soundtrack from the film's cues and muxes the MP4.
// usage: node torn-paper-city/tools/record.js   (needs Playwright, ffmpeg, python3 + numpy)
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..'), fps = 12;
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto('file://' + path.join(dir, 'index.html') + '?capture');
  await pg.waitForFunction(() => window.__ready, null, { timeout: 60000 });
  const total = await pg.evaluate(() => window.__TOTAL);
  const cues = path.join(dir, '.cues.json');
  fs.writeFileSync(cues, JSON.stringify(await pg.evaluate(() => window.__CUES)));
  const silent = path.join(dir, '.video-silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-r', '24', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.ceil(total * fps);
  for (let i = 0; i < n; i++) {
    await pg.evaluate(t => window.__seek(t), i / fps);
    const buf = await pg.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
  const wav = path.join(dir, '.sound.wav');
  execFileSync('python3', [path.join(__dirname, 'sound.py'), cues, wav], { stdio: 'inherit' });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '160k', path.join(dir, 'soundtrack.m4a')]);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', silent, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
    '-shortest', '-movflags', '+faststart', path.join(dir, 'torn-paper-city.mp4')]);
  for (const f of [silent, wav, cues]) fs.unlinkSync(f);
  console.log('done');
})();
