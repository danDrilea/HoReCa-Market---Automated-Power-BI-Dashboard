const pdfParseModule = require('pdf-parse');
const { parsePrice, cleanText } = require('./formatters');

async function extractTextFromPdf(pdfBuffer) {
  if (pdfParseModule.PDFParse) {
    const parser = new pdfParseModule.PDFParse({ data: pdfBuffer });
    const textResult = await parser.getText();
    const text = textResult.text || '';
    await parser.destroy();
    return text;
  } else if (typeof pdfParseModule === 'function') {
    const data = await pdfParseModule(pdfBuffer);
    return data.text || '';
  } else {
    throw new Error('Unsupported pdf-parse module format');
  }
}

function isMostlyUppercase(str) {
  const letters = str.replace(/[^a-zA-ZĂÂÎȘȚăâîșț]/g, '');
  if (letters.length < 3) return false;
  const upperCount = (letters.match(/[A-ZĂÂÎȘȚ]/g) || []).length;
  return upperCount / letters.length > 0.7;
}

async function parseMenuPdf(pdfBuffer, restaurantName = 'Berăria H') {
  const rawText = await extractTextFromPdf(pdfBuffer);
  
  const lines = rawText
    .split(/\r?\n/)
    .map(line => cleanText(line))
    .filter(line => line.length > 0);

  const scrapedAt = new Date().toISOString();
  const items = [];
  
  let currentCategory = 'MENIU GENERAL';
  let bufferTextParts = [];

  const priceRegex = /(\d+(?:[\.,]\d{1,2})?)\s*(?:LEI|lei|RON|ron)\b/i;
  const grammageRegex = /\b(\d+\s*(?:g|ml|kg|l|buc|metru))\b/i;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.includes('MENIU') && line.includes('BERARIA H')) continue;
    if (line.includes('Prețurile includ TVA') || line.includes('Pagina')) continue;

    if (
      isMostlyUppercase(line) && 
      line.length > 3 && 
      !line.match(priceRegex) && 
      !line.match(grammageRegex) &&
      !line.match(/\d+/)
    ) {
      currentCategory = cleanText(line);
      bufferTextParts = [];
      continue;
    }

    const priceMatch = line.match(priceRegex);
    if (priceMatch) {
      const priceVal = parsePrice(priceMatch[1]);
      
      let lineWithoutPrice = line.replace(priceRegex, '').trim();
      if (lineWithoutPrice) {
        bufferTextParts.push(lineWithoutPrice);
      }

      let allText = bufferTextParts.join(' ');
      bufferTextParts = [];

      let grammage = null;
      const gMatch = allText.match(grammageRegex);
      if (gMatch) {
        grammage = gMatch[1];
        allText = allText.replace(grammageRegex, '').trim();
      }

      const words = allText.split(' ');
      let titleWords = [];
      let descWords = [];

      for (const w of words) {
        if (isMostlyUppercase(w)) {
          titleWords.push(w);
        } else {
          descWords.push(w);
        }
      }

      let itemName = titleWords.length > 0 ? titleWords.join(' ') : allText;
      let description = titleWords.length > 0 ? descWords.join(' ') : '';

      itemName = cleanText(itemName.replace(/[\.\_\-\–,]+$/g, ''));
      description = cleanText(description.replace(/\s+\b(DE|LA|CU)\b$/gi, ''));

      if (itemName.length >= 2 && priceVal !== null) {
        items.push({
          restaurant_name: restaurantName,
          category: currentCategory,
          item_name: itemName,
          grammage: grammage,
          description: description,
          price: priceVal,
          currency: 'RON',
          scraped_at: scrapedAt
        });
      }
    } else {
      bufferTextParts.push(line);
    }
  }

  return items;
}

module.exports = {
  extractTextFromPdf,
  parseMenuPdf
};
