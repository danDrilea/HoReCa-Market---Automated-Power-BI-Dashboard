const path = require('path');
const fs = require('fs');

const BerariaHScraper = require('./scrapers/berariaH');
const LaMamaScraper = require('./scrapers/laMama');
const TavernaSarbuluiScraper = require('./scrapers/tavernaSarbului');

async function runOrchestrator(options = { headless: false, slowMo: 300 }) {
  console.log('Starting HoReCa competitor scrapers pipeline...');
  console.log(`Execution mode: ${options.headless ? 'Headless (hidden)' : 'Headed (visible browser)'}`);
  const startTime = Date.now();

  const results = {
    berariaH: [],
    laMama: [],
    tavernaSarbului: []
  };

  try {
    console.log('\n[1/3] Running Beraria H scraper...');
    const berariaScraper = new BerariaHScraper(options);
    results.berariaH = await berariaScraper.scrape();
    console.log(`Beraria H completed: ${results.berariaH.length} items.`);
  } catch (err) {
    console.error('Beraria H scraper error:', err.message);
  }

  try {
    console.log('\n[2/3] Running La Mama scraper...');
    const laMamaScraper = new LaMamaScraper(options);
    results.laMama = await laMamaScraper.scrape();
    console.log(`La Mama completed: ${results.laMama.length} items.`);
  } catch (err) {
    console.error('La Mama scraper error:', err.message);
  }

  try {
    console.log('\n[3/3] Running Taverna Sarbului scraper...');
    const tavernaScraper = new TavernaSarbuluiScraper(options);
    results.tavernaSarbului = await tavernaScraper.scrape();
    console.log(`Taverna Sarbului completed: ${results.tavernaSarbului.length} items.`);
  } catch (err) {
    console.error('Taverna Sarbului scraper error:', err.message);
  }

  const combinedItems = [
    ...results.berariaH,
    ...results.laMama,
    ...results.tavernaSarbului
  ];

  const rawDir = path.join(__dirname, 'data', 'raw');
  if (!fs.existsSync(rawDir)) {
    fs.mkdirSync(rawDir, { recursive: true });
  }

  const outputPath = path.join(rawDir, 'competitors_scraped.json');
  fs.writeFileSync(outputPath, JSON.stringify(combinedItems, null, 2), 'utf-8');

  const durationSec = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log('\n========================================');
  console.log('Pipeline Summary:');
  console.log(`- Beraria H:       ${results.berariaH.length} items`);
  console.log(`- La Mama:         ${results.laMama.length} items`);
  console.log(`- Taverna Sarbului: ${results.tavernaSarbului.length} items`);
  console.log(`- Total Combined:  ${combinedItems.length} items`);
  console.log(`- Total Execution: ${durationSec}s`);
  console.log(`- Saved Output:    ${outputPath}`);
  console.log('========================================\n');

  return combinedItems;
}

if (require.main === module) {
  const isHeadless = process.argv.includes('--headless');
  runOrchestrator({ headless: isHeadless, slowMo: isHeadless ? 0 : 300 });
}

module.exports = runOrchestrator;
