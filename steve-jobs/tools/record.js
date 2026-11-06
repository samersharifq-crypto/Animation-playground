// Renders the film frame by frame, builds the soundtrack from the film's cues and muxes the MP4.
// usage: node steve-jobs/tools/record.js   (needs Playwright, ffmpeg, python3 + numpy)
// The page is served over a local HTTP server so the canvas with photos can be read back.
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..'), fps = 30;
const TYPES = { '.html': 'text/html', '.jpg': 'image/jpeg', '.m4a': 'audio/mp4' };
const srv = http.createServer((q, r) => {
  const f = path.join(dir, decodeURIComponent(q.url.split('?')[0]));
  if (!f.startsWith(dir)) { r.writeHead(403); r.end(); return; }
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); r.end(d); });
});
srv.listen(0, '127.0.0.1', async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 600, height: 1100 } });
  await pg.goto(`http://127.0.0.1:${srv.address().port}/index.html?capture`, { waitUntil: 'commit' });
  await pg.waitForFunction(() => window.__ready, null, { timeout: 60000 });
  const total = await pg.evaluate(() => window.__TOTAL);
  const cues = path.join(dir, '.cues.json');
  fs.writeFileSync(cues, JSON.stringify(await pg.evaluate(() => window.__CUES)));
  const silent = path.join(dir, '.video-silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '27', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(total * fps);
  for (let i = 0; i < n; i++) {
    const url = await pg.evaluate(t => window.__frame(t), i / fps);
    if (!ff.stdin.write(Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); srv.close();
  const wav = path.join(dir, '.sound.wav');
  execFileSync('python3', [path.join(__dirname, 'sound.py'), cues, wav], { stdio: 'inherit' });
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '160k', path.join(dir, 'soundtrack.m4a')]);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', silent, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', path.join(dir, 'steve-jobs.mp4')]);
  for (const f of [silent, wav, cues]) fs.unlinkSync(f);
  console.log('done');
});
