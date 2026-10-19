const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const f of ['f1','f2','f3']) {
    await p.goto('file://' + process.cwd() + '/' + f + '.html');
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(300);
    await p.screenshot({ path: f + '.png' });
  }
  await b.close();
})();
