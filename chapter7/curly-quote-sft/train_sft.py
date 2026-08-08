from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent


def load_rows(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def encode(tokenizer, row, max_length):
    messages = [
        {"role": "system", "content": "你是中文技术文档编辑。遵循项目的中文弯引号作用域规范。"},
        {"role": "user", "content": row["prompt"]},
    ]
    prompt_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, enable_thinking=False)
    target_ids = tokenizer(row["target"], add_special_tokens=False).input_ids
    eos = tokenizer.eos_token_id
    ids = (prompt_ids + target_ids + ([eos] if eos is not None else []))[:max_length]
    labels = ([-100] * len(prompt_ids) + target_ids + ([eos] if eos is not None else []))[:max_length]
    return {"input_ids": ids, "labels": labels, "attention_mask": [1] * len(ids)}


class Collator:
    def __init__(self, pad): self.pad = pad
    def __call__(self, batch):
        m = max(len(x["input_ids"]) for x in batch)
        return {
            "input_ids": torch.tensor([x["input_ids"] + [self.pad] * (m - len(x["input_ids"])) for x in batch]),
            "labels": torch.tensor([x["labels"] + [-100] * (m - len(x["labels"])) for x in batch]),
            "attention_mask": torch.tensor([x["attention_mask"] + [0] * (m - len(x["attention_mask"])) for x in batch]),
        }


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-8B")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--max-length", type=int, default=768)
    ap.add_argument("--seed", type=int, default=718)
    ap.add_argument("--output", default=str(ROOT / "output" / "adapter"))
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    if not torch.cuda.is_available(): raise SystemExit("需要 CUDA GPU")
    data_path = ROOT / "data" / "train.jsonl"
    rows = load_rows(data_path)
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token_id is None: tokenizer.pad_token = tokenizer.eos_token
    encoded = [encode(tokenizer, r, args.max_length) for r in rows]
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="auto")
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM", target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]))
    model.print_trainable_parameters()
    loader = torch.utils.data.DataLoader(encoded, batch_size=args.batch_size, shuffle=True, collate_fn=Collator(tokenizer.pad_token_id))
    opt = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr)
    device = next(p for p in model.parameters() if p.requires_grad).device
    model.train(); updates = 0; losses = []
    started = datetime.now(timezone.utc)
    for epoch in range(args.epochs):
        opt.zero_grad(set_to_none=True)
        for step, batch in enumerate(loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            loss = model(**batch).loss / args.grad_accum
            loss.backward()
            if (step + 1) % args.grad_accum == 0 or step == len(loader) - 1:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); opt.zero_grad(set_to_none=True)
                updates += 1; losses.append(float(loss.detach().cpu() * args.grad_accum))
        print(f"epoch={epoch+1}/{args.epochs} loss={sum(losses[-max(1, len(losses)//args.epochs):])/max(1, len(losses)//args.epochs):.4f}", flush=True)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True); model.save_pretrained(out); tokenizer.save_pretrained(out)
    finished = datetime.now(timezone.utc); run = started.strftime("train_%Y%m%dT%H%M%SZ")
    vdir = ROOT / "validation" / run; vdir.mkdir(parents=True, exist_ok=True)
    receipt = {"experiment":"7-18-curly-quote-sft","run":run,"model":args.model,"data_sha256":sha(data_path),"train_examples":len(rows),"config":vars(args),"cuda":torch.cuda.get_device_name(0),"started_at":started.isoformat(),"finished_at":finished.isoformat(),"updates":updates,"final_loss":losses[-1]}
    (vdir / "training_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "validation" / "latest.json").write_text(json.dumps({"run":run,"training_receipt":str((vdir / "training_receipt.json").relative_to(ROOT))}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
