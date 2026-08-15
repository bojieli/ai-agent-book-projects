#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from voice_library import DEFAULT_LIBRARY_DIR, build_reference_library

load_dotenv(Path(__file__).parent / ".env")

parser = argparse.ArgumentParser(description="Build 24 real Fish Audio S1 reference clips")
parser.add_argument("--base-reference-id", default=os.getenv("FISH_BASE_REFERENCE_ID"))
parser.add_argument("--output-dir", type=Path, default=DEFAULT_LIBRARY_DIR)
args = parser.parse_args()
if not os.getenv("FISH_API_KEY") or not args.base_reference_id:
    parser.error("Set FISH_API_KEY and FISH_BASE_REFERENCE_ID (a voice you are authorized to use)")
manifest = build_reference_library(os.environ["FISH_API_KEY"], args.base_reference_id, args.output_dir)
print(f"Built {len(manifest['profiles'])} Fish S1 reference clips in {args.output_dir}")
