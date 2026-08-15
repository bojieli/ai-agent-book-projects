from __future__ import annotations
import argparse, json
from pathlib import Path
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
def load(path): return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="Qwen/Qwen3-8B"); ap.add_argument("--adapter", default=""); ap.add_argument("--label", default="adapted"); ap.add_argument("--split", default="eval", choices=["eval", "boundary"]); ap.add_argument("--max-new-tokens", type=int, default=256); args = ap.parse_args()
    tok = AutoTokenizer.from_pretrained(args.model, use_fast=True); model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="auto")
    if args.adapter: model = PeftModel.from_pretrained(model, args.adapter)
    model.eval(); out = []
    for row in load(ROOT / "data" / (args.split + ".jsonl")):
        messages = [{"role": "system", "content": "你是工具调用中的精确复制器。只输出要求的字符串或 JSON，不要解释。"}, {"role": "user", "content": row["prompt"]}]
        ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, enable_thinking=False, return_tensors="pt").to(model.device); mask = torch.ones_like(ids)
        with torch.no_grad(): generated = model.generate(ids, attention_mask=mask, max_new_tokens=args.max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id)
        pred = tok.decode(generated[0, ids.shape[-1]:], skip_special_tokens=True).strip(); target = row["target"]
        pb, tb = pred.encode("utf-8"), target.encode("utf-8")
        first = next((i for i, (a, b) in enumerate(zip(pb, tb)) if a != b), min(len(pb), len(tb)))
        out.append({"id": row["id"], "kind": row["kind"], "exact": int(pb == tb), "prediction": pred, "target": target, "first_diff_byte": first})
    summary = {"label": args.label, "split": args.split, "count": len(out), "byte_exact": sum(x["exact"] for x in out) / len(out), "mean_first_diff_byte": sum(x["first_diff_byte"] for x in out) / len(out)}
    (ROOT / "validation" / f"eval_{args.label}_{args.split}.json").write_text(json.dumps({"summary": summary, "rows": out}, ensure_ascii=False, indent=2), encoding="utf-8"); print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
