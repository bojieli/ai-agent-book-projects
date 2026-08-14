import { existsSync } from "node:fs";
import { readFile, readdir, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { lessons } from "./course.mjs";
import { chapter1PilotFigures, chapter1PilotSlideCount } from "./chapter1-pilot.mjs";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const REPO = path.resolve(HERE, "..");
const CJK = /[\u3400-\u9fff\uf900-\ufaff]/u;

function fail(message) {
  throw new Error(message);
}

function movementFor(lesson) {
  if (lesson.number <= 21) return "Build";
  if (lesson.number <= 34) return "Improve";
  return "Expand";
}

function demoMinutes(lesson) {
  return lesson.experiments.reduce((sum, experiment) => sum + experiment.duration, 0);
}

function extensionSlideCount(lesson) {
  return lesson.extensions.length <= 6 ? 1 : 2;
}

function isChapterStart(lesson) {
  return !lessons.some((candidate) => candidate.chapter === lesson.chapter && candidate.number < lesson.number);
}

function slideCount(lesson) {
  const pilotCount = chapter1PilotSlideCount(lesson.number);
  if (pilotCount !== null) return pilotCount;
  const compacted = demoMinutes(lesson) >= 5 ? (isChapterStart(lesson) ? 1 : 2) : 0;
  return 15 + Math.max(0, extensionSlideCount(lesson) - 1) + (lesson.synthesis ? 1 : 0) - compacted;
}

function duration(lesson) {
  return slideCount(lesson) + demoMinutes(lesson);
}

function splitSlides(source) {
  const lines = source.split("\n");
  const slides = [];
  let index = 0;

  if (lines[index] === "---") {
    index += 1;
    while (index < lines.length && lines[index] !== "---") index += 1;
    index += 1;
  }

  while (index < lines.length) {
    const body = [];
    while (index < lines.length && lines[index] !== "---") {
      body.push(lines[index]);
      index += 1;
    }
    slides.push(body.join("\n"));
    if (index >= lines.length) break;

    index += 1;
    if (/^(?:layout|class|transition):/.test(lines[index] || "")) {
      while (index < lines.length && lines[index] !== "---") index += 1;
      index += 1;
    }
  }
  return slides.filter((slide) => slide.trim());
}

function visibleText(markdown) {
  return markdown
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/~~~\w*\n?/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&(?:amp|quot|lt|gt);/g, " ")
    .replace(/[#*`$]/g, " ");
}

function words(text) {
  return text.match(/[A-Za-z0-9][A-Za-z0-9+./:'’_–—-]*/g) || [];
}

function textBlocks(markdown) {
  const blocks = [];
  for (const match of markdown.matchAll(/<(?:p(?=[\s>])|h3(?=[\s>])|div class="course-(?:big|boundary|rule|next|terminal-watch)")[^>]*>([\s\S]*?)<\/[^>]+>/g)) {
    blocks.push(visibleText(match[1]));
  }
  return blocks;
}

async function main() {
  if (lessons.length !== 42) fail("Expected 42 lessons");
  const deckFiles = (await readdir(HERE)).filter((name) => /^lesson-\d{2}\.md$/.test(name)).sort();
  if (deckFiles.length !== 42) fail("Expected 42 generated deck files; found " + deckFiles.length);

  const chapterStarts = new Set(lessons.filter(isChapterStart).map((lesson) => lesson.number));
  const bookText = (await Promise.all(Array.from({ length: 10 }, (_, index) =>
    readFile(path.join(REPO, "book-en", "chapter" + (index + 1) + ".md"), "utf8")
  ))).join("\n");
  const bookExperiments = [...new Set([...bookText.matchAll(/Experiment\s+(\d+-\d+)/g)].map((match) => match[1]))];
  const courseMetadata = JSON.stringify(lessons);
  const missingExperiments = bookExperiments.filter((id) => !courseMetadata.includes(id));
  if (missingExperiments.length) fail("Book experiments missing from anchors/extensions: " + missingExperiments.join(", "));

  let totalSlides = 0;
  let totalCommands = 0;
  let maxSlideWords = { count: 0, lesson: 0, slide: 0 };
  let maxBlockWords = { count: 0, lesson: 0, slide: 0, text: "" };
  const durationHistogram = new Map();

  for (const [index, lesson] of lessons.entries()) {
    const number = index + 1;
    const lessonNo = String(number).padStart(2, "0");
    if (lesson.number !== number) fail("Lesson numbering is not consecutive at " + lessonNo);
    if (!lesson.title.endsWith("?")) fail("Lesson " + lessonNo + " title is not problem-oriented");
    if (lesson.experiments.length < 1 || lesson.experiments.length > 3) fail("Lesson " + lessonNo + " must anchor 1–3 experiments");

    const target = duration(lesson);
    if (target < 15 || target > 20) fail("Lesson " + lessonNo + " duration is " + target + " minutes");
    durationHistogram.set(target, (durationHistogram.get(target) || 0) + 1);

    const source = await readFile(path.join(HERE, deckFiles[index]), "utf8");
    if (CJK.test(source)) fail("Lesson " + lessonNo + " contains visible or source CJK text");
    if ((source.match(/Switching to the terminal/g) || []).length !== 1) fail("Lesson " + lessonNo + " needs one terminal handoff");
    const commands = (source.match(/^\$ /gm) || []).length;
    if (commands !== lesson.experiments.length) fail("Lesson " + lessonNo + " command/experiment mismatch");
    totalCommands += commands;
    const pilot = chapter1PilotSlideCount(number) !== null;
    const figureCount = (source.match(/<img /g) || []).length;
    if (pilot && figureCount < 2) fail("Lesson " + lessonNo + " needs multiple Chapter 1 figures");
    if (!pilot && figureCount !== 1) fail("Lesson " + lessonNo + " needs exactly one primary figure");
    const fencedCodeCount = (source.match(/^~~~(?:python|bash|javascript|json|typescript|text)/gm) || []).length;
    const htmlCodeCount = pilot ? (source.match(/<pre class="chapter-code-block/g) || []).length : 0;
    if (fencedCodeCount + htmlCodeCount < 2) fail("Lesson " + lessonNo + " needs conceptual and terminal code");
    const coursePosition = pilot
      ? (movementFor(lesson) + " · " + lesson.chapter + " · " + lesson.part).toUpperCase()
      : movementFor(lesson) + " · " + lesson.chapter + " · " + lesson.part;
    if (!source.includes(coursePosition)) fail("Lesson " + lessonNo + " cover lacks course position");
    if (!source.includes("Lesson " + lessonNo + " of 42 · " + target + " minutes")) fail("Lesson " + lessonNo + " cover timing is stale");

    const mapCount = (source.match(/Problems this chapter will solve/g) || []).length;
    const expectedMaps = !pilot && chapterStarts.has(number) && lesson.chapter !== "Introduction" ? 1 : 0;
    if (mapCount !== expectedMaps) fail("Lesson " + lessonNo + " chapter-map mismatch");

    const slides = splitSlides(source);
    if (slides.length !== slideCount(lesson)) fail("Lesson " + lessonNo + " rendered " + slides.length + " slides; expected " + slideCount(lesson));
    totalSlides += slides.length;

    for (const [slideIndex, slide] of slides.entries()) {
      const count = words(visibleText(slide)).length;
      if (count > maxSlideWords.count) maxSlideWords = { count, lesson: number, slide: slideIndex + 1 };
      const slideWordLimit = pilot ? 190 : 105;
      const blockWordLimit = pilot ? 70 : 38;
      if (count > slideWordLimit) fail("Lesson " + lessonNo + " slide " + (slideIndex + 1) + " is too dense at " + count + " words");
      for (const block of textBlocks(slide)) {
        const blockCount = words(block).length;
        if (blockCount > maxBlockWords.count) {
          maxBlockWords = { count: blockCount, lesson: number, slide: slideIndex + 1, text: block };
        }
        if (blockCount > blockWordLimit) fail("Lesson " + lessonNo + " slide " + (slideIndex + 1) + " has a paragraph-like block of " + blockCount + " words");
      }
    }

    const figurePath = path.join(REPO, "book-en", "images", lesson.figure);
    if (!existsSync(figurePath)) fail("Lesson " + lessonNo + " figure is missing");
    if (CJK.test(await readFile(figurePath, "utf8"))) fail("Lesson " + lessonNo + " figure contains CJK labels");
    for (const experiment of lesson.experiments) {
      if (!existsSync(path.join(REPO, experiment.path))) fail("Lesson " + lessonNo + " experiment path is missing: " + experiment.path);
    }
    for (const [, targetPath] of lesson.extensions) {
      if (!/^(?:https?:|#|mailto:)/.test(targetPath) && !existsSync(path.join(REPO, targetPath))) {
        fail("Lesson " + lessonNo + " extension path is missing: " + targetPath);
      }
    }

    const builtIndex = path.join(HERE, "dist", "lesson-" + lessonNo, "index.html");
    if (existsSync(builtIndex)) await stat(builtIndex);
  }

  for (const figure of chapter1PilotFigures) {
    const figurePath = path.join(REPO, "book-en", "images", figure);
    if (!existsSync(figurePath)) fail("Chapter 1 pilot figure is missing: " + figure);
    if (CJK.test(await readFile(figurePath, "utf8"))) fail("Chapter 1 pilot figure contains CJK labels: " + figure);
  }

  console.log(JSON.stringify({
    lessons: lessons.length,
    slides: totalSlides,
    terminalCommands: totalCommands,
    bookExperimentsCovered: bookExperiments.length,
    durationHistogram: Object.fromEntries([...durationHistogram].sort(([a], [b]) => a - b)),
    maxSlideWords,
    maxTextBlockWords: maxBlockWords
  }, null, 2));
}

await main();
