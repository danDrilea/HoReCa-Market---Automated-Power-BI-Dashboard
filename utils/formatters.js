function parsePrice(priceStr) {
  if (typeof priceStr === 'number') return priceStr;
  if (!priceStr) return null;
  
  const cleaned = priceStr
    .toString()
    .trim()
    .replace(/\s+/g, '')
    .replace(',', '.');

  const match = cleaned.match(/(\d+(?:\.\d+)?)/);
  return match ? parseFloat(match[1]) : null;
}

function cleanText(text) {
  if (!text) return '';
  return text.replace(/\s+/g, ' ').trim();
}

module.exports = {
  parsePrice,
  cleanText
};
