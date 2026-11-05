// Renders rainy-day/index.html frame-by-frame into an MP4 (needs playwright + ffmpeg).
// usage: node rainy-day/tools/record.js [out.mp4] [fps]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const out = process.argv[2] || path.join(__dirname, '..', 'rainy-day.mp4');
  const fps = +(process.argv[3] || 30);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await pg.goto('file://' + path.join(__dirname, '..', 'index.html') + '?capture');
  await pg.waitForTimeout(500);
  const total = await pg.evaluate(() => window.__TOTAL);
  const n = Math.round(total * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-f', 'lavfi', '-i', `anoisesrc=color=brown:amplitude=0.5:duration=${total}`,
    '-f', 'lavfi', '-i', `anoisesrc=color=pink:amplitude=0.08:duration=${total}`,
    '-filter_complex', `[1][2]amix=inputs=2:normalize=0,highpass=f=120,lowpass=f=5000,afade=in:d=2,afade=out:st=${total - 2.5}:d=2.5,volume=1.6[a]`,
    '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) {
    const url = await pg.evaluate(([t, dt]) => window.__capture(t, dt), [i / fps, 1 / fps]);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
  console.log('wrote', out);
})();
