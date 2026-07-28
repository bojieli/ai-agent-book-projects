const emojiRegex = require('emoji-regex');

// Remove emoji from the sentence
function removeEmoji(sentence) {
  const regex = emojiRegex();
  return sentence.replace(regex, ' ').trim();
}

// Convert markdown to plain text
function markdownToText(markdown) {
  let text = markdown;
  
  // Remove links, keeping only the link text
  text = text.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');
  
  // Remove headers
  text = text.replace(/^#+\s*/gm, '');
  
  // Remove bold and italic markers
  // Keep snake_case identifiers; only strip markdown __bold__ markers.
  text = text.replace(/\*\*/g, '').replace(/\*/g, '')
    .replace(/__/g, '');
  
  // Remove blockquotes
  text = text.replace(/^>\s*/gm, '');
  
  // Remove horizontal rules
  text = text.replace(/[-*_]{3,}/g, '');
  
  // Remove list markers
  text = text.replace(/^[-*+]\s*/gm, '');
  
  // Remove code block markers
  text = text.replace(/```/g, '');
  
  return text.trim();
}

// Convert numbers to words
function numberToWords(num) {
  const ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
  const tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];
  const teens = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'];
  const scales = ['', 'thousand', 'million', 'billion', 'trillion', 'quadrillion'];

  if (num === 0) return 'zero';
  if (!Number.isFinite(num)) return String(num);

  function convertGroup(n) {
    let result = '';
    
    if (n >= 100) {
      result += ones[Math.floor(n / 100)] + ' hundred ';
      n %= 100;
    }
    
    if (n >= 20) {
      result += tens[Math.floor(n / 10)] + ' ';
      n %= 10;
      if (n > 0) {
        result += ones[n] + ' ';
      }
    } else if (n >= 10) {
      result += teens[n - 10] + ' ';
    } else if (n > 0) {
      result += ones[n] + ' ';
    }
    
    return result;
  }

  let result = '';
  let groupIndex = 0;
  
  while (num > 0) {
    const group = num % 1000;
    if (group !== 0) {
      const scale = scales[groupIndex] || '';
      result = convertGroup(group) + scale + ' ' + result;
    }
    num = Math.floor(num / 1000);
    groupIndex++;
  }
  
  return result.trim();
}

// Pronounce special characters
function pronounceSpecialCharacters(text, isCodeBlock = false) {
  const specialCharMap = {
    '@': 'at',
    '#': 'hash',
    '$': 'dollar',
    '%': 'percent',
    '^': 'caret',
    '&': 'ampersand',
    '*': 'asterisk',
    '_': 'underscore',
    '=': 'equals',
    '+': 'plus',
    '[': 'left square bracket',
    ']': 'right square bracket',
    '{': 'left curly brace',
    '}': 'right curly brace',
    '|': 'vertical bar',
    '\\': 'backslash',
    '<': 'less than',
    '>': 'greater than',
    '/': 'slash',
    '`': 'backtick',
    '~': 'tilde',
  };

  const punctuationMap = {
    '!': 'exclamation',
    '.': 'dot',
    ',': 'comma',
    '?': 'question mark',
    ';': 'semicolon',
    ':': 'colon',
    '"': 'double quote',
    "'": 'single quote',
    '-': 'minus',
    '(': 'left parenthesis',
    ')': 'right parenthesis',
  };

  let processedText = text;
  
  // Replace special characters
  Object.entries(specialCharMap).forEach(([char, pronunciation]) => {
    processedText = processedText.replace(new RegExp(char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), ` ${pronunciation} `);
  });

  // Replace punctuation if in code block
  if (isCodeBlock) {
    Object.entries(punctuationMap).forEach(([char, pronunciation]) => {
      processedText = processedText.replace(new RegExp(char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), ` ${pronunciation} `);
    });
  }

  return processedText;
}

// Pronounce numbers in text
function pronounceNumbers(text, language) {
  if (language.startsWith('zh')) return text;

  // Only consume the '.' when it is a real decimal point (digits follow).
  // The old /(\d+\.?\d*)/ also matched "42." at the end of a sentence, which
  // ate the period and emitted a dangling "point".
  return text.replace(/\d+(?:\.\d+)?/g, match => {
    const num = parseFloat(match);
    if (isNaN(num)) return match;
    
    if (match.includes('.')) {
      const [integer, decimal] = match.split('.');
      return `${numberToWords(parseInt(integer))} point ${decimal.split('').map(d => numberToWords(parseInt(d))).join(' ')}`;
    }
    return numberToWords(parseInt(match));
  });
}

// Remove emotional indicators
function removeEmotions(text) {
  return text.replace(/\*[a-zA-Z0-9 -]*\*/g, '').trim();
}

// Process code blocks
function pronounceCodeBlock(text) {
  return text.replace(/`([^`\n]+)`|```(?:[\s\S]*?)```/g, (match) => {
    const content = match.startsWith('```') 
      ? match.slice(3, -3)
      : match.slice(1, -1);
    return pronounceSpecialCharacters(content, true);
  });
}

// Main preprocessing function
function preprocessSentence(sentence, language = 'en') {
  let processed = sentence;
  processed = pronounceCodeBlock(processed);
  processed = markdownToText(processed);
  processed = pronounceNumbers(processed, language);
  processed = removeEmotions(processed);
  processed = pronounceSpecialCharacters(processed);
  processed = removeEmoji(processed);
  return processed.trim();
}

module.exports = {
  preprocessSentence,
  numberToWords,
  markdownToText,
};
