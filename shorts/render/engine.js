// 장면 타임라인 엔진. render.js가 window.renderAt(t)를 프레임마다 부른다.
// 애니메이션 속성의 숫자는 장면 길이에 대한 비율(0~1)이다. 음성 길이에 맞춰 장면이 늘어나도 그대로 맞는다.
//   data-draw="a b"  선이 a~b 동안 그려진다
//   data-fade="a b"  a~b 동안 나타난다
//   data-out="a b"   a~b 동안 사라진다
//   data-grow="a b"  a~b 동안 아래에서 위로 자란다 (막대 게이지)
//   data-cls="a 이름" a 이후 class를 붙인다
(function () {
  const clamp = (x) => Math.max(0, Math.min(1, x));
  const ease = (x) => x * x * (3 - 2 * x);
  const prog = (attr, p) => { const [a, b] = attr.split(/\s+/).map(Number); return ease(clamp((p - a) / Math.max(b - a, 1e-6))); };

  function chunk(text, max) {
    const out = [];
    for (const phrase of text.split(/(?<=[.,?!])\s+/)) {
      let cur = '';
      for (const w of phrase.split(/\s+/)) {
        if (cur && (cur + ' ' + w).length > max) { out.push(cur); cur = w; } else cur = cur ? cur + ' ' + w : w;
      }
      if (cur) out.push(cur);
    }
    return out.map((c) => c.replace(/[.,]$/, ''));
  }

  window.setup = function (tl, scale, missing) {
    const sched = [], caps = [];
    let t = 0;
    for (const beat of tl.beats) {
      const dur = beat.dur * scale;
      const wsum = beat.scenes.reduce((s, x) => s + (x.w || 1), 0);
      let st = t;
      for (const sc of beat.scenes) {
        const d = dur * (sc.w || 1) / wsum;
        sched.push({ ...sc, start: st, end: st + d });
        st += d;
      }
      const chunks = chunk(beat.text, tl.capMax || 13);
      const total = chunks.reduce((s, c) => s + c.replace(/\s/g, '').length, 0);
      let ct = t;
      for (const c of chunks) {
        const d = dur * c.replace(/\s/g, '').length / total;
        caps.push({ text: c, em: beat.em || [], start: ct, end: ct + d });
        ct += d;
      }
      t += dur;
    }
    window.TOTAL = t;
    window.SCHED = sched; window.CAPS = caps; window.MISSING = missing || [];
    document.querySelector('#tb .t').textContent = tl.title;
    document.querySelector('#tb .r').textContent = tl.dwg;
    // 선 길이를 미리 재 둔다
    document.querySelectorAll('[data-draw]').forEach((el) => {
      const L = el.getTotalLength ? el.getTotalLength() : 1000;
      el.style.strokeDasharray = L; el.dataset.len = L;
    });
    return t;
  };

  window.renderAt = function (t) {
    const sc = SCHED.find((s) => t >= s.start && t < s.end) || SCHED[SCHED.length - 1];
    const p = clamp((t - sc.start) / (sc.end - sc.start));
    const video = sc.type === 'video';
    document.body.classList.toggle('video', video);
    document.querySelectorAll('.scene').forEach((el) => el.classList.toggle('on', !video && el.id === sc.id));
    const tag = document.getElementById('tag');
    tag.textContent = sc.label || ''; tag.classList.toggle('on', video && !!sc.label);
    const ph = document.getElementById('ph');
    ph.classList.toggle('on', video && MISSING.includes(sc.clip));
    ph.innerHTML = `FLOW ${sc.clip || ''}<br>(실사 사진·영상 자리)`;
    document.getElementById('sheet').textContent = sc.sheet || '';
    if (!video) {
      const root = document.getElementById(sc.id);
      root.querySelectorAll('[data-draw]').forEach((el) => { el.style.strokeDashoffset = el.dataset.len * (1 - prog(el.dataset.draw, p)); });
      root.querySelectorAll('[data-fade]').forEach((el) => { el.style.opacity = prog(el.dataset.fade, p); });
      root.querySelectorAll('[data-out]').forEach((el) => { el.style.opacity = 1 - prog(el.dataset.out, p); });
      root.querySelectorAll('[data-grow]').forEach((el) => {
        el.style.transformBox = 'fill-box'; el.style.transformOrigin = '50% 100%';
        el.style.transform = `scaleY(${prog(el.dataset.grow, p)})`;
      });
      root.querySelectorAll('[data-cls]').forEach((el) => {
        const [a, cls] = el.dataset.cls.split(/\s+/); el.classList.toggle(cls, p >= Number(a));
      });
    }
    const cap = CAPS.find((c) => t >= c.start && t < c.end);
    let html = cap ? cap.text : '';
    for (const w of (cap ? cap.em : [])) html = html.split(w).join(`<em>${w}</em>`);
    document.getElementById('cap').innerHTML = html;
  };
})();
