import { copyFile, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { lessons } from "./course.mjs";
import {
  chapter1PilotFigures,
  chapter1PilotSlideCount,
  renderChapter1Pilot
} from "./chapter1-pilot.mjs";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const REPO = path.resolve(HERE, "..");
const PUBLIC_IMAGES = path.join(HERE, "public", "images");
const CJK = new RegExp("[\\u3400-\\u9fff\\uf900-\\ufaff]", "u");

function fail(message) {
  throw new Error(message);
}

function yaml(value) {
  return JSON.stringify(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function repositoryHref(target) {
  if (/^(?:https?:|#|mailto:)/.test(target)) return target;
  return "../" + target.replace(/^\.\//, "");
}

function cards(items, colors = ["blue", "green", "orange"]) {
  return [
    '<div class="grid grid-cols-' + Math.min(items.length, 3) + ' gap-5 mt-6">',
    ...items.map(([title, text], index) => [
      '<div class="course-card ' + colors[index % colors.length] + '">',
      "<h3>" + escapeHtml(title) + "</h3>",
      "<p>" + escapeHtml(text) + "</p>",
      "</div>"
    ].join("\n")),
    "</div>"
  ].join("\n");
}

function slide(options, body, cue) {
  const hasFrontmatter = Boolean(options.layout || options.className || options.transition);
  const metadata = ["---"];
  if (hasFrontmatter) {
    if (options.layout) metadata.push("layout: " + options.layout);
    if (options.className) metadata.push("class: " + options.className);
    if (options.transition) metadata.push("transition: " + options.transition);
    metadata.push("---");
  }
  metadata.push("", body.trim(), "");
  if (cue) metadata.push("<!-- Presenter cue: " + cue + " -->", "");
  return metadata.join("\n");
}

function extensionSlide(chunk, index, total) {
  const title = total === 1 ? "Continue the experiment" : "Continue the experiment · " + index + "/" + total;
  const columns = chunk.length > 4 ? 3 : 2;
  const links = [
    '<div class="grid grid-cols-' + columns + ' gap-4 mt-6">',
    ...chunk.map(([label, target]) => [
      '<a class="course-link" href="' + escapeHtml(repositoryHref(target)) + '">',
      '<span class="course-link-title">' + escapeHtml(label) + "</span>",
      '<span class="course-link-path">' + escapeHtml(target) + "</span>",
      "</a>"
    ].join("\n")),
    "</div>"
  ].join("\n");
  return slide({}, "# " + title + "\n\n" + links, "Point viewers to the companion paths; do not walk through every extension.");
}

function demoMinutes(lesson) {
  return lesson.experiments.reduce((sum, item) => sum + item.duration, 0);
}

function extensionChunks(lesson) {
  if (lesson.extensions.length <= 6) return [lesson.extensions];
  const split = Math.ceil(lesson.extensions.length / 2);
  return [lesson.extensions.slice(0, split), lesson.extensions.slice(split)];
}

function isDemoHeavy(lesson) {
  return demoMinutes(lesson) >= 5;
}

function movementFor(lesson) {
  if (lesson.number <= 21) return "Build";
  if (lesson.number <= 34) return "Improve";
  return "Expand";
}

function chapterLessonsFor(lesson) {
  return lessons.filter((candidate) => candidate.chapter === lesson.chapter);
}

function isChapterStart(lesson) {
  return chapterLessonsFor(lesson).at(0)?.number === lesson.number;
}

function chapterMap(lesson) {
  const chapterLessons = chapterLessonsFor(lesson);
  return [
    '<div class="course-kicker">' + escapeHtml(movementFor(lesson) + " · " + lesson.chapter + " · " + lesson.part) + "</div>",
    "",
    "# Problems this chapter will solve",
    "",
    cards(chapterLessons.map((candidate) => [
      "Lesson " + String(candidate.number).padStart(2, "0"),
      candidate.title
    ]), ["blue", "green", "purple"])
  ].join("\n");
}

function plannedSlideCount(lesson) {
  const pilotCount = chapter1PilotSlideCount(lesson.number);
  if (pilotCount !== null) return pilotCount;
  const extraExtensionSlides = Math.max(0, extensionChunks(lesson).length - 1);
  const compactedSlides = isDemoHeavy(lesson) ? (isChapterStart(lesson) ? 1 : 2) : 0;
  return 15 + extraExtensionSlides + (lesson.synthesis ? 1 : 0) - compactedSlides;
}

function selectedLessonNumbers() {
  const optionIndex = process.argv.indexOf("--lessons");
  if (optionIndex === -1) return null;
  const value = process.argv[optionIndex + 1];
  if (!value) fail("--lessons requires a comma-separated list such as 2,3");
  const numbers = value.split(",").map((item) => Number(item.trim()));
  if (numbers.some((number) => !Number.isInteger(number) || number < 1 || number > lessons.length)) {
    fail("--lessons values must be integers from 1 to " + lessons.length);
  }
  return new Set(numbers);
}

function lessonDuration(lesson) {
  return plannedSlideCount(lesson) + demoMinutes(lesson);
}

function renderLesson(lesson) {
  const lessonNo = String(lesson.number).padStart(2, "0");
  const deck = [];

  deck.push([
    "---",
    "theme: seriph",
    "title: " + yaml("Lesson " + lessonNo + " — " + lesson.title),
    "info: " + yaml("English video course for AI Agents in Depth"),
    "author: Bojie Li",
    "transition: slide-left",
    "mdc: true",
    "lineNumbers: false",
    "monaco: false",
    "aspectRatio: 16/9",
    "canvasWidth: 980",
    "layout: cover",
    "class: cover",
    "---",
    "",
    '<div class="course-kicker">' + escapeHtml(movementFor(lesson) + " · " + lesson.chapter + " · " + lesson.part) + "</div>",
    "",
    "# " + lesson.title,
    "",
    '<p class="course-subtitle">' + escapeHtml(lesson.subtitle) + "</p>",
    "",
    '<div class="course-cover-meta">Lesson ' + lessonNo + " of 42 · " + lessonDuration(lesson) + " minutes · " + escapeHtml(lesson.book) + "</div>",
    "",
    "<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->",
    ""
  ].join("\n"));

  if (isChapterStart(lesson) && lesson.chapter !== "Introduction") {
    deck.push(slide(
      {},
      chapterMap(lesson),
      "Orient viewers to the chapter. Name the progression, then highlight today's first problem."
    ));
  } else if (!isDemoHeavy(lesson)) {
    deck.push(slide(
      { layout: "center", className: "text-center" },
      '<div class="course-kicker">The central question</div>\n\n<div class="course-big">' + escapeHtml(lesson.question) + "</div>",
      "Let the question sit for a moment, then state the failure mode the lesson will explain."
    ));
  }

  deck.push(slide(
    {},
    "# Why this problem matters\n\n" + cards(lesson.stakes),
    "Connect each card to a product or experiment consequence."
  ));

  deck.push(slide(
    {},
    "# Three ideas to keep in view\n\n" + cards(lesson.concepts, ["purple", "blue", "green"]),
    "Define unfamiliar terms in plain language; the audience is new to ML training and RL."
  ));

  deck.push(slide(
    {},
    "# The book's visual model\n\n" +
      '<img class="course-figure" src="/images/' + escapeHtml(lesson.figure) + '" alt="' + escapeHtml(lesson.figureAlt) + '">\n\n' +
      '<div class="course-caption">' + escapeHtml(lesson.figureAlt) + "</div>",
    "Trace the diagram in one direction and name the mechanism that matters for this lesson."
  ));

  deck.push(slide(
    {},
    "# " + escapeHtml(lesson.contrast.leftTitle) + " vs. " + escapeHtml(lesson.contrast.rightTitle) + "\n\n" +
      '<div class="grid grid-cols-2 gap-6 mt-5">\n' +
      '<div class="course-card orange"><h3>' + escapeHtml(lesson.contrast.leftTitle) + "</h3><ul>" +
      lesson.contrast.left.map((item) => "<li>" + escapeHtml(item) + "</li>").join("") +
      "</ul></div>\n" +
      '<div class="course-card green"><h3>' + escapeHtml(lesson.contrast.rightTitle) + "</h3><ul>" +
      lesson.contrast.right.map((item) => "<li>" + escapeHtml(item) + "</li>").join("") +
      "</ul></div>\n</div>\n\n" +
      '<div class="course-caption course-caption-strong">' + escapeHtml(lesson.contrast.caption) + "</div>",
    "Explain the trade-off; avoid presenting the right column as universally superior."
  ));

  deck.push(slide(
    {},
    "# " + lesson.code.title + "\n\n~~~" + lesson.code.lang + "\n" + lesson.code.lines.join("\n") + "\n~~~",
    "Walk through the executable idea line by line; keep implementation details for the terminal."
  ));

  const experimentCards = lesson.experiments.map((experiment) => [
    '<div class="course-card blue">',
    '<div class="course-demo-head"><span>' + escapeHtml(experiment.id) + "</span><span>" + experiment.duration + " min</span></div>",
    "<h3>" + escapeHtml(experiment.name) + "</h3>",
    '<p><strong>Observe:</strong> ' + escapeHtml(experiment.watch) + "</p>",
    "</div>"
  ].join("\n"));
  deck.push(slide(
    {},
    "# Test the claim\n\n" +
      '<div class="grid grid-cols-' + Math.min(lesson.experiments.length, 3) + ' gap-4 mt-5">\n' + experimentCards.join("\n") + "\n</div>\n\n" +
      (() => {
        const minutes = demoMinutes(lesson);
        return '<div class="course-caption course-caption-strong">Demo budget: ' + minutes + " " + (minutes === 1 ? "minute" : "minutes") + " · one contiguous terminal block</div>";
      })(),
    "State the prediction before running anything. Name the observation that could disconfirm it."
  ));

  const commands = lesson.experiments.map((experiment) => "$ " + experiment.command).join("\n\n");
  deck.push(slide(
    { className: "course-terminal" },
    '<div class="course-kicker">Live demo</div>\n\n# Switching to the terminal\n\n~~~bash\n' + commands + "\n~~~\n\n" +
      '<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>',
    "Switch windows now. Return to the next slide after every listed experiment is complete."
  ));

  deck.push(slide(
    {},
    "# What the evidence supports\n\n" + cards(lesson.findings.map((item, index) => ["Finding " + (index + 1), item]), ["green", "blue", "purple"]),
    "Tie each finding to something viewers just observed; distinguish evidence from interpretation."
  ));

  if (isDemoHeavy(lesson)) {
    deck.push(slide(
      {},
      "# Boundary → design rule\n\n" +
        '<div class="course-boundary">' + escapeHtml(lesson.boundary) + "</div>\n\n" +
        '<div class="course-rule">' + escapeHtml(lesson.rule) + "</div>",
      "State where the evidence stops, then turn that limitation into a reusable engineering rule."
    ));
  } else {
    deck.push(slide(
      { layout: "center" },
      '<div class="course-kicker course-kicker-red">Where the claim stops</div>\n\n# Boundary condition\n\n<div class="course-boundary">' + escapeHtml(lesson.boundary) + "</div>",
      "Say explicitly what this experiment does not establish."
    ));

    deck.push(slide(
      { layout: "center" },
      '<div class="course-kicker">Engineering takeaway</div>\n\n# Design rule\n\n<div class="course-rule">' + escapeHtml(lesson.rule) + "</div>",
      "Present this as a reusable decision rule, then give one counterexample or trade-off."
    ));
  }

  const chunks = extensionChunks(lesson);
  chunks.forEach((chunk, index) => {
    deck.push(extensionSlide(chunk, index + 1, chunks.length));
  });

  if (lesson.synthesis) {
    deck.push(slide(
      {},
      "# The complete course arc\n\n" + cards(lesson.synthesis, ["blue", "green", "purple"]),
      "Return to the three-part arc from Lesson 1 and connect each stage to evidence viewers saw in the course."
    ));
  }

  deck.push(slide(
    { layout: "center", className: "text-center" },
    '<div class="course-kicker">Pause and apply</div>\n\n# Your turn\n\n<div class="course-big course-reflection">' + escapeHtml(lesson.reflection) + "</div>",
    "Invite viewers to pause the video. Offer your own answer after a short beat."
  ));

  const followingLesson = lessons[lesson.number];
  const movementEnds = followingLesson && movementFor(followingLesson) !== movementFor(lesson);
  const chapterEnds = followingLesson && followingLesson.chapter !== lesson.chapter;
  const nextLabel = lesson.number === lessons.length
    ? "Course synthesis"
    : movementEnds
      ? movementFor(lesson) + " complete · Next · Lesson " + String(lesson.number + 1).padStart(2, "0")
      : chapterEnds
        ? lesson.chapter + " complete · Next · Lesson " + String(lesson.number + 1).padStart(2, "0")
        : "Next · Lesson " + String(lesson.number + 1).padStart(2, "0");
  if (lesson.number === lessons.length) {
    deck.push(slide(
      { layout: "center", className: "text-center" },
      '<div class="course-kicker">' + nextLabel + '</div>\n\n' +
        '<div class="course-loop mt-8">\n' +
        '<div class="course-loop-step blue"><span>1</span><strong>Define the failure</strong></div>\n' +
        '<div class="course-loop-arrow">→</div>\n' +
        '<div class="course-loop-step green"><span>2</span><strong>Run a controlled experiment</strong></div>\n' +
        '<div class="course-loop-arrow">→</div>\n' +
        '<div class="course-loop-step purple"><span>3</span><strong>Interpret the evidence</strong></div>\n' +
        '<div class="course-loop-arrow">→</div>\n' +
        '<div class="course-loop-step orange"><span>4</span><strong>Update safely</strong></div>\n' +
        '</div>\n\n' +
        '<div class="course-loop-return">↺ Repeat when new evidence arrives</div>',
      "Close by tracing the evidence-driven loop from Lesson 1, then leave viewers with the repeat trigger."
    ));
  } else {
    deck.push(slide(
      { layout: "center", className: "text-center" },
      '<div class="course-kicker">' + nextLabel + '</div>\n\n<div class="course-next">' + escapeHtml(lesson.next) + '</div>\n\n<div class="course-next-arrow">→</div>',
      "Use this transition to make the course feel continuous rather than episodic."
    ));
  }

  return { markdown: deck.join("\n"), slideCount: deck.length };
}

function validateLesson(lesson, index) {
  const required = [
    "number", "chapter", "part", "title", "subtitle", "book", "figure",
    "figureAlt", "question", "stakes", "concepts", "contrast", "code", "experiments",
    "findings", "boundary", "rule", "extensions", "reflection", "next"
  ];
  for (const field of required) {
    if (lesson[field] === undefined || lesson[field] === null || lesson[field] === "") {
      fail("Lesson " + lesson.number + " is missing " + field);
    }
  }
  if (lesson.number !== index + 1) fail("Lessons must be consecutive at index " + index);
  if (!lesson.title.endsWith("?")) fail("Lesson " + lesson.number + " must have a problem-oriented question title");
  if (lesson.stakes.length !== 3 || lesson.concepts.length !== 3 || lesson.findings.length !== 3) {
    fail("Lesson " + lesson.number + " must have three stakes, concepts, and findings");
  }
  if (lesson.experiments.length < 1 || lesson.experiments.length > 3) {
    fail("Lesson " + lesson.number + " must have one to three experiments");
  }
  for (const experiment of lesson.experiments) {
    for (const field of ["id", "name", "duration", "command", "watch", "mode", "path"]) {
      if (experiment[field] === undefined || experiment[field] === null || experiment[field] === "") {
        fail("Lesson " + lesson.number + " experiment is missing " + field);
      }
    }
    if (experiment.duration < 1 || experiment.duration > 3) {
      fail("Lesson " + lesson.number + " experiment duration must be one to three minutes");
    }
  }
  const target = lessonDuration(lesson);
  if (target < 15 || target > 20) {
    fail("Lesson " + lesson.number + " plans " + target + " minutes; expected 15–20");
  }
  const visible = JSON.stringify({
    title: lesson.title,
    subtitle: lesson.subtitle,
    book: lesson.book,
    figureAlt: lesson.figureAlt,
    question: lesson.question,
    stakes: lesson.stakes,
    concepts: lesson.concepts,
    contrast: lesson.contrast,
    code: lesson.code,
    experiments: lesson.experiments,
    findings: lesson.findings,
    boundary: lesson.boundary,
    rule: lesson.rule,
    extensions: lesson.extensions,
    synthesis: lesson.synthesis,
    reflection: lesson.reflection,
    next: lesson.next
  });
  if (CJK.test(visible)) fail("Lesson " + lesson.number + " contains CJK characters in visible metadata");
  const sourceFigure = path.join(REPO, "book-en", "images", lesson.figure);
  if (!existsSync(sourceFigure)) fail("Missing figure for Lesson " + lesson.number + ": " + lesson.figure);
  for (const [, target] of lesson.extensions) {
    if (!/^(?:https?:|#|mailto:)/.test(target) && !existsSync(path.join(REPO, target))) {
      fail("Lesson " + lesson.number + " links a missing extension: " + target);
    }
  }
  for (const experiment of lesson.experiments) {
    if (!existsSync(path.join(REPO, experiment.path))) {
      fail("Lesson " + lesson.number + " links a missing experiment path: " + experiment.path);
    }
  }
}

function outline() {
  const groups = [];
  for (const lesson of lessons) {
    const current = groups.at(-1);
    if (!current || current.chapter !== lesson.chapter) {
      groups.push({ chapter: lesson.chapter, lessons: [lesson] });
    } else {
      current.lessons.push(lesson);
    }
  }
  const allocationRows = groups.map(({ chapter, lessons: chapterLessons }) => {
    const first = chapterLessons.at(0).number;
    const last = chapterLessons.at(-1).number;
    const range = first === last ? String(first) : first + "–" + last;
    return "| " + chapter + " | " + range + " | " + chapterLessons.length + " |";
  });
  const lessonSections = groups.flatMap(({ chapter, lessons: chapterLessons }) => [
    "### " + chapter,
    "",
    "| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |",
    "| ---: | --- | --- | --- | ---: | ---: | ---: |",
    ...chapterLessons.map((lesson) => {
      const lessonNo = String(lesson.number).padStart(2, "0");
      const demos = lesson.experiments.map((item) => item.id).join(", ");
      return "| [" + lessonNo + "](lesson-" + lessonNo + ".md) | " + lesson.title + " | " + lesson.subtitle + " | " + demos + " | " + plannedSlideCount(lesson) + " | " + demoMinutes(lesson) + " min | " + lessonDuration(lesson) + " min |";
    }),
    ""
  ]);
  return [
    "# AI Agents in Depth — English Video Course",
    "",
    "Approved Option B curriculum: 42 problem-oriented lessons following the English book order. Each lesson is 15–20 minutes, budgeting approximately one minute per Slidev slide plus one to three minutes per live experiment.",
    "",
    "## Learning arc",
    "",
    "| Movement | Chapters | Viewer progression |",
    "| --- | --- | --- |",
    "| Build an Agent | Introduction–Chapter 5 | Context → memory → tools → executable capabilities |",
    "| Improve it scientifically | Chapters 6–8 | Evaluation → post-training → continual evolution |",
    "| Expand it | Chapters 9–10 | Voice → Computer Use → robotics → multi-Agent collaboration |",
    "",
    "## Approved chapter allocation",
    "",
    "| Book section | Lessons | Count |",
    "| --- | ---: | ---: |",
    ...allocationRows,
    "| **Total** | **1–42** | **42** |",
    "",
    "Chapter 7 intentionally receives six lessons because post-training and reinforcement learning are the largest conceptual jump for viewers without prior ML-training knowledge. Chapter 9 receives four lessons so Computer Use and robotics have separate mechanisms, experiments, and safety boundaries.",
    "",
    "## Lesson-by-lesson outline",
    "",
    ...lessonSections,
    "",
    "## Recording contract",
    "",
    "- Speak in your own voice and add interpretation; the decks are visual prompts, not narration scripts.",
    "- Run the listed commands in one contiguous terminal block after the explicit handoff slide.",
    "- Treat preflights, validators, smoke checks, and dry configurations as scoped evidence—not completed long campaigns.",
    "- Use the linked companion projects for experiments that are not demonstrated live.",
    "- Demo-heavy lessons combine or remove conceptual slides so slide time plus terminal time stays within 20 minutes.",
    ""
  ].join("\n");
}

async function main() {
  if (lessons.length !== 42) fail("Expected exactly 42 lessons; found " + lessons.length);
  lessons.forEach(validateLesson);

  const allocation = new Map();
  for (const lesson of lessons) allocation.set(lesson.chapter, (allocation.get(lesson.chapter) || 0) + 1);
  const expectedAllocation = new Map([
    ["Introduction", 1], ["Chapter 1", 3], ["Chapter 2", 5], ["Chapter 3", 4],
    ["Chapter 4", 4], ["Chapter 5", 4], ["Chapter 6", 4], ["Chapter 7", 6],
    ["Chapter 8", 3], ["Chapter 9", 4], ["Chapter 10", 4]
  ]);
  if (JSON.stringify([...allocation]) !== JSON.stringify([...expectedAllocation])) {
    fail("Lesson allocation does not match approved Option B");
  }

  const bookText = (await Promise.all(Array.from({ length: 10 }, (_, index) =>
    readFile(path.join(REPO, "book-en", "chapter" + (index + 1) + ".md"), "utf8")
  ))).join("\n");
  const experimentIds = [...new Set([...bookText.matchAll(/Experiment\s+(\d+-\d+)/g)].map((match) => match[1]))];
  const courseText = JSON.stringify(lessons);
  const missingExperiments = experimentIds.filter((id) => !courseText.includes(id));
  if (missingExperiments.length) fail("Unlinked book experiments: " + missingExperiments.join(", "));

  await mkdir(PUBLIC_IMAGES, { recursive: true });
  const selection = selectedLessonNumbers();
  const targetLessons = selection
    ? lessons.filter((lesson) => selection.has(lesson.number))
    : lessons;
  if (selection && targetLessons.length !== selection.size) fail("Could not resolve every requested lesson");

  const figures = new Set([...lessons.map((lesson) => lesson.figure), ...chapter1PilotFigures]);
  for (const figure of figures) {
    const source = await readFile(path.join(REPO, "book-en", "images", figure), "utf8");
    if (CJK.test(source)) fail("Selected figure contains non-English visible text: " + figure);
  }
  await Promise.all([...figures].map((figure) => copyFile(
    path.join(REPO, "book-en", "images", figure),
    path.join(PUBLIC_IMAGES, figure)
  )));
  if (!selection) {
    const staleFigures = (await readdir(PUBLIC_IMAGES))
      .filter((figure) => figure.endsWith(".svg") && !figures.has(figure))
      .map((figure) => path.join(PUBLIC_IMAGES, figure));
    await Promise.all(staleFigures.map((figure) => rm(figure)));
  }

  const expectedDecks = new Set();
  let totalSlides = 0;
  for (const lesson of targetLessons) {
    const lessonNo = String(lesson.number).padStart(2, "0");
    const name = "lesson-" + lessonNo + ".md";
    expectedDecks.add(name);
    const rendered = renderChapter1Pilot(lesson) ?? renderLesson(lesson);
    if (rendered.slideCount !== plannedSlideCount(lesson)) {
      fail("Lesson " + lesson.number + " rendered " + rendered.slideCount + " slides; planned " + plannedSlideCount(lesson));
    }
    if ((rendered.markdown.match(/Switching to the terminal/g) || []).length !== 1) {
      fail("Lesson " + lesson.number + " must contain exactly one terminal handoff");
    }
    totalSlides += rendered.slideCount;
    await writeFile(path.join(HERE, name), rendered.markdown, "utf8");
  }

  if (!selection) {
    const stale = [];
    for (let number = 43; number <= 99; number += 1) {
      const name = "lesson-" + String(number).padStart(2, "0") + ".md";
      const target = path.join(HERE, name);
      if (existsSync(target) && !expectedDecks.has(name)) stale.push(target);
    }
    await Promise.all(stale.map((target) => rm(target)));
    await writeFile(path.join(HERE, "COURSE_OUTLINE.md"), outline(), "utf8");
  }

  const scope = selection ? targetLessons.length + " selected Slidev decks" : "42 Slidev decks";
  const outlineStatus = selection ? "without changing COURSE_OUTLINE.md" : "with COURSE_OUTLINE.md";
  console.log("Generated " + scope + " (" + totalSlides + " slides), " + outlineStatus + ", and synchronized " + figures.size + " figure assets.");
}

await main();
