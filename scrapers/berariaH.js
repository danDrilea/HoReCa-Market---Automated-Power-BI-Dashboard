const BaseScraper = require('./baseScraper');
const { parseMenuPdf } = require('../utils/pdfParser');

class BerariaHScraper extends BaseScraper {
  constructor(options = {}) {
    super(options);
    this.pdfUrl = 'https://berariah.ro/meniu_beraria_h.pdf?v22';
    this.fallbackPageUrl = 'https://www.berariah.ro/meniu';
  }

  async scrape() {
    console.log('Initializing Beraria H scraper...');
    await this.init();

    let targetUrl = this.pdfUrl;

    try {
      console.log(`Downloading PDF menu from: ${targetUrl}`);
      const { filePath, buffer } = await this.downloadFile(targetUrl, 'beraria_h_menu.pdf');
      console.log(`PDF saved to: ${filePath}`);

      console.log('Parsing PDF menu text...');
      const items = await parseMenuPdf(buffer, 'Berăria H');

      console.log(`Extracted ${items.length} items.`);
      const savedPath = this.saveJsonData(items, 'beraria_h.json');
      console.log(`Saved JSON data to: ${savedPath}`);

      return items;
    } catch (err) {
      console.error('PDF download/parsing error:', err.message);
      console.log('Attempting fallback navigation...');
      const page = await this.context.newPage();
      await page.goto(this.fallbackPageUrl, { waitUntil: 'domcontentloaded' });
      
      const dynamicPdfUrl = await page.evaluate(() => {
        const link = document.querySelector('a[href*=".pdf"]');
        return link ? link.href : null;
      });

      if (dynamicPdfUrl) {
        console.log(`Found dynamic PDF URL: ${dynamicPdfUrl}`);
        const { buffer } = await this.downloadFile(dynamicPdfUrl, 'beraria_h_menu.pdf');
        const items = await parseMenuPdf(buffer, 'Berăria H');
        this.saveJsonData(items, 'beraria_h.json');
        return items;
      }
      throw err;
    } finally {
      await this.close();
    }
  }
}

if (require.main === module) {
  const scraper = new BerariaHScraper({ headless: false, slowMo: 300 });
  scraper.scrape()
    .then(items => {
      console.log('Beraria H scraping complete. Items count:', items.length);
    })
    .catch(err => {
      console.error('Scraping failed:', err);
      process.exit(1);
    });
}

module.exports = BerariaHScraper;
