import { defineConfig } from 'astro/config';
import { unified } from '@astrojs/markdown-remark';
import { bookMarkdown } from './src/lib/book-markdown.mjs';

export default defineConfig({
  output: 'static',
  trailingSlash: 'always',
  devToolbar: { enabled: false },
  markdown: {
    processor: unified({ remarkPlugins: [bookMarkdown] }),
    shikiConfig: { theme: 'github-dark' },
  },
});
