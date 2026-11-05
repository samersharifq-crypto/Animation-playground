// Renders beyond-the-familiar/index.html frame by frame to a 1080x1920 MP4 (needs Playwright + ffmpeg).
// usage: node beyond-the-familiar/tools/record.js [out.mp4] [fps]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const out = process.argv[2] || path.join(__dirname, '..', 'beyond-the-familiar.mp4');
  const fps = +(process.argv[3] || 30);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 600, height: 1100 } });
  await pg.goto('file://' + path.join(__dirname, '..', 'index.html') + '?capture', { waitUntil: 'commit' });
  await pg.waitForFunction(() => window.__ready, null, { timeout: 30000 });
  const total = await pg.evaluate(() => window.__TOTAL);
  const n = Math.round(total * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '30', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) {
    const url = await pg.evaluate(t => window.__frame(t), i / fps);
    if (!ff.stdin.write(Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
  console.log('wrote', out);
})();
