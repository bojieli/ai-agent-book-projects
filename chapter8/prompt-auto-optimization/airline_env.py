"""
精简版「航空客服」模拟环境（对标 tau-bench 的航空场景，但去掉复杂度）。

包含三部分：
1. TOOLS      —— 暴露给 Agent 的工具（含关键的 transfer_to_human）。
2. run_agent  —— 一个带工具调用循环的最小 Agent：给定 system prompt 和用户请求，
                 返回它是否转接人工、以及最终回复。
3. CASES      —— 两组评测用例：
                 - 保留任务集(holdout)：正常请求，Agent 应正确处理（不该转的别转，该转的要转）。
                 - 边界案例集(boundary)：政策争议，Agent 应解释政策而非一转了之。
"""

import json
from config import get_client, get_model, get_temperature

# ----------------------------------------------------------------------------
# 1. 工具定义（OpenAI function-calling 格式）
# ----------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_reservation",
            "description": "根据订单号查询乘客的订单详情（航班、舱位、票价类型等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string", "description": "订单号"}
                },
                "required": ["confirmation_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_flight",
            "description": "为乘客办理改签到指定的新航班。",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string"},
                    "new_flight": {"type": "string", "description": "新航班号或日期"},
                },
                "required": ["confirmation_code", "new_flight"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_refund_policy",
            "description": "查询退票/退款政策。传入票价类型（如 经济舱特价票/全价经济舱/商务舱）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "fare_type": {"type": "string", "description": "票价类型"}
                },
                "required": ["fare_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_baggage_policy",
            "description": "查询行李额与逾重费政策。传入舱位等级。",
            "parameters": {
                "type": "object",
                "properties": {
                    "cabin": {"type": "string", "description": "舱位等级，如 经济舱/商务舱"}
                },
                "required": ["cabin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "change_seat",
            "description": "为乘客办理选座或换座。",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string"},
                    "seat": {"type": "string", "description": "目标座位号"},
                },
                "required": ["confirmation_code", "seat"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "把对话转接给人工客服。调用后 Agent 不再继续处理本次请求。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "转接原因"}
                },
                "required": ["reason"],
            },
        },
    },
]

# ----------------------------------------------------------------------------
# 2. 工具的 mock 实现（返回固定的模拟数据，供 Agent 组织回复）
# ----------------------------------------------------------------------------
_POLICY_REFUND = {
    "经济舱特价票": "经济舱特价票为不可退票产品，不支持自愿退款；如未起飞可申请退还机建燃油等税费。",
    "全价经济舱": "全价经济舱起飞前可退，收取 5% 退票手续费。",
    "商务舱": "商务舱起飞前可全额退票，不收手续费。",
}


def _run_tool(name: str, args: dict) -> str:
    """执行工具，返回给模型的字符串结果。"""
    if name == "lookup_reservation":
        return json.dumps(
            {
                "confirmation_code": args.get("confirmation_code", "UNKNOWN"),
                "passenger": "张伟",
                "flight": "YS1234 上海虹桥→北京首都 2026-08-01 09:00",
                "cabin": "经济舱",
                "fare_type": "经济舱特价票",
                "status": "已出票",
            },
            ensure_ascii=False,
        )
    if name == "change_flight":
        return json.dumps(
            {"result": "success", "new_flight": args.get("new_flight"), "fee": "改签费 200 元"},
            ensure_ascii=False,
        )
    if name == "get_refund_policy":
        fare = args.get("fare_type", "经济舱特价票")
        text = _POLICY_REFUND.get(fare, _POLICY_REFUND["经济舱特价票"])
        return json.dumps({"fare_type": fare, "policy": text}, ensure_ascii=False)
    if name == "get_baggage_policy":
        cabin = args.get("cabin") or "经济舱"
        free = "20kg" if "经济" in cabin else "30kg"
        return json.dumps(
            {"cabin": cabin, "free_allowance": free, "excess_fee": "逾重费 50 元/kg"},
            ensure_ascii=False,
        )
    if name == "change_seat":
        return json.dumps(
            {"result": "success", "seat": args.get("seat")}, ensure_ascii=False
        )
    return json.dumps({"result": "ok"}, ensure_ascii=False)


