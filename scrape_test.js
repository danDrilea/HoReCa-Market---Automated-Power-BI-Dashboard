const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('https://ro.wikipedia.org/wiki/HoReCa');

  const title = await page.locator('#firstHeading').innerText();
  const paragraphs = await page.locator('#bodyContent p').allInnerTexts();
  const content = paragraphs.find(p => p.trim().length > 0);

  console.log({ title, content });

  await browser.close();
})();
