import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const slidev = path.join(HERE, "node_modules", ".bin", process.platform === "win32" ? "slidev.cmd" : "slidev");
const requested = process.argv.slice(2).map((value) => Number(value));
const lessonNumbers = requested.length ? requested : Array.from({ length: 42 }, (_, index) => index + 1);

for (const number of lessonNumbers) {
  if (!Number.isInteger(number) || number < 1 || number > 42) {
    throw new Error("Lesson numbers must be integers from 1 to 42");
  }
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: HERE, stdio: "inherit" });
    child.on("error", reject);
    child.on("exit", (code) => code === 0 ? resolve() : reject(new Error("Slidev exited with code " + code)));
  });
}

for (const number of lessonNumbers) {
  const lessonNo = String(number).padStart(2, "0");
  const deck = "lesson-" + lessonNo + ".md";
  const out = "dist/lesson-" + lessonNo;
  console.log("\nBuilding " + deck + "...");
  await run(slidev, ["build", deck, "--out", out, "--base", "/lesson-" + lessonNo + "/"]);
}

console.log("\nBuilt " + lessonNumbers.length + " deck(s).");
