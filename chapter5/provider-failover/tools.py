"""任务与工具。

工具全是本地确定性函数：这个实验测的是轨迹能不能换一家模型接着跑，不是模型
会不会查天气。答案唯一，可以程序化核对。
"""

from __future__ import annotations

PRICES = {
    "东京": {"flight_cny": 3200, "hotel": (18000, "JPY"), "meal": (6000, "JPY")},
}
RATES = {"JPY": 0.048, "USD": 7.12, "EUR": 7.75}

TASK = ("帮我算一下从北京去东京出差的总预算：往返机票、住宿和餐费都要算上，行程是 3 晚 4 天，"
        "住宿按 3 晚、餐费按 4 天计。最后用人民币给出一个总额。")

# 3200 + 18000*3*0.048 + 6000*4*0.048
EXPECTED_TOTAL_CNY = 6944.0

# 实验 5-2 在这次调用的参数中途切断，拼接回来的参数应当与它逐字相同。
TRUNCATED_CALL_ARGS = {"city": "东京"}

SYSTEM = "你是一个差旅助理。需要数据时调用工具，不要凭印象编造价格或汇率。拿齐数据后给出人民币总额。"

TOOLS = [
    {"type": "function", "function": {
        "name": "get_flight_price", "description": "查询往返机票价格（人民币）",
        "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "目的地城市"}},
                       "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "get_hotel_price", "description": "查询每晚住宿价格及其币种",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "get_meal_budget", "description": "查询每日餐费预算及其币种",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "get_exchange_rate", "description": "查询该币种兑人民币的汇率",
        "parameters": {"type": "object", "properties": {"currency": {"type": "string", "description": "如 JPY"}},
                       "required": ["currency"]}}},
]


def execute(name: str, args: dict) -> str:
    city = (args.get("city") or "东京").strip()
    row = PRICES.get(city) or PRICES["东京"]
    if name == "get_flight_price":
        return f'{{"city":"{city}","round_trip_cny":{row["flight_cny"]}}}'
    if name == "get_hotel_price":
        amount, cur = row["hotel"]
        return f'{{"city":"{city}","per_night":{amount},"currency":"{cur}"}}'
    if name == "get_meal_budget":
        amount, cur = row["meal"]
        return f'{{"city":"{city}","per_day":{amount},"currency":"{cur}"}}'
    if name == "get_exchange_rate":
        cur = (args.get("currency") or "JPY").upper()
        rate = RATES.get(cur)
        if rate is None:
            return f'{{"error":"不支持的币种 {cur}"}}'
        return f'{{"currency":"{cur}","cny_per_unit":{rate}}}'
    return f'{{"error":"没有名为 {name} 的工具"}}'


def answer_is_correct(text: str, tolerance: float = 0.01) -> bool:
    """最终答复里出现正确总额即算完成，允许 1% 的取整误差。"""
    import re

    if not text:
        return False
    for raw in re.findall(r"\d[\d,]*\.?\d*", text):
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        if abs(value - EXPECTED_TOTAL_CNY) <= EXPECTED_TOTAL_CNY * tolerance:
            return True
    return False
