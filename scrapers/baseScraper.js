const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

class BaseScraper {
  constructor(options = {}) {
    this.headless = options.headless !== undefined ? options.headless : false;
    this.slowMo = options.slowMo !== undefined ? options.slowMo : 300;
    this.browser = null;
    this.context = null;
  }

  async init() {
    this.browser = await chromium.launch({
      headless: this.headless,
      slowMo: this.slowMo
    });
    this.context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1280, height: 800 }
    });
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  }

  async downloadFile(fileUrl, outputFilename) {
    if (!this.context) {
      await this.init();
    }
    const response = await this.context.request.get(fileUrl);
    if (!response.ok()) {
      throw new Error(`Failed to download file from ${fileUrl}: Status ${response.status()}`);
    }

    const buffer = await response.body();
    const downloadsDir = path.join(__dirname, '..', 'data', 'downloads');
    if (!fs.existsSync(downloadsDir)) {
      fs.mkdirSync(downloadsDir, { recursive: true });
    }

    const filePath = path.join(downloadsDir, outputFilename);
    fs.writeFileSync(filePath, buffer);
    return { filePath, buffer };
  }

  saveJsonData(data, filename) {
    const rawDir = path.join(__dirname, '..', 'data', 'raw');
    if (!fs.existsSync(rawDir)) {
      fs.mkdirSync(rawDir, { recursive: true });
    }
    const filePath = path.join(rawDir, filename);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
    return filePath;
  }
}

module.exports = BaseScraper;
