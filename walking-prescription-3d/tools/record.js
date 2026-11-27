// Renders the 3D scene frame by frame to walking-prescription-3d.mp4 (1080x1920, 24 fps, silent).
// usage: node walking-prescription-3d/tools/record.js   (needs Playwright + ffmpeg)
// Set THREE_MODULE=/path/to/three.module.js to serve three.js locally when the CDN is unreachable.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..'), fps = 24;
const types = { '.html': 'text/html', '.webp': 'image/webp', '.js': 'text/javascript' };

(async () => {
  // textures can't be uploaded to WebGL from file:// pages, so serve the folder over http
  const server = http.createServer((q, s) => {
    const f = path.join(dir, decodeURIComponent(q.url.split('?')[0]));
    if (!f.startsWith(dir) || !fs.existsSync(f)) { s.writeHead(404); return s.end(); }
    s.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(s);
  }).listen(0);
  const port = server.address().port;
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  if (process.env.THREE_MODULE) await pg.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ path: process.env.THREE_MODULE, contentType: 'text/javascript' }));
  await pg.goto(`http://localhost:${port}/index.html?capture`);
  await pg.waitForFunction(() => window.__ready, null, { timeout: 120000 });
  const total = await pg.evaluate(() => window.__TOTAL);
  const out = path.join(dir, 'walking-prescription-3d.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(total * fps);
  for (let i = 0; i < n; i++) {
    await pg.evaluate(t => window.__seek(t), i / fps);
    const buf = await pg.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 48 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await b.close(); server.close();
  console.log('done ->', out);
})();
