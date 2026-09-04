const BaseScraper = require('./baseScraper');
const { parsePrice, cleanText } = require('../utils/formatters');

class LaMamaScraper extends BaseScraper {
  constructor(options = {}) {
    super(options);
    this.targetUrl = 'https://comenzi.lamama.ro/la-mama-clubul-taranului/delivery';
  }

  async scrape() {
    console.log('Initializing La Mama scraper...');
    await this.init();

    const page = await this.context.newPage();
    const scrapedAt = new Date().toISOString();
    const itemsMap = new Map();

    // Intercept API menu responses if available
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/menu') || url.includes('/products') || url.includes('taptasty.com')) {
        try {
          const json = await response.json();
          if (json && (json.categories || json.data || Array.isArray(json))) {
            this.parseApiMenuJson(json, itemsMap, scrapedAt);
          }
        } catch (e) {
          // Response body might not be JSON
        }
      }
    });

    console.log(`Navigating to ${this.targetUrl}...`);
    await page.goto(this.targetUrl, { waitUntil: 'networkidle', timeout: 60000 });

    await page.waitForTimeout(3000);

    // Click through all category buttons/links to ensure all categories load
    const categorySelectors = [
      '.category-item',
      '.category-sticky a',
      '.category-sticky button',
      'a[href*="#cat-"]',
      'nav button',
      '[role="tab"]'
    ];

    for (const selector of categorySelectors) {
      const categoryElements = await page.$$(selector);
      if (categoryElements.length > 0) {
        console.log(`Found ${categoryElements.length} category elements matching selector '${selector}'`);
        for (let i = 0; i < categoryElements.length; i++) {
          try {
            await categoryElements[i].click({ timeout: 1000 }).catch(() => {});
            await page.waitForTimeout(500);
          } catch (e) {}
        }
        break;
      }
    }

    // Scroll down to load all dynamic content
    await page.evaluate(async () => {
      await new Promise((resolve) => {
        let totalHeight = 0;
        const distance = 300;
        const timer = setInterval(() => {
          const scrollHeight = document.body.scrollHeight;
          window.scrollBy(0, distance);
          totalHeight += distance;
          if (totalHeight >= scrollHeight) {
            clearInterval(timer);
            resolve();
          }
        }, 100);
      });
    });

    await page.waitForTimeout(2000);

    // Extract items from window.__NUXT__ or DOM if API interception didn't capture all
    const nuxtStateItems = await page.evaluate((scrapedAtTime) => {
      const results = [];
      
      // Helper to check window.__NUXT__
      try {
        const nuxtData = window.__NUXT__;
        if (nuxtData && nuxtData.data) {
          const jsonStr = JSON.stringify(nuxtData.data);
          // Look for products in nuxt state
        }
      } catch (e) {}

      // Extract directly from DOM product cards
      const cards = Array.from(document.querySelectorAll('.product-card, [class*="product-card"], [class*="productCard"], article, .grid > div'));
      
      cards.forEach((card) => {
        const titleEl = card.querySelector('[class*="title"], h2, h3, h4, .font-bold');
        const priceEl = card.querySelector('[class*="price"], .font-semibold');
        const descEl = card.querySelector('[class*="desc"], [class*="description"], p');
        const catEl = card.closest('[id*="cat-"], section, div')?.querySelector('h2, h3, [class*="category"]');

        const title = titleEl ? titleEl.innerText.trim() : '';
        const priceText = priceEl ? priceEl.innerText.trim() : '';
        const desc = descEl ? descEl.innerText.trim() : '';
        const cat = catEl ? catEl.innerText.trim() : 'Meniu General';

        if (title && priceText && priceText.match(/\d+/)) {
          results.push({
            restaurant_name: 'La Mama',
            category: cat,
            item_name: title,
            description: desc !== title ? desc : '',
            priceText: priceText,
            scraped_at: scrapedAtTime
          });
        }
      });

      return results;
    }, scrapedAt);

    nuxtStateItems.forEach(item => {
      const p = parsePrice(item.priceText);
      if (p !== null && item.item_name) {
        const key = item.item_name.toLowerCase();
        let grammageVal = item.grammage || null;
        let descVal = cleanText(item.description);

        const weightMatch = descVal.match(/^\((\d+\s*(?:g|ml|kg|l|buc|g\+)?)\)\s*/i);
        if (weightMatch) {
          grammageVal = weightMatch[1];
          descVal = descVal.replace(/^\(\d+\s*(?:g|ml|kg|l|buc|g\+)?\)\s*/i, '').trim();
        }

        if (!itemsMap.has(key)) {
          itemsMap.set(key, {
            restaurant_name: 'La Mama',
            category: cleanText(item.category),
            item_name: cleanText(item.item_name),
            grammage: grammageVal,
            description: descVal,
            price: p,
            currency: 'RON',
            scraped_at: scrapedAt
          });
        }
      }
    });

    const items = Array.from(itemsMap.values());
    console.log(`Extracted ${items.length} items from La Mama.`);

    const savedPath = this.saveJsonData(items, 'la_mama.json');
    console.log(`Saved JSON data to: ${savedPath}`);

    await page.close();
    await this.close();

    return items;
  }

  parseApiMenuJson(json, itemsMap, scrapedAt) {
    const parseProductsArray = (prods, categoryName = 'Meniu General') => {
      if (!Array.isArray(prods)) return;
      prods.forEach(p => {
        const name = p.name || p.title || p.item_name;
        const priceVal = p.price || p.final_price || p.price_val;
        if (name && priceVal !== undefined) {
          const key = name.toLowerCase();
          if (!itemsMap.has(key)) {
            itemsMap.set(key, {
              restaurant_name: 'La Mama',
              category: cleanText(categoryName),
              item_name: cleanText(name),
              grammage: p.weight || p.size || null,
              description: cleanText(p.description || p.desc || ''),
              price: parsePrice(priceVal),
              currency: 'RON',
              scraped_at: scrapedAt
            });
          }
        }
      });
    };

    if (json.categories && Array.isArray(json.categories)) {
      json.categories.forEach(c => {
        const catName = c.name || c.title || 'Meniu General';
        if (c.products) parseProductsArray(c.products, catName);
        if (c.items) parseProductsArray(c.items, catName);
      });
    } else if (Array.isArray(json)) {
      parseProductsArray(json);
    }
  }
}

if (require.main === module) {
  const scraper = new LaMamaScraper({ headless: false, slowMo: 300 });
  scraper.scrape()
    .then(items => {
      console.log('La Mama scraping complete. Items count:', items.length);
    })
    .catch(err => {
      console.error('Scraping failed:', err);
      process.exit(1);
    });
}

module.exports = LaMamaScraper;
