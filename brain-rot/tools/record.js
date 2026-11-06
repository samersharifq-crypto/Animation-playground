// Renders the film frame by frame, builds the soundtrack and muxes the MP4.
// usage: node brain-rot/tools/record.js   (needs Playwright, ffmpeg, python3 + numpy)
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..'), fps = 30;
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 600, height: 1100 } });
  await pg.goto('file://' + path.join(dir, 'index.html') + '?capture', { waitUntil: 'commit' });
  await pg.waitForFunction(() => window.__ready, null, { timeout: 60000 });
  const total = await pg.evaluate(() => window.__TOTAL);
  const silent = path.join(dir, '.video-silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(total * fps);
  for (let i = 0; i < n; i++) {
    const url = await pg.evaluate(t => window.__frame(t), i / fps);
    if (!ff.stdin.write(Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
  const wav = path.join(dir, '.sound.wav');
  execFileSync('python3', [path.join(__dirname, 'sound.py'), wav], { stdio: 'inherit' });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', silent, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', path.join(dir, 'brain-rot.mp4')]);
  fs.unlinkSync(silent); fs.unlinkSync(wav);
  console.log('done');
})();
