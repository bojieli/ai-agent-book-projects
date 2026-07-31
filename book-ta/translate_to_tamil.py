#!/usr/bin/env python3
"""Translate the English book text in this repository into Tamil.

Adapted from ``translate_repo.py`` (the Chinese->English pass). Differences:

* Direction            - English -> Tamil (தமிழ்).
* Non-destructive       - the English sources are never modified. Each source
  ``foo.md`` is written to a sibling ``foo.ta.md``.
* Scoped by default     - only the book Markdown (``book/*.md``) is translated
  unless ``--include`` globs are given. Generated ``*.ta.md`` files are always
  excluded so re-runs never translate a translation.

Everything else mirrors the original: structure-preserving (code, identifiers,
Markdown/LaTeX/JSON syntax, URLs, paths and whitespace are copied verbatim),
resumable (a JSON state file records the source hash of each finished file), and
concurrent (a thread pool issues API calls in parallel). The API key is read
from the environment and is never written to disk.

Usage
-----
    export DEEPSEEK_API_KEY=your-deepseek-api-key
    python translate_to_tamil.py --list          # show what would be translated
    python translate_to_tamil.py --limit 1       # translate one file first
    python translate_to_tamil.py                  # translate the whole book

Run ``python translate_to_tamil.py --help`` for all options.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # import only for type hints; not required for --list/--dry-run
    from openai import OpenAI

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Presence of at least one ASCII letter marks a fragment as worth translating.
# Fragments that are pure whitespace/numbers/symbols are copied verbatim.
LETTER_RE = re.compile(r"[A-Za-z]")

# Marks already-generated Tamil outputs like ``chapter1.ta.md`` so we never
# translate a translation.
TAMIL_OUT_RE = re.compile(r"\.ta\.[^.]+$")

# File extensions we never translate (binary / data / vendored artefacts).
SKIP_EXTS = {
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4a", ".mp3", ".wav", ".flac",
    ".ogg", ".aac", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".tiff", ".psd",
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".onnx", ".parquet", ".tiktoken", ".bin", ".pt", ".pth", ".safetensors",
    ".npy", ".npz", ".h5", ".hdf5", ".pkl", ".pickle", ".model", ".arrow",
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".class", ".o", ".a", ".lock",
    ".min.js", ".min.css", ".map",
}

SKIP_NAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Cargo.lock", "uv.lock", "composer.lock", "Gemfile.lock",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", ".next", ".turbo", ".cache",
    ".idea", ".vscode", "site-packages",
}

TYPE_HINTS = {
    ".md": "Markdown documentation",
    ".mdx": "MDX documentation (Markdown + JSX)",
    ".py": "Python source code",
    ".ts": "TypeScript source code",
    ".tsx": "TypeScript React (TSX) source code",
    ".js": "JavaScript source code",
    ".jsx": "JavaScript React (JSX) source code",
    ".svg": "SVG vector image (translate ONLY the visible text inside <text>/<tspan>/<title> and human-facing attributes)",
    ".json": "JSON data (translate ONLY human-readable string values; keep object keys and identifier-like values unchanged)",
    ".jsonl": "JSON Lines data (translate ONLY human-readable string values; keep keys unchanged)",
    ".yaml": "YAML config (translate ONLY comments and human-readable string values; keep keys unchanged)",
    ".yml": "YAML config (translate ONLY comments and human-readable string values; keep keys unchanged)",
    ".toml": "TOML config (translate ONLY comments and human-readable string values; keep keys unchanged)",
    ".ini": "INI config (translate ONLY comments and human-readable values; keep keys unchanged)",
    ".html": "HTML (translate ONLY visible text and human-facing attributes such as title/alt/placeholder)",
    ".htm": "HTML (translate ONLY visible text and human-facing attributes such as title/alt/placeholder)",
    ".xml": "XML (translate ONLY visible text content and human-facing attribute values)",
    ".sql": "SQL (translate ONLY comments and human-facing string literals; keep identifiers)",
    ".sh": "Shell script (translate ONLY comments and human-facing echoed strings)",
    ".tex": "LaTeX (translate prose; keep commands, math, labels and references)",
    ".lua": "Lua source code",
    ".css": "CSS stylesheet (translate ONLY comments and content strings)",
    ".less": "LESS stylesheet (translate ONLY comments and content strings)",
    ".txt": "plain text",
}

SYSTEM_PROMPT = """\
You are a professional book-localization engine. You translate English technical \
prose into clear, natural, fluent Tamil (தமிழ்) for a professional \
software-engineering book about AI agents.