# ----------------------------------------------------------------------------
# 3. 最小 Agent 循环
# ----------------------------------------------------------------------------
def run_agent(system_prompt: str, user_message: str, max_steps: int = 4) -> dict:
    """
    运行一次客服会话。返回：
      {
        "transferred": bool,        # 是否调用了 transfer_to_human
        "transfer_reason": str|None,
        "final_text": str,          # Agent 面向乘客的最终回复（若转接则为空）
        "tool_calls": [str, ...],   # 依次调用过的工具名
      }
    """
    client = get_client()
    model = get_model()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    tool_calls_log = []

    for _ in range(max_steps):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            temperature=get_temperature(),
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            # 模型直接给出面向乘客的文字回复 —— 会话结束
            return {
                "transferred": False,
                "transfer_reason": None,
                "final_text": msg.content or "",
                "tool_calls": tool_calls_log,
            }

        # 有工具调用，先把 assistant 消息加入历史
        messages.append(msg)

        transferred_now = False
        transfer_reason = None
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls_log.append(name)

            if name == "transfer_to_human":
                transferred_now = True
                transfer_reason = args.get("reason", "")
                result = json.dumps({"result": "transferred"}, ensure_ascii=False)
            else:
                result = _run_tool(name, args)

            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result}
            )

        if transferred_now:
            return {
                "transferred": True,
                "transfer_reason": transfer_reason,
                "final_text": "",
                "tool_calls": tool_calls_log,
            }

    # 超出步数上限仍未收敛，兜底再要一次纯文本回复
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=get_temperature()
    )
    return {
        "transferred": False,
        "transfer_reason": None,
        "final_text": resp.choices[0].message.content or "",
        "tool_calls": tool_calls_log,
    }


# ----------------------------------------------------------------------------
# 4. 评测用例
# ----------------------------------------------------------------------------
# 每个用例字段：
#   id / group / user   —— 用户请求
#   should_transfer     —— 正确行为是否应当转接人工
#   rubric              —— 当 should_transfer=False 时，判定"是否妥善处理"的要点
CASES = [
    # ---------- 保留任务集(holdout)：既有正确行为，优化后不能退化 ----------
    {
        "id": "H1-改签",
        "group": "holdout",
        "user": "你好，我的订单号是 ABC123，想把 8 月 1 日的航班改到 8 月 3 日，帮我改一下。",
        "should_transfer": False,
        "rubric": "查询订单并为乘客办理/说明改签到 8 月 3 日的相关信息（如改签费），而不是转人工。",
    },
    {
        "id": "H2-行李额",
        "group": "holdout",
        "user": "我买的是经济舱，免费托运行李额是多少？超重了怎么收费？",
        "should_transfer": False,
        "rubric": "给出经济舱免费行李额与逾重费的具体政策信息，而不是转人工。",
    },
    {
        "id": "H3-选座",
        "group": "holdout",
        "user": "订单号 ABC123，我想换到靠窗的 32A 座位。",
        "should_transfer": False,
        "rubric": "为乘客办理/确认换到 32A 座位，而不是转人工。",
    },
    {
        "id": "H4-明确要人工",
        "group": "holdout",
        "user": "别跟我扯了，我就要跟人工客服说话，马上给我转人工。",
        "should_transfer": True,  # 乘客明确要求人工 —— 这类本就该转，优化后仍要能转
        "rubric": "乘客明确要求人工客服，应当转接。",
    },
    {
        "id": "H5-紧急安全",
        "group": "holdout",
        "user": "我现在在机场，同行的老人突然晕倒了，赶不上 YS1234 航班了，需要马上有人帮忙处理！",
        "should_transfer": True,  # 紧急安全 —— 本就该转，优化后仍要能转
        "rubric": "涉及紧急人身安全，应当转接人工立即介入。",
    },

    # ---------- 边界案例集(boundary)：政策争议，应解释政策而非一转了之 ----------
    {
        "id": "B1-不可退票要退款",
        "group": "boundary",
        "user": "我要求全额退款！订单 ABC123。我不管，我就要全退。",
        "should_transfer": False,
        "rubric": "查询退票政策后，耐心解释该票（经济舱特价票）为不可退票产品、可退税费，并给出可行替代方案，而不是转人工。",
    },
    {
        "id": "B2-要求免改签费",
        "group": "boundary",
        "user": "改签还要收我 200 块？凭什么！你必须给我免掉这个改签费，不然没完。",
        "should_transfer": False,
        "rubric": "耐心解释改签费的政策依据，说明无法违规减免，并提供合规的替代方案，而不是因为乘客不满就转人工。",
    },
    {
        "id": "B3-小延误索赔",
        "group": "boundary",
        "user": "航班晚了半小时，害我差点误事，我要求航空公司赔偿我 500 块！",
        "should_transfer": False,
        "rubric": "共情并解释延误补偿的政策门槛（30 分钟的短延误通常不达补偿标准），说明处理口径，而不是转人工。",
    },
    {
        "id": "B4-索要免费升舱",
        "group": "boundary",
        "user": "我是老客户了，这次必须给我免费升到商务舱，这点面子都不给？",
        "should_transfer": False,
        "rubric": "礼貌解释免费升舱不符合政策、说明可付费升舱或积分兑换等合规途径，而不是转人工。",
    },
    {
        "id": "B5-超额免费行李",
        "group": "boundary",
        "user": "我经济舱，这次要带 3 件行李，你们必须都给我免费托运，别收钱。",
        "should_transfer": False,
        "rubric": "解释经济舱的免费行李额与超出部分的收费政策，说明无法全部免费，并给出合规建议，而不是转人工。",
    },
]


def get_cases(group: str = None):
    if group is None:
        return CASES
    return [c for c in CASES if c["group"] == group]
