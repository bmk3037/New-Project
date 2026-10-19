// 편 폴더(예: ep07)의 timeline.json + sheets.html + assets/를 합쳐 1080x1920 mp4를 만든다.
//   node render.js ep07            → out/ep07.mp4
//   node render.js ep07 --fps 15   → 빠른 미리보기
//   node render.js ep07 --still 20 → 20초 지점 한 장만 PNG로
// assets/narration.(mp3|wav)가 있으면 장면 길이를 음성 길이에 맞춰 늘리거나 줄인다.
// 실사 자리(clip A, B…)에는 assets/A.mp4(Flow 영상) 또는 assets/A.png·jpg(Flow 사진)를 넣는다.
// 사진은 천천히 확대되는 움직임을 넣는다. 둘 다 없으면 회색 임시 화면으로 채운다.
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ep = process.argv[2];
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const dir = path.resolve(__dirname, ep);
const tl = JSON.parse(fs.readFileSync(path.join(dir, 'timeline.json'), 'utf8'));
const fps = Number(arg('--fps', tl.fps || 30));
const assets = path.join(dir, 'assets');
const outDir = path.resolve(__dirname, 'out');
fs.mkdirSync(outDir, { recursive: true });

const probe = (f) => Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString());
const audio = ['narration.mp3', 'narration.wav', 'narration.m4a'].map((f) => path.join(assets, f)).find(fs.existsSync);
const planned = tl.beats.reduce((s, b) => s + b.dur, 0);
const scale = audio ? (probe(audio) + 0.3) / planned : 1;
const clips = [...new Set(tl.beats.flatMap((b) => b.scenes).filter((s) => s.type === 'video').map((s) => s.clip))];
const clipFile = (c) => ['mp4', 'png', 'jpg', 'jpeg', 'webp'].map((e) => path.join(assets, `${c}.${e}`)).find(fs.existsSync);
const isImage = (f) => !f.endsWith('.mp4');
const missing = clips.filter((c) => !clipFile(c));

function run(cmd, args) {
  return new Promise((res, rej) => {
    const p = spawn(cmd, args, { stdio: ['ignore', 'inherit', 'inherit'] });
    p.on('close', (c) => (c ? rej(new Error(`${cmd} exited ${c}`)) : res()));
  });
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(dir, 'sheets.html'));
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(([t, s, m]) => window.setup(t, s, m), [tl, scale, missing]);
  const sched = await page.evaluate(() => window.SCHED);

  const still = arg('--still');
  if (still) {
    await page.evaluate((t) => window.renderAt(t), Number(still));
    const f = path.join(outDir, `${ep}-${still}s.png`);
    await page.screenshot({ path: f });
    console.log(f);
    await browser.close();
    return;
  }

  // 1) 배경: 실사 영상 구간만 Flow 영상을 깔고 나머지는 검정
  const bg = path.join(outDir, `${ep}-bg.mp4`);
  const vids = sched.filter((s) => s.type === 'video' && !missing.includes(s.clip));
  const bgArgs = ['-y', '-v', 'error', '-f', 'lavfi', '-i', `color=black:s=1080x1920:r=${fps}:d=${total}`];
  let fc = '', last = '0:v';
  vids.forEach((s, i) => {
    const f = clipFile(s.clip), dur = (s.end - s.start).toFixed(3), frames = Math.ceil((s.end - s.start) * fps);
    if (isImage(f)) {
      // 사진: 2배 크기로 맞춘 뒤 장면 길이 동안 8% 확대
      bgArgs.push('-loop', '1', '-framerate', '1', '-t', '1', '-i', f);
      fc += `[${i + 1}:v]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,` +
        `zoompan=z='1+0.08*on/${frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${frames}:s=1080x1920:fps=${fps},` +
        `trim=0:${dur},setpts=PTS-STARTPTS+${s.start.toFixed(3)}/TB[c${i}];`;
    } else {
      bgArgs.push('-stream_loop', '-1', '-i', f);
      fc += `[${i + 1}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=${fps},trim=0:${dur},setpts=PTS-STARTPTS+${s.start.toFixed(3)}/TB[c${i}];`;
    }
    fc += `[${last}][c${i}]overlay=eof_action=pass:enable='between(t,${s.start.toFixed(3)},${s.end.toFixed(3)})'[b${i}];`;
    last = `b${i}`;
  });
  if (vids.length) bgArgs.push('-filter_complex', fc.replace(/;$/, ''), '-map', `[${last}]`);
  bgArgs.push('-t', String(total), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', bg);
  await run('ffmpeg', bgArgs);

  // 2) 도면·자막 프레임을 투명 PNG로 뽑아 배경 위에 얹고 음성을 붙인다
  const out = path.join(outDir, `${ep}.mp4`);
  const audioIn = audio ? ['-i', audio] : ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo'];
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-i', bg, ...audioIn,
    '-filter_complex', '[1:v][0:v]overlay=format=auto,format=yuv420p[v]', '-map', '[v]', '-map', '2:a',
    '-t', String(total), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out],
  { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', (c) => (c ? rej(new Error('ffmpeg ' + c)) : res())));
  const n = Math.ceil(total * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate((t) => window.renderAt(t), i / fps);
    const buf = await page.screenshot({ omitBackground: true, type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % (fps * 5) === 0) process.stdout.write(`\r${(i / fps).toFixed(0)}s / ${total.toFixed(0)}s`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
  fs.unlinkSync(bg);
  console.log(`\n${out} (${total.toFixed(1)}초, 음성 ${audio ? '있음' : '없음'}, 빠진 실사 컷: ${missing.join(', ') || '없음'})`);
})();
