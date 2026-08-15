const assert = require('assert');
const Module = require('module');
const orig = Module.prototype.require;
Module.prototype.require = function (id) {
  if (id === 'emoji-regex') return () => /(?!)/g;
  return orig.apply(this, arguments);
};
const { numberToWords } = require('./textProcessor.js');
assert.strictEqual(numberToWords(0), 'zero');
assert.ok(!numberToWords(1e12).includes('undefined'));
assert.ok(numberToWords(1e12).includes('trillion'));
assert.strictEqual(numberToWords(Infinity), 'Infinity');
console.log('ok');