You are given the contents (or a fragment) of a source file. The file type is: {filetype}.

TRANSLATE
- All English natural-language text: prose, headings, list items, table cells,
  block quotes, figure/image captions and alt text, footnote bodies, and
  human-facing string literals or comments inside code blocks.
- Produce fluent, idiomatic Tamil (meaning-for-meaning, not word-for-word),
  written for a technical reader in a precise, professional tone.
- CRITICAL — NEVER transliterate English technical terms, concept keywords, or
  proper nouns into Tamil script. Keep them VERBATIM in Latin (English) script,
  exactly as written in the source. Transliteration (spelling an English word
  using Tamil letters) is forbidden. This applies to, among others: agent,
  model, context, tool/tools, prompt, token, embedding, attention, transformer,
  workflow, harness, pipeline, fine-tuning, reinforcement learning, and all
  abbreviations / product / company names (LLM, RAG, API, KV Cache, SFT, RL,
  ReAct, GPT, Claude, Cursor, OpenAI, ...). Translate ONLY the genuine Tamil
  grammatical/connective words around them.
  Worked example: "Model as Agent" MUST become "Model ஆக Agent" — translate
  only "as" → "ஆக" and keep "Model" and "Agent" in English. It is WRONG to
  write "மாடல் ஆக ஏஜென்ட்" or "மாடல்" or "ஏஜென்ட்".
- Do not invent obscure Tamil neologisms for technical concepts; if the natural
  Tamil word is uncommon or ambiguous, keep the English term instead.
- Keep terminology consistent throughout the file.

