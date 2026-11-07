// Renders the film frame by frame (12 fps stop-motion, written out at 24 fps), builds the
// soundtrack from the film's cues and muxes the MP4.
// It also writes narration-timing.srt, mixes in narration.mp3 as a voice-over when that file exists,
// and frames the film on kraft paper as 16:9 and square versions.
// usage: node torn-paper-lucid/tools/record.js   (needs Playwright, ffmpeg, python3 + numpy)
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
  const C = await pg.evaluate(() => window.__CUES);
  fs.writeFileSync(cues, JSON.stringify(C));
  const ts = t => { const ms = Math.round(t * 1000), h = ms / 3600000 | 0, m = ms / 60000 % 60 | 0, s = ms / 1000 % 60 | 0;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms % 1000).padStart(3, '0')}`; };
  fs.writeFileSync(path.join(dir, 'narration-timing.srt'),
    C.lines.map((l, i) => `${i + 1}\n${ts(l.start)} --> ${ts(l.end)}\n${l.text}\n`).join('\n'));
  const silent = path.join(dir, '.video-silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-r', '24', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
  // warm-up: the first heavy filtered frame can come back blank
  for (const w of [0, 1, 2]) { await pg.evaluate(t => window.__seek(t), w); await pg.screenshot({ type: 'jpeg' }); }
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
  // the film's audio: soundtrack, plus the voice-over on top when narration.mp3 is there
  const voice = path.join(dir, 'narration.mp3'), audio = path.join(dir, '.audio.wav');
  if (fs.existsSync(voice)) execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', wav, '-i', voice, '-filter_complex',
    '[0]volume=0.75[m];[1]volume=1.3[v];[m][v]amix=inputs=2:duration=first:normalize=0', audio]);
  else fs.copyFileSync(wav, audio);
  const main = path.join(dir, 'torn-paper-lucid.mp4');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', silent, '-i', audio, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
    '-shortest', '-movflags', '+faststart', main]);
  // 16:9 and square: the vertical film mounted on kraft paper with a white paper border
  for (const [name, W, H] of [['16x9', 1920, 1080], ['1x1', 1080, 1080]]) {
    // a still sheet of grainy kraft paper (a still background keeps the files small)
    const bg = path.join(dir, `.bg-${name}.png`);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'lavfi', '-i', `color=c=0xa9845a:s=${W}x${H}`, '-vf', 'noise=alls=14,gblur=sigma=0.6', '-frames:v', '1', bg]);
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', main, '-loop', '1', '-framerate', '24', '-i', bg, '-filter_complex',
      `[0]scale=-2:${H - 64},pad=iw+20:ih+20:10:10:color=0xfbf8f1,rotate=-0.012:c=none:ow=rotw(-0.012):oh=roth(-0.012)[v];[1][v]overlay=(W-w)/2:(H-h)/2:shortest=1,format=yuv420p`,
      '-map', '0:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart',
      path.join(dir, `torn-paper-lucid-${name}.mp4`)]);
    fs.unlinkSync(bg);
  }
  fs.unlinkSync(audio);
  for (const f of [silent, wav, cues]) fs.unlinkSync(f);
  console.log('done');
})();
