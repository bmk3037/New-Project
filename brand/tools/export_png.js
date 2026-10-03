// SVG → PNG 내보내기 (Playwright 필요: npm i -D playwright)
//   node brand/tools/export_png.js
// SVG의 글자는 모두 아웃라인이라 글꼴 없이 그대로 렌더링된다.
const path = require('path');
const { chromium } = require('playwright');

const BRAND = path.join(__dirname, '..');
const JOBS = [
  { src: 'logo/symbol-square.svg', out: 'logo/symbol-512.png', w: 512, h: 512 },
  { src: 'og-image.svg', out: 'og-image.png', w: 1200, h: 630 },
];

(async () => {
  const browser = await chromium.launch();
  for (const { src, out, w, h } of JOBS) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    // viewBox만 있는 SVG는 창 크기에 꽉 차게 그려진다
    await page.goto('file://' + path.join(BRAND, src));
    await page.screenshot({ path: path.join(BRAND, out), omitBackground: true });
    await page.close();
    console.log(out);
  }
  await browser.close();
})();