DO NOT CHANGE (copy verbatim, byte for byte)
- Code structure, syntax, indentation and ALL whitespace. Never reflow or reindent.
- Programming identifiers: variable/function/class/module names, keywords, decorators.
- Import paths, file paths, URLs, environment-variable names, CLI flags, hashes, IDs.
- Markdown/HTML/XML/JSON/YAML structure and syntax; translate ONLY the human text.
  Keep heading markers (#), list markers, table pipes, emphasis markers, and the
  link/image syntax intact (translate the visible text or caption, but keep the
  URL/path). Keep footnote reference labels such as [^name] unchanged (translate
  only the note body). Keep Markdown attribute blocks like {{.unnumbered}} as-is.
- Code fences and the code inside them, EXCEPT translate comments and
  human-facing strings within that code. Keep all code identifiers in English.
- LaTeX and math ($...$, $$...$$), numbers, dates, and content already written in
  a non-English script.

OUTPUT RULES (critical)
- Output ONLY the translated file content. No preamble, no explanation, no notes.
- Do NOT wrap the whole output in a Markdown code fence.
- Preserve the exact leading and trailing whitespace, including the final newline.
- The output must be structurally identical to the input, with English prose replaced by Tamil.\
"""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()


def is_secret_file(name: str) -> bool:
    if name == ".env":
        return True
    if name.startswith(".env.") and not name.endswith(
        (".example", ".template", ".sample")
    ):
        return True
    return False


def has_source_text(text: str) -> bool:
    """True if the fragment contains English text worth translating."""
    return LETTER_RE.search(text) is not None


def type_hint(path: Path) -> str:
    return TYPE_HINTS.get(path.suffix.lower(), "plain text / config")


def tamil_out_path(path: Path) -> Path:
    """``book/afterword.md`` -> ``book/afterword.ta.md``."""
    return path.parent / f"{path.stem}.ta{path.suffix}"


def read_text(path: Path) -> Optional[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def split_budget(text: str, budget: int) -> list[str]:
    """Split text into fragments <= ``budget`` chars on line boundaries."""
    lines = text.splitlines(keepends=True)
    parts: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for ln in lines:
        if cur and cur_len + len(ln) > budget:
            parts.append("".join(cur))
            cur, cur_len = [], 0
        cur.append(ln)
        cur_len += len(ln)
    if cur:
        parts.append("".join(cur))
    return parts or [text]


# A fenced code block opens with >=3 backticks or tildes (optionally indented)
# and closes with a line of only that fence character (>= the opening length).
FENCE_OPEN_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def split_prose_code(text: str) -> list[tuple[str, str]]:
    """Split markdown into ('prose'|'code', segment) parts on fenced code blocks.

    Concatenating the segments reproduces ``text`` exactly. Fenced code blocks
    (the fence lines and everything between them) are isolated as 'code' so the
    caller can pass them through untranslated -- translating inside code fences
    is what corrupts fence structure (the model reflows fences, bolds lines,
    merges markers), so we never send code to the model.
    """
    lines = text.splitlines(keepends=True)
    out: list[tuple[str, str]] = []
    prose: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = FENCE_OPEN_RE.match(lines[i])
        if m:
            fence = m.group(1)
            fchar, flen = fence[0], len(fence)
            if prose:
                out.append(("prose", "".join(prose)))
                prose = []
            code = [lines[i]]
            i += 1
            while i < n:
                code.append(lines[i])
                s = lines[i].strip()
                if s and all(c == fchar for c in s) and len(s) >= flen:
                    i += 1
                    break
                i += 1
            out.append(("code", "".join(code)))
        else:
            prose.append(lines[i])
            i += 1
    if prose:
        out.append(("prose", "".join(prose)))
    return out


def strip_wrapping_fence(src: str, out: str) -> str:
    """Remove a Markdown code fence the model may have wrapped the output in."""
    if src.lstrip().startswith("```"):
        return out
    stripped = out.strip()
    if stripped.startswith("```") and stripped.endswith("```") and len(stripped) > 6:
        nl = stripped.find("\n")
        if nl != -1:
            inner = stripped[nl + 1:]
            last = inner.rfind("```")
            if last != -1:
                return inner[:last].rstrip("\n")
    return out


def match_globs(rel: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, g) for g in globs)


# --------------------------------------------------------------------------- #
# Translator
# --------------------------------------------------------------------------- #

@dataclass
class Translator:
    client: OpenAI
    model: str
    temperature: float = 0.2
    max_output_tokens: int = 8192
    max_chars: int = 3000
    max_retries: int = 5
    min_chunk: int = 400

    def _call(self, system: str, user: str) -> tuple[str, str]:
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_output_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                choice = resp.choices[0]
                content = choice.message.content or ""
                if not content.strip():
                    raise RuntimeError("empty response from model")
                return content, (choice.finish_reason or "stop")
            except Exception as exc:  # noqa: BLE001 - surface after retries
                last_err = exc
                time.sleep(min(2 ** attempt, 30))
        raise RuntimeError(f"API call failed after {self.max_retries} retries: {last_err}")

    def _fragment(self, text: str, filetype: str, depth: int = 0) -> str:
        if not has_source_text(text):
            return text
        system = SYSTEM_PROMPT.format(filetype=filetype)
        content, finish = self._call(system, text)
        if finish == "length" and depth < 6 and len(text) > self.min_chunk:
            parts = split_budget(text, max(len(text) // 2, self.min_chunk))
            if len(parts) > 1:
                return "".join(self._fragment(p, filetype, depth + 1) for p in parts)
            mid = len(text) // 2
            return self._fragment(text[:mid], filetype, depth + 1) + self._fragment(
                text[mid:], filetype, depth + 1
            )
        return strip_wrapping_fence(text, content)

    def translate(self, text: str, filetype: str) -> tuple[str, int]:
        """Translate a file, passing fenced code blocks through verbatim.

        Only prose segments are sent to the model; fenced code blocks (fences +
        contents) are copied unchanged, so the Tamil output keeps byte-identical
        code-fence structure to the English source. Returns (new_text, chunks).

        The model often drops the leading/trailing newlines of a fragment. If
        left uncorrected, the trailing newline before a code block is lost and
        the block's opening ``` glues onto the previous prose line, breaking the
        fence. So for every translated fragment we restore the EXACT leading and
        trailing newline count of its source, guaranteeing fences and block
        boundaries always start on their own line.
        """
        out_parts: list[str] = []
        chunks = 0
        for kind, seg in split_prose_code(text):
            if kind == "code" or not has_source_text(seg):
                out_parts.append(seg)  # code fences / blank gaps: verbatim
                continue
            parts = [seg] if len(seg) <= self.max_chars else split_budget(seg, self.max_chars)
            for p in parts:
                if not has_source_text(p):
                    out_parts.append(p)
                    continue
                tp = self._fragment(p, filetype)
                lead = len(p) - len(p.lstrip("\n"))
                trail = len(p) - len(p.rstrip("\n"))
                out_parts.append(("\n" * lead) + tp.strip("\n") + ("\n" * trail))
                chunks += 1
        out = "".join(out_parts)
        if text.endswith("\n") and not out.endswith("\n"):
            out += "\n"
        elif not text.endswith("\n") and out.endswith("\n"):
            out = out.rstrip("\n")
        return out, chunks


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #

class State:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self._dirty = 0
        self.data: dict = {"version": 1, "files": {}}
        if path.exists():
            try:
                self.data = json.loads(path.read_text("utf-8"))
                self.data.setdefault("files", {})
            except (OSError, json.JSONDecodeError):
                pass

    def source_hash(self, rel: str) -> Optional[str]:
        entry = self.data["files"].get(rel)
        return entry.get("source_sha") if entry else None

    def record(self, rel: str, **fields) -> None:
        with self.lock:
            self.data["files"][rel] = {"ts": int(time.time()), **fields}
            self._dirty += 1
            if self._dirty >= 8:
                self._flush_locked()

    def flush(self) -> None:
        with self.lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        self._dirty = 0
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(self.path)


# --------------------------------------------------------------------------- #
# File discovery
# --------------------------------------------------------------------------- #

def git_files(root: Path) -> Optional[list[Path]]:
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [root / n.decode("utf-8") for n in res.stdout.split(b"\x00") if n]


def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            out.append(Path(dirpath) / f)
    return out


def is_candidate(path: Path, self_path: Path, state_path: Path) -> bool:
    if not path.is_file():
        return False
    if path in (self_path, state_path):
        return False
    name = path.name
    if name in SKIP_NAMES or is_secret_file(name):
        return False
    if TAMIL_OUT_RE.search(name):  # never translate a translation
        return False
    if path.suffix.lower() in SKIP_EXTS or name.endswith((".min.js", ".min.css")):
        return False
    if any(part in SKIP_DIRS or part.startswith(".venv") for part in path.parts):
        return False
    return True


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def build_client(args) -> "OpenAI":
    try:
        from openai import OpenAI
    except ImportError:  # pragma: no cover
        sys.exit("The 'openai' package is required to translate. "
                 "Install with: pip install openai")
    api_key = (
        args.api_key
        or os.environ.get("TRANSLATE_API_KEY")
        or os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    if not api_key:
        sys.exit(
            "No API key found. Set DEEPSEEK_API_KEY (or TRANSLATE_API_KEY / "
            "OPENAI_API_KEY) in the environment, or pass --api-key."
        )
    base_url = (
        args.base_url
        or os.environ.get("TRANSLATE_BASE_URL")
        or os.environ.get("DEEPSEEK_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or "https://api.deepseek.com"
    )
    return OpenAI(api_key=api_key, base_url=base_url, timeout=180.0, max_retries=0)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Translate the English book text into Tamil (writes *.ta.md).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parent,
                   help="Repository root to translate.")
    p.add_argument("--model", default=os.environ.get("TRANSLATE_MODEL")
                   or os.environ.get("DEEPSEEK_MODEL")
                   or os.environ.get("OPENAI_MODEL") or "deepseek-chat",
                   help="Chat model name.")
    p.add_argument("--base-url", default=None, help="OpenAI-compatible base URL.")
    p.add_argument("--api-key", default=None,
                   help="API key (prefer the environment variable instead).")
    p.add_argument("--workers", type=int, default=6, help="Parallel API workers.")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--max-chars", type=int, default=3000,
                   help="Max characters per API request before splitting.")
    p.add_argument("--max-output-tokens", type=int, default=8192)
    p.add_argument("--max-file-bytes", type=int, default=2_000_000,
                   help="Skip files larger than this.")
    p.add_argument("--include", action="append", default=[],
                   help="Only translate paths matching this glob (repeatable). "
                        "Default: book/*.md")
    p.add_argument("--exclude", action="append", default=[],
                   help="Skip paths matching this glob (repeatable).")
    p.add_argument("--limit", type=int, default=0, help="Translate at most N files.")
    p.add_argument("--all-files", action="store_true",
                   help="Walk the filesystem instead of using 'git ls-files'.")
    p.add_argument("--force", action="store_true",
                   help="Re-translate even files already recorded as done.")
    p.add_argument("--state-file", type=Path, default=None,
                   help="Path to the resume-state JSON file.")
    p.add_argument("--list", action="store_true",
                   help="List candidate files and exit (no API calls).")
    p.add_argument("--dry-run", action="store_true", help="Alias for --list.")
    return p.parse_args(argv)


def collect_candidates(args, self_path: Path, state_path: Path):
    root: Path = args.root.resolve()
    include = args.include or ["book/*.md"]
    exclude = list(args.exclude) + ["*.ta.md"]

    raw = None if args.all_files else git_files(root)
    if raw is None:
        raw = walk_files(root)
    candidates = []
    for path in raw:
        path = path.resolve()
        if not is_candidate(path, self_path, state_path):
            continue
        rel = os.path.relpath(path, root)
        if not match_globs(rel, include):
            continue
        if match_globs(rel, exclude):
            continue
        try:
            if path.stat().st_size > args.max_file_bytes:
                continue
        except OSError:
            continue
        text = read_text(path)
        if text is None or not has_source_text(text):
            continue
        candidates.append((path, rel, text))
    return root, candidates


def main(argv=None) -> int:
    args = parse_args(argv)
    self_path = Path(__file__).resolve()
    root = args.root.resolve()
    state_path = (args.state_file or (root / ".translate_tamil_state.json")).resolve()

    print(f"Scanning {root} ...", flush=True)
    root, candidates = collect_candidates(args, self_path, state_path)

    state = State(state_path)
    if not args.force:
        pending = []
        for path, rel, text in candidates:
            out_path = tamil_out_path(path)
            if state.source_hash(rel) == sha256(text) and out_path.exists():
                continue  # already translated by us and unchanged
            pending.append((path, rel, text))
    else:
        pending = candidates

    total_bytes = sum(len(t.encode("utf-8")) for _, _, t in pending)
    print(f"Candidate source files: {len(candidates)}")
    print(f"Pending (not yet done):  {len(pending)}  "
          f"(~{total_bytes/1_000_000:.2f} MB of text)")

    if args.limit:
        pending = pending[: args.limit]
        print(f"Limited to first {len(pending)} file(s).")

    if args.list or args.dry_run:
        for path, rel, _ in pending:
            print(f"  {rel}  ->  {os.path.relpath(tamil_out_path(path), root)}")
        print(f"\n[list] {len(pending)} file(s) would be translated. No API calls made.")
        return 0

    if not pending:
        print("Nothing to do - everything is already translated.")
        return 0

    client = build_client(args)
    translator = Translator(
        client=client, model=args.model, temperature=args.temperature,
        max_output_tokens=args.max_output_tokens, max_chars=args.max_chars,
    )
    print(f"Model: {args.model}   Workers: {args.workers}\n")

    counter = {"done": 0, "failed": 0}
    clock = threading.Lock()
    n = len(pending)

    def work(item):
        path, rel, text = item
        out_path = tamil_out_path(path)
        t0 = time.time()
        try:
            new_text, chunks = translator.translate(text, type_hint(path))
        except Exception as exc:  # noqa: BLE001
            state.record(rel, status="error", error=str(exc)[:300])
            with clock:
                counter["failed"] += 1
                i = counter["done"] + counter["failed"]
                print(f"[{i:>4}/{n}] FAIL {rel}\n         {exc}", flush=True)
            return
        out_path.write_text(new_text, "utf-8")
        state.record(rel, status="done", out=os.path.relpath(out_path, root),
                     source_sha=sha256(text), result_sha=sha256(new_text))
        with clock:
            counter["done"] += 1
            i = counter["done"] + counter["failed"]
            print(f"[{i:>4}/{n}] OK  {rel}  "
                  f"(chunks={chunks}, {time.time()-t0:.1f}s)", flush=True)

    try:
        with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(work, pending))
    except KeyboardInterrupt:
        print("\nInterrupted - progress saved to state file; re-run to resume.")
    finally:
        state.flush()

    print(f"\nDone. translated={counter['done']} "
          f"failed={counter['failed']}  state={state_path.name}")
    return 1 if counter["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
