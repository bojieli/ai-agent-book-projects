const assert = require('assert');
const Module = require('module');
const orig = Module.prototype.require;
Module.prototype.require = function (id) {
  if (id === 'emoji-regex') return () => /(?!)/g;
  return orig.apply(this, arguments);
};
const { markdownToText } = require('./textProcessor.js');
const out = markdownToText('Call get_user_id then save_to_db');
assert.ok(out.includes('get_user_id'));
assert.ok(out.includes('save_to_db'));
console.log('ok');
