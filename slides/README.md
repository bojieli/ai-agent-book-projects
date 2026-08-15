# AI Agents in Depth — English Slidev Course

This directory contains the 42-lesson English video course derived from the
English edition of the book.

The approved curriculum is documented in [COURSE_OUTLINE.md](COURSE_OUTLINE.md).
It uses the Option B allocation: four Chapter 5 lessons and four Chapter 9
lessons, with Computer Use and robotics taught separately. Chapter 7 retains
six lessons so post-training and reinforcement learning can be introduced
without assuming prior ML-training knowledge. Lesson 42 concludes both Chapter
10 and the complete series.

## Production rules

- Each lesson is 15–20 minutes.
- The author budgets roughly one minute per slide.
- The generator derives each displayed lesson duration from the rendered slide
  count plus the live-demo budget; it rejects any lesson outside 15–20 minutes.
- Decks are intentionally sparse: one claim, comparison, figure, or short code
  excerpt per slide.
- Every live-demo lesson contains a dark “Switching to the terminal” handoff
  slide before the author changes windows.
- Live terminal demonstrations are budgeted at one to three minutes each.
- Several short experiments may share one contiguous demo block.
- Lessons with five or six minutes of demos automatically use a compact
  13–14-slide structure instead of squeezing the terminal work past 20 minutes.
- Long-running, external-service, GPU, telephony, or hardware experiments use
  traceable artifacts or preflight commands and never imply unperformed work.
- The decks contain slide content and brief presenter cues, not narration
  scripts. The author supplies the interpretation in his own voice.
- All visible slide content is English.

## Visual language

The style follows the author’s existing Slidev talks under
~/ring0.me/public/files: Seriph, problem-led titles, two- and three-column
cards, section dividers, code, architecture diagrams, and restrained accent
colors. This course uses larger type and more whitespace than the older talks.

## Generate and run

From this directory:

1. Run npm install.
2. Run npm run generate.
3. Run npm run dev -- lesson-01.md.

The generator also creates COURSE_OUTLINE.md and copies the selected English
book figures into public/images.

## Build and export

- Build selected lessons: `node build-all.mjs 1 23 42`
- Build every lesson: `npm run build:all`
- Export one deck to PDF: `npm run export -- lesson-01.md --output lesson-01.pdf`
- Export selected slides to PNG: `npm run export -- lesson-01.md --format png --range 1,8-10`

The generated course outline lists every lesson, target duration, live
experiment, and terminal-demo budget. Regenerate the decks after changing
course.mjs; generated lesson files should not be edited by hand.
