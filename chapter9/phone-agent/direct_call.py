#!/usr/bin/env python3
"""Direct Pine SDK control for comparison with the ReAct path."""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from pineclaw_tool import make_phone_call

load_dotenv(Path(__file__).parent / ".env")
parser = argparse.ArgumentParser(description="Place one direct Pine Voice call (no ReAct planning)")
parser.add_argument("--phone", required=True, help="Authorized test number in E.164 form")
parser.add_argument("--name", required=True)
parser.add_argument("--goal", required=True)
parser.add_argument("--context", default="")
parser.add_argument("--instructions", default="Confirm all task-critical details before ending the call.")
args = parser.parse_args()
record = make_phone_call(
    args.phone, args.goal, args.context, callee_name=args.name, instructions=args.instructions
)
print(json.dumps(record, ensure_ascii=False, indent=2))
