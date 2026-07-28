#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成/校验「骑士与无赖」(Knights and Knaves)谜题，并导出 puzzles.json。

每道谜题的每句话都用 csp_solver.py 里的结构化 DSL 表示(见该文件顶部说明)，
既能渲染成中文题面(给 LLM 看)，也能直接翻译成 python-constraint 约束来求解。
本脚本用 python-constraint 校验每题「解唯一」后才写出——这确保真值解无歧义，
同时演示了实验 5-2 的核心：把谜题形式化为 CSP 并用求解器离线求解。

约定：骑士(knight)永远说真话，无赖(knave)永远说假话。t[name]=True 表示骑士。

用法：
    python build_puzzles.py                       # 导出内置的 12 道精选谜题(默认)
    python build_puzzles.py --generate 20         # 随机生成 20 道解唯一的谜题
    python build_puzzles.py --generate 20 --min-people 3 --max-people 5 --seed 7
    python build_puzzles.py --output my.json      # 指定输出文件
"""
import argparse
import json
import random

from csp_solver import render_nl, solve, solve_labeled

# 每题：id, 名字列表, dict{name: 结构化陈述}。中文题面由结构化陈述自动渲染，
# 但精选题保留手写的更自然的中文(见 STATEMENTS_NL 覆盖)。
CURATED = [
    ("kk01", ["A", "B"], {
        "A": ["is", "B", "knave"],
        "B": ["and", ["is", "A", "knave"], ["is", "B", "knave"]]}),
    ("kk02", ["A", "B"], {
        "A": ["same", "A", "B"],
        "B": ["diff", "A", "B"]}),
    ("kk03", ["A", "B"], {
        "A": ["count", "knight", ">=", 1],
        "B": ["is", "A", "knave"]}),
    ("kk04", ["A", "B", "C"], {
        "A": ["is", "B", "knave"],
        "B": ["is", "C", "knave"],
        "C": ["and", ["is", "A", "knave"], ["is", "B", "knave"]]}),
    ("kk05", ["A", "B", "C"], {
        "A": ["is", "B", "knight"],
        "B": ["is", "C", "knave"],
        "C": ["same", "A", "B"]}),
    ("kk06", ["A", "B", "C"], {
        "A": ["same", "B", "C"],
        "B": ["is", "A", "knave"],
        "C": ["same", "C", "A"]}),
    ("kk07", ["A", "B", "C"], {
        "A": ["or", ["is", "A", "knave"], ["is", "B", "knight"]],
        "B": ["is", "A", "knight"],
        "C": ["is", "B", "knave"]}),
    ("kk08", ["A", "B", "C", "D"], {
        "A": ["same", "B", "D"],
        "B": ["is", "C", "knave"],
        "C": ["is", "D", "knight"],
        "D": ["diff", "B", "C"]}),
    ("kk09", ["A", "B", "C", "D"], {
        "A": ["is", "B", "knight"],
        "B": ["is", "C", "knave"],
        "C": ["is", "D", "knight"],
        "D": ["diff", "A", "B"]}),
    ("kk10", ["A", "B", "C", "D"], {
        "A": ["count", "knave", ">=", 3],
        "B": ["is", "A", "knave"],
        "C": ["is", "B", "knight"],
        "D": ["is", "C", "knave"]}),
    ("kk11", ["A", "B", "C", "D", "E"], {
        "A": ["is", "B", "knight"],
        "B": ["is", "C", "knave"],
        "C": ["is", "D", "knight"],
        "D": ["is", "E", "knave"],
        "E": ["count", "knight", ">=", 2]}),
    ("kk12", ["A", "B", "C", "D", "E"], {
        "A": ["is", "B", "knight"],
        "B": ["is", "C", "knave"],
        "C": ["is", "D", "knave"],
        "D": ["is", "E", "knight"],
        "E": ["same", "A", "C"]}),
]

# 精选题的手写中文题面(比自动渲染更自然)。未覆盖的句子回退到 render_nl。
STATEMENTS_NL = {
    ("kk01", "B"): "我们两人都不是骑士。",
    ("kk02", "A"): "我和 B 是同一类人（要么都是骑士，要么都是无赖）。",
    ("kk02", "B"): "我和 A 是不同类人。",
    ("kk03", "A"): "我们当中至少有一个骑士。",
    ("kk04", "C"): "A 和 B 都是无赖。",
    ("kk06", "C"): "我和 A 是同一类人。",
    ("kk07", "A"): "我是无赖，或者 B 是骑士。",
    ("kk09", "D"): "A 和 B 不是同一类人。",
    ("kk10", "A"): "我们四人当中至少有三个无赖。",
    ("kk11", "E"): "我们五人当中至少有两个骑士。",
    ("kk12", "E"): "A 和 C 是同一类人。",
}


def build_puzzle(pid, names, structs, nl_overrides=None):
    """求解校验(要求解唯一)并组装成写入 puzzles.json 的一条记录。"""
    sols = solve_labeled(names, structs)
    if len(sols) != 1:
        raise ValueError(f"{pid} 解不唯一: {len(sols)} 个解 -> {sols}")
    solution = sols[0]

    nl_overrides = nl_overrides or {}
    statements = {n: nl_overrides.get(n, render_nl(structs[n])) for n in names}
    lines = [f"{n}: 「{statements[n]}」" for n in names]
    desc = (
        f"这座岛上有 {len(names)} 位居民：{', '.join(names)}。"
        "每位居民要么是永远说真话的骑士(knight)，要么是永远说假话的无赖(knave)。"
        "他们各自说了如下的话：\n" + "\n".join(lines)
    )
    return dict(id=pid, num_people=len(names), names=names,
                statements=statements, statements_struct=structs,
                description=desc, solution=solution)


# ---------------- 随机生成器 ----------------
def _random_stmt(speaker, names, rng):
    """为 speaker 随机生成一句合法的结构化陈述。"""
    others = [n for n in names if n != speaker]
    # Solo resident: only count statements are valid (no "others" to name).
    if not others:
        role = rng.choice(["knight", "knave"])
        op = rng.choice([">=", "<=", "=="])
        return ["count", role, op, rng.randint(1, len(names))]
    kind = rng.choice(["is", "is", "same", "diff", "count"])
    if kind == "is":
        return ["is", rng.choice(others), rng.choice(["knight", "knave"])]
    if kind == "same":
        return ["same", speaker, rng.choice(others)]
    if kind == "diff":
        return ["diff", speaker, rng.choice(others)]
    # count：全体中某角色的人数满足某比较
    role = rng.choice(["knight", "knave"])
    op = rng.choice([">=", "<=", "=="])
    k = rng.randint(1, len(names))
    return ["count", role, op, k]


def generate(count, min_people, max_people, seed):
    """随机生成 count 道「解唯一」的谜题(用 python-constraint 过滤)。"""
    rng = random.Random(seed)
    names_pool = ["A", "B", "C", "D", "E", "F", "G"]
    puzzles = []
    attempts = 0
    while len(puzzles) < count and attempts < count * 2000:
        attempts += 1
        n = rng.randint(min_people, max_people)
        names = names_pool[:n]
        structs = {sp: _random_stmt(sp, names, rng) for sp in names}
        if len(solve(names, structs)) != 1:      # 只保留解唯一的谜题
            continue
        pid = f"gen{len(puzzles) + 1:03d}"
        puzzles.append(build_puzzle(pid, names, structs))
    if len(puzzles) < count:
        print(f"警告：{attempts} 次尝试只生成了 {len(puzzles)}/{count} 道解唯一的谜题。")
    return puzzles


def build_curated():
    out = []
    for pid, names, structs in CURATED:
        nl = {n: STATEMENTS_NL[(pid, n)]
              for n in names if (pid, n) in STATEMENTS_NL}
        out.append(build_puzzle(pid, names, structs, nl))
    return out


def main():
    ap = argparse.ArgumentParser(
        description="生成/校验骑士与无赖谜题并导出 puzzles.json"
                    "（用 python-constraint 离线求解，校验每题解唯一）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument("--generate", type=int, metavar="N", default=0,
                    help="随机生成 N 道解唯一的谜题(默认 0=导出内置 12 道精选题)")
    ap.add_argument("--min-people", type=int, default=2,
                    help="随机生成时每题最少居民数(默认 2)")
    ap.add_argument("--max-people", type=int, default=5,
                    help="随机生成时每题最多居民数(难度上限，默认 5)")
    ap.add_argument("--seed", type=int, default=42,
                    help="随机种子，保证可复现(默认 42)")
    ap.add_argument("--output", default="puzzles.json",
                    help="输出文件路径(默认 puzzles.json)")
    args = ap.parse_args()

    if args.generate > 0:
        print(f"随机生成 {args.generate} 道谜题"
              f"({args.min_people}~{args.max_people} 人，seed={args.seed})...")
        out = generate(args.generate, args.min_people, args.max_people, args.seed)
    else:
        out = build_curated()

    for p in out:
        print(f"{p['id']}: OK 唯一解 = {p['solution']}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n已写出 {len(out)} 题到 {args.output}")


if __name__ == "__main__":
    main()
