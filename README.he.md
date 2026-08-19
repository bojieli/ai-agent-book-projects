# סוכני AI לעומק: עקרונות עיצוב ופרקטיקה הנדסית

[![PDF](https://img.shields.io/badge/PDF-הורדה-success.svg)](#ספר-אלקטרוני) [![קריאה מקוונת](https://img.shields.io/badge/🌐_קריאה_מקוונת-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/index.he/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE) [![Languages](https://img.shields.io/badge/תרגומים-14%20שפות-informational.svg)](#ספר-אלקטרוני)

[中文](README.md) · [English](docs/en/README.md) · [Español](docs/es/README.md) · [Bahasa Indonesia](docs/id/README.md) · [العربية](docs/ar/README.md) · [繁體中文（台灣）](docs/zh-TW/README.md) · [Русский](docs/ru/README.md) · [Tiếng Việt](docs/vi/README.md) · [தமிழ்](docs/ta/README.md) · [日本語](docs/ja/README.md) · [Türkçe](docs/tr/README.md) · [한국어](docs/ko/README.md) · [Magyar](docs/hu/README.md) · **עברית** ← נוכחי

> 📥 **[הורדת PDF / EPUB](#ספר-אלקטרוני)** (מומלץ) — מהדורות ה־PDF וה־EPUB מספקות את חוויית הקריאה הטובה ביותר. ניתן גם [לקרוא באתר](https://bojieli.github.io/ai-agent-book/index.he/) עם ניווט מלא מימין לשמאל, מעבר בין שפות וחיפוש בטקסט המלא.

**סוכן = LLM + הקשר + כלים** — הספר בנוי סביב נוסחה זו ומציג בעשרה פרקים את העקרונות ואת הפרקטיקה ההנדסית של סוכני AI.

> 📢 **השינויים בגרסה 2.0 לעומת 1.4:** גרסה 2.0 מאחדת את החלק „אינטראקציה אסינכרונית” מהפרק הרביעי הקודם עם התוכן על „סוכנים רב־מודאליים” מהפרק התשיעי הקודם, ומארגנת אותם מחדש כפרק השישי החדש, „אינטראקציה: הרחבת מרחבי התצפית והפעולה”. הפרקים הקודמים 6 („הערכת סוכנים”), 7 („אימון־על של מודלים”) ו־8 („התפתחות מתמשכת של סוכנים”) הוזזו כל אחד בפרק אחד, וכעת הם פרקים 7, 8 ו־9 בהתאמה.
>
> אם ברשותכם PDF ישן, מומלץ [להוריד את ה־PDF העדכני ביותר](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-he.pdf). המהדורה החדשה כוללת גם תיקונים והתאמות רבים בתוכן; אנא הסתמכו על הגרסה העדכנית ביותר.

התרגום העברי המלא נתרם על ידי [@itzikwo](https://github.com/itzikwo). תודה על התרגום ועל עבודת ההנדסה המוקפדת שאפשרה עימוד RTL תקין ב־PDF וב־EPUB.

## ספר אלקטרוני

- **עברית** — תרגום קהילתי מאת [@itzikwo](https://github.com/itzikwo): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-he.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-he.epub)
- **המקור בסינית**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)

## תוכן הספר

| פרק | נושא | קריאה |
| :--: | --- | :--: |
| — | הקדמה | [קריאה](book-he/introduction.he.md) |
| 1 | צעדים ראשונים עם סוכני AI | [קריאה](book-he/chapter1.he.md) |
| 2 | הנדסת הקשר | [קריאה](book-he/chapter2.he.md) |
| 3 | זיכרון משתמש ובסיס ידע | [קריאה](book-he/chapter3.he.md) |
| 4 | כלים | [קריאה](book-he/chapter4.he.md) |
| 5 | סוכן קוד ויצירת קוד | [קריאה](book-he/chapter5.he.md) |
| 6 | אינטראקציה: הרחבת מרחבי התצפית והפעולה | [קריאה](book-he/chapter6.he.md) |
| 7 | הערכת סוכנים | [קריאה](book-he/chapter7.he.md) |
| 8 | אימון־על של מודלים | [קריאה](book-he/chapter8.he.md) |
| 9 | התפתחות מתמשכת של סוכנים | [קריאה](book-he/chapter9.he.md) |
| 10 | שיתוף פעולה רב־סוכני | [קריאה](book-he/chapter10.he.md) |
| — | אחרית דבר | [קריאה](book-he/afterword.he.md) |

התיעוד של הניסויים הנלווים עדיין אינו מתורגם לעברית. קוד הניסויים וההוראות באנגלית או בסינית זמינים בתיקיות `chapter1/` עד `chapter10/`.

## בנייה מקומית

לבניית ה־PDF נדרשים Pandoc,‏ LuaLaTeX,‏ librsvg וגופני Culmus הכלולים ב־TeX Live:

```bash
cd book-he
bash build_pdf.sh
```

לאחר בניית ה־PDF ניתן לבנות ולאמת את ה־EPUB משורש המאגר:

```bash
./build_epub.sh he
```

המקור של המהדורה העברית נמצא בתיקייה [`book-he/`](book-he/). התוכן מתעדכן באופן שוטף ועשוי להשתנות ביחס למהדורה הסינית המקורית.
