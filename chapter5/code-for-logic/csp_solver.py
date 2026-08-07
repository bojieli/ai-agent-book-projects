"""
离线约束求解器：把「骑士与无赖」谜题的结构化陈述翻译成约束满足问题(CSP)，
用 python-constraint 库求解——这是实验 5-2 想论证的「代码求解」路径的确定性参考实现。

它不依赖任何 LLM / 网络，可完全离线运行，因此既用于 build_puzzles.py 校验谜题
「解唯一」，也用于 demo.py 的 solver 模式给出约束求解基线(理论上 100% 正确)。

【结构化陈述 DSL】每句话用一个 JSON 可序列化的列表表示，节点形式如下
(True=骑士/说真话，False=无赖/说假话)：

    ["is",   target, "knight"|"knave"]   # target 是骑士 / 无赖
    ["same",  a, b]                       # a 和 b 是同一类人
    ["diff",  a, b]                       # a 和 b 是不同类人
    ["count", "knight"|"knave", op, k]    # 全体中该角色的人数 op k, op ∈ {">=","<=","=="}
    ["and",  s1, s2]                       # 合取
    ["or",   s1, s2]                       # 析取
    ["not",  s1]                           # 否定
    ["implies", s1, s2]                    # 蕴含 s1 -> s2
    ["iff", s1, s2]                        # 双条件 s1 <-> s2

关键建模规则：对每位说话者 X 加一条【双条件约束】 `t[X] == eval_stmt(X 的话)`——
X 是骑士当且仅当他的话为真。绝不能把话本身当作硬约束。
"""
from constraint import Problem

_OPS = {">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b}


def eval_stmt(node, t):
    """在赋值 t(name->bool, True=骑士) 下求某句话的语义真值。"""
    tag = node[0]
    if tag == "is":
        _, target, role = node
        return t[target] if role == "knight" else (not t[target])
    if tag == "same":
        return t[node[1]] == t[node[2]]
    if tag == "diff":
        return t[node[1]] != t[node[2]]
    if tag == "count":
        _, role, op, k = node
        want = (role == "knight")
        cnt = sum(1 for v in t.values() if v == want)
        return _OPS[op](cnt, k)
    if tag == "and":
        return eval_stmt(node[1], t) and eval_stmt(node[2], t)
    if tag == "or":
        return eval_stmt(node[1], t) or eval_stmt(node[2], t)
    if tag == "not":
        return not eval_stmt(node[1], t)
    if tag == "implies":
        return (not eval_stmt(node[1], t)) or eval_stmt(node[2], t)
    if tag == "iff":
        return eval_stmt(node[1], t) == eval_stmt(node[2], t)
    raise ValueError(f"未知的陈述节点: {node!r}")


def solve(names, structs):
    """用 python-constraint 求解，返回所有满足约束的赋值(dict name->bool)列表。

    names   : 居民名字列表
    structs : dict name -> 该居民陈述的结构化 DSL
    """
    problem = Problem()
    for n in names:
        problem.addVariable(n, [True, False])

    # 对每位说话者加一条双条件约束：t[X] == (X 的话为真)
    for speaker in names:
        stmt = structs.get(speaker)
        if stmt is None:
            continue
        def make_constraint(speaker=speaker, stmt=stmt):
            def constraint(*values):
                t = dict(zip(names, values))
                return t[speaker] == eval_stmt(stmt, t)
            return constraint

        problem.addConstraint(make_constraint(), names)

    return problem.getSolutions()


def solve_labeled(names, structs):
    """求解并把布尔解转成 {name: 'knight'/'knave'}。返回解列表(通常唯一)。"""
    out = []
    for sol in solve(names, structs):
        out.append({n: ("knight" if sol[n] else "knave") for n in names})
    return out


def render_nl(node):
    """把结构化陈述渲染成中文题面(供随机生成的谜题使用)。"""
    tag = node[0]
    if tag == "is":
        role = "骑士" if node[2] == "knight" else "无赖"
        return f"{node[1]} 是{role}。"
    if tag == "same":
        return f"{node[1]} 和 {node[2]} 是同一类人。"
    if tag == "diff":
        return f"{node[1]} 和 {node[2]} 是不同类人。"
    if tag == "count":
        role = "骑士" if node[1] == "knight" else "无赖"
        word = {">=": "至少", "<=": "至多", "==": "恰好"}[node[2]]
        return f"我们当中{word}有 {node[3]} 个{role}。"
    if tag == "and":
        return f"{render_nl(node[1])[:-1]}，并且 {render_nl(node[2])}"
    if tag == "or":
        return f"{render_nl(node[1])[:-1]}，或者 {render_nl(node[2])}"
    if tag == "not":
        return f"以下说法不成立：{render_nl(node[1])}"
    if tag == "implies":
        return f"如果 {render_nl(node[1])[:-1]}，那么 {render_nl(node[2])}"
    if tag == "iff":
        return f"{render_nl(node[1])[:-1]}，当且仅当 {render_nl(node[2])}"
    raise ValueError(f"未知的陈述节点: {node!r}")


if __name__ == "__main__":
    # 自测：kk01 —— A 说"B 是无赖"，B 说"我们都不是骑士"
    names = ["A", "B"]
    structs = {
        "A": ["is", "B", "knave"],
        "B": ["and", ["is", "A", "knave"], ["is", "B", "knave"]],
    }
    print("求解结果:", solve_labeled(names, structs))
