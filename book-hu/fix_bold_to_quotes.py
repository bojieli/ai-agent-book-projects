#! /usr/bin/env python3
"""
Replace short **bold** formatting (used for terminology/keywords) with "quotes"
in Hungarian translated chapters. Longer bold text (statements, formulas) stays bold.

Rules:
- **text** where text is 1-6 words and <= 60 chars → "text"
- Longer **text** stays as **text** (formulas, emphasized statements)
- Tries to avoid table header formatting
"""

import os
import re

book_dir = os.path.dirname(os.path.abspath(__file__))

files = [
    "chapter1.md", "chapter2.md", "chapter3.md", "chapter4.md",
    "chapter5.md", "chapter6.md", "chapter7.md", "chapter8.md",
    "chapter9.md", "chapter10.md", "afterword.md", "reference-answers.md"
]

total_changes = 0

def should_keep_bold(text):
    """Check if bold text should stay bold (statement, formula, table header, etc.)"""
    stripped = text.strip()
    # Table headers with pipe
    if '|' in stripped:
        return True
    # Long text (multi-word statements)
    words = stripped.split()
    if len(words) > 6:
        return True
    if len(stripped) > 60:
        return True
    # Contains formula operators
    if '=' in stripped or '+' in stripped or '→' in stripped:
        return True
    # Contains list markers
    if stripped.startswith('- ') or stripped.startswith('* '):
        return True
    # Numbered items
    if re.match(r'^\d+\.', stripped):
        return True
    return False

def process_file(filepath, filename):
    global total_changes
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: **text** - match inline bold
    def replace_bold(match):
        inner = match.group(1)
        if should_keep_bold(inner):
            return f'**{inner}**'
        else:
            return f'"{inner}"'

    new_content = re.sub(r'\*\*(.+?)\*\*', replace_bold, content)

    if new_content != content:
        # Count changes
        old_count = len(re.findall(r'\*\*(.+?)\*\*', content))
        new_count = len(re.findall(r'\*\*(.+?)\*\*', new_content))
        changes = old_count - new_count
        total_changes += changes

        # Count quote uses
        quote_count = len(re.findall(r'"([^"]*?)"', new_content)) - len(re.findall(r'"([^"]*?)"', content))

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ {filename}: {changes} bold → quote (now {quote_count} new quote pairs)")
        return True
    else:
        print(f"⏭️  {filename}: no changes")
        return False

print("=== Félkövér → Idézőjel csere ===\n")

for fname in files:
    fpath = os.path.join(book_dir, fname)
    if os.path.exists(fpath):
        process_file(fpath, fname)
    else:
        print(f"⚠️  {fname}: nincs meg")

print(f"\n✅ Összesen {total_changes} darab ** → \" csere")
