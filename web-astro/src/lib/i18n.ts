import messages from './translations.json';
export const locales = ['en', 'zh-CN', 'zh-TW'] as const;
export type Locale = (typeof locales)[number];
export const editions = {
  en: {
    name: 'English',
    home: '/',
    chapter: '/book-en/chapter1/',
    directory: 'book-en',
    suffix: '',
    pdf: 'en',
  },
  'zh-CN': {
    name: '简体中文',
    home: '/zh-CN/',
    chapter: '/book/chapter1/',
    directory: 'book',
    suffix: '',
    pdf: 'zh-CN',
  },
  'zh-TW': {
    name: '繁體中文',
    home: '/zh-TW/',
    chapter: '/book-zhtw/chapter1.zhtw/',
    directory: 'book-zhtw',
    suffix: '.zhtw',
    pdf: 'zh-TW',
  },
} as const;
export function translator(locale: string) {
  return (message: string): string => {
    const translation = (messages as Record<string, string[]>)[message];
    return (
      translation?.[locale === 'zh-CN' ? 0 : locale === 'zh-TW' ? 1 : -1] ??
      message
    );
  };
}
export function browserTranslator() {
  return translator(document.documentElement.lang);
}
