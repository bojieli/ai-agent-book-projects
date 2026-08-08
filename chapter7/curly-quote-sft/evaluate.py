from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent
def rows(path): return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
def protected_segments(target: str) -> list[str]:
    """Return spans whose ASCII syntax must survive the quote edit.

    The data generator varies method names, JSON values and literals, so a
    fixed list of examples would silently under/over-count preservation.  We
    derive the protected spans from the gold target itself: inline-code spans
    and ASCII-quoted spans (JSON, English prose, or source literals).  Chinese
    prose quotes are curly in the target and therefore are intentionally not
    included.
    """
    return re.findall(r"`[^`\n]+`|\"[^\"\n]*\"", target)
def score(pred, target, kind):
    eligible = target.count("“") + target.count("”") + target.count("‘") + target.count("’")
    got = sum(pred.count(c) for c in "“”‘’")
    protected = protected_segments(target)
    protected_ok = sum(x in pred for x in protected)
    return {"exact": int(pred.strip() == target.strip()), "curly_count_target": eligible, "curly_count_pred": got, "protected_ok": protected_ok, "protected_total": len(protected)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--model",default="Qwen/Qwen3-8B"); ap.add_argument("--adapter",default=""); ap.add_argument("--label",default="adapted"); ap.add_argument("--split",default="eval",choices=["eval","boundary"]); ap.add_argument("--max-new-tokens",type=int,default=512); args=ap.parse_args()
    tok=AutoTokenizer.from_pretrained(args.model, use_fast=True)
    model=AutoModelForCausalLM.from_pretrained(args.model,torch_dtype=torch.bfloat16,device_map="auto")
    if args.adapter: model=PeftModel.from_pretrained(model,args.adapter)
    model.eval(); out=[]
    for r in rows(ROOT/"data"/(args.split+".jsonl")):
        msgs=[{"role":"system","content":"你是中文技术文档编辑。请只输出修订后的文本，不要解释。"},{"role":"user","content":r["prompt"]}]
        ids=tok.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True,enable_thinking=False,return_tensors="pt").to(model.device); mask=torch.ones_like(ids)
        with torch.no_grad(): gen=model.generate(ids,attention_mask=mask,max_new_tokens=args.max_new_tokens,do_sample=False,pad_token_id=tok.eos_token_id)
        pred=tok.decode(gen[0,ids.shape[-1]:],skip_special_tokens=True).strip(); s=score(pred,r["target"],r["kind"]); out.append({"id":r["id"],"kind":r["kind"],"prediction":pred,"target":r["target"],**s})
    by_kind={}
    for kind in sorted({x["kind"] for x in out}):
        part=[x for x in out if x["kind"]==kind]
        by_kind[kind]={"count":len(part),"exact":sum(x["exact"] for x in part)/len(part),"curly_count_match":sum(x["curly_count_pred"]==x["curly_count_target"] for x in part)/len(part)}
    summary={"label":args.label,"split":args.split,"count":len(out),"exact":sum(x["exact"] for x in out)/len(out),"protected_preservation":sum(x["protected_ok"] for x in out)/max(1,sum(x["protected_total"] for x in out)),"curly_count_match":sum(x["curly_count_pred"]==x["curly_count_target"] for x in out)/len(out),"by_kind":by_kind}
    run=ROOT/"validation"/f"eval_{args.label}_{args.split}.json"; run.write_text(json.dumps({"summary":summary,"rows":out},ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
