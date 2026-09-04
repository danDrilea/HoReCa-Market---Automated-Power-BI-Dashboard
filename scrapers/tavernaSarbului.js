const BaseScraper = require('./baseScraper');
const { parsePrice, cleanText } = require('../utils/formatters');

class TavernaSarbuluiScraper extends BaseScraper {
  constructor(options = {}) {
    super(options);
    this.targetUrl = 'https://dinehub.eu/r/taverna-sarbului-bucuresti-sector1/menu';

    this.categoriesToScrape = [
      {
        main: 'Meniu Mancare',
        subs: ['Aperitive', 'Ciorbe', 'Peste', 'Specialitati', 'Gratar', 'Garnituri', 'Brutarie', 'Salate', 'Desert']
      },
      {
        main: 'Steakhouse',
        subs: []
      },
      {
        main: 'Business Lunch',
        subs: []
      },
      {
        main: 'Comanda din Timp',
        subs: []
      },
      {
        main: 'Meniu Copii',
        subs: []
      },
      {
        main: 'Magaza',
        subs: []
      },
      {
        main: 'Bauturi',
        subs: [
          'Serbian Alcohol', 'Soft Drinks', 'Coffee', 'Draught Beer',
          'Lager', 'Non-alcoholic beer', 'Specialties', 'Craft beer', 'House Wine',
          'Miniature Wines', 'White Wines', 'Rose Wines', 'Red Wines',
          'Sparkling Wines', 'Miniature Bubbles', 'Drink',
          'Cocktails', 'Aperitivo', 'Gin', 'Tequila',
          'Rom', 'Vodka', 'Whiskey', 'Bitters', 'Brandy'
        ]
      }
    ];
  }

  async scrape() {
    console.log('Initializing Taverna Sarbului scraper...');
    await this.init();

    const page = await this.context.newPage();
    const scrapedAt = new Date().toISOString();
    const itemsMap = new Map();

    console.log(`Navigating to ${this.targetUrl}...`);
    await page.goto(this.targetUrl, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(3000);

    // Flexible category clicker using string contains & regex
    const clickCategoryByName = async (categoryName) => {
      const clicked = await page.evaluate((target) => {
        const cleanTarget = target.toLowerCase().replace(/[^a-z0-9]/g, '');
        const elements = Array.from(document.querySelectorAll('button, a, div, span, p, h2, h3, li'));
        
        const match = elements.find(el => {
          const text = (el.innerText || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
          return text.includes(cleanTarget) && text.length < cleanTarget.length + 15 && el.children.length < 3;
        });

        if (match) {
          match.click();
          return true;
        }
        return false;
      }, categoryName);

      if (clicked) {
        console.log(`Clicked category: "${categoryName}"`);
        await page.waitForTimeout(1200);
      } else {
        console.log(`Category NOT found on page: "${categoryName}"`);
      }
      return clicked;
    };

    // Extract products from current page DOM
    const extractItemsFromDOM = async (currentCatLabel) => {
      const foundProducts = await page.evaluate((categoryName) => {
        const results = [];
        const allNodes = Array.from(document.querySelectorAll('div, section, article, li'));
        
        allNodes.forEach(node => {
          const text = (node.innerText || '').trim();
          if (text.match(/\d+(?:[\.,]\d{1,2})?\s*(?:lei|LEI|RON|ron)/i) && text.length > 5 && text.length < 400 && node.children.length < 8) {
            const lines = text.split(/\n+/).map(l => l.trim()).filter(l => l.length > 0);
            if (lines.length >= 2) {
              const priceLine = lines.find(l => l.match(/\d+(?:[\.,]\d{1,2})?\s*(?:lei|LEI|RON|ron)/i));
              const nameLine = lines.find(l => !l.match(/\d+(?:[\.,]\d{1,2})?\s*(?:lei|LEI|RON|ron)/i) && l.length >= 2);
              
              if (nameLine && priceLine) {
                const descLine = lines.filter(l => l !== nameLine && l !== priceLine).join(' ');
                results.push({
                  category: categoryName,
                  name: nameLine,
                  priceText: priceLine,
                  desc: descLine
                });
              }
            }
          }
        });

        return results;
      }, currentCatLabel);

      foundProducts.forEach(p => {
        const priceVal = parsePrice(p.priceText);
        if (priceVal !== null && p.name) {
          let titleClean = p.name;
          let grammageVal = null;

          const gMatch = titleClean.match(/\b(\d+\s*(?:g|ml|kg|l|buc))\b/i) || p.desc.match(/\b(\d+\s*(?:g|ml|kg|l|buc))\b/i);
          if (gMatch) {
            grammageVal = gMatch[1];
            titleClean = titleClean.replace(/\b\d+\s*(?:g|ml|kg|l|buc)\b/i, '').trim();
          }

          const key = titleClean.toLowerCase();
          if (!itemsMap.has(key)) {
            itemsMap.set(key, {
              restaurant_name: 'Taverna Sârbului',
              category: cleanText(p.category),
              item_name: cleanText(titleClean),
              grammage: grammageVal,
              description: cleanText(p.desc),
              price: priceVal,
              currency: 'RON',
              scraped_at: scrapedAt
            });
          }
        }
      });
    };

    // Iterate through category groups
    for (const catGroup of this.categoriesToScrape) {
      const mainClicked = await clickCategoryByName(catGroup.main);
      if (mainClicked) {
        await extractItemsFromDOM(catGroup.main);

        if (catGroup.subs && catGroup.subs.length > 0) {
          for (const subName of catGroup.subs) {
            await clickCategoryByName(subName);
            await extractItemsFromDOM(`${catGroup.main} - ${subName}`);
          }
        }
      }
    }

    // Scroll through page to catch any remaining section items
    for (let s = 0; s < 8; s++) {
      await page.evaluate(() => window.scrollBy(0, 500));
      await page.waitForTimeout(400);
      await extractItemsFromDOM('Meniu General');
    }

    const items = Array.from(itemsMap.values());
    console.log(`Extracted ${items.length} total items from Taverna Sarbului.`);

    const savedPath = this.saveJsonData(items, 'taverna_sarbului.json');
    console.log(`Saved JSON data to: ${savedPath}`);

    await page.close();
    await this.close();

    return items;
  }
}

if (require.main === module) {
  const scraper = new TavernaSarbuluiScraper({ headless: false, slowMo: 300 });
  scraper.scrape()
    .then(items => {
      console.log('Taverna Sarbului scraping complete. Items count:', items.length);
    })
    .catch(err => {
      console.error('Scraping failed:', err);
      process.exit(1);
    });
}

module.exports = TavernaSarbuluiScraper;
