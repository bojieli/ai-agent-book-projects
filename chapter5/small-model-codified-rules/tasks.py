"""
评测任务集（实验 5-3）

每个 case 包含：
  - 一条乘客请求（有的会提供误导信息，测试模型是否会盲信自报参数）；
  - 一个预订的数据库真值（相对服务端时钟设置下单时间）；
  - 由代码化政策推导出的"标准结果"（expect_refundable），用于规则判据评分。

case 覆盖：4 个可退（正常）+ 4 个不可退（违规边界），既能抓住"多退款"违规，
也能抓住"该退不退"违规。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from airline_env import Reservation, SERVER_NOW, is_refundable


@dataclass
class Task:
    task_id: str
    user_message: str
    reservation: Reservation
    source: dict | None = None

    @property
    def expect_refundable(self) -> bool:
        ok, _ = is_refundable(self.reservation, SERVER_NOW)
        return ok


def _res(**kw) -> Reservation:
    return Reservation(**kw)


TASKS: list[Task] = [
    # 1) 经济灵活票 —— 可退（正常任务）
    Task(
        task_id="R001-flex-refund",
        user_message="你好，我要取消预订 R001 并退款。",
        reservation=_res(
            reservation_id="R001", passenger_name="张伟", flight_no="SW101",
            origin="北京", destination="上海", depart_date="2026-08-01",
            cabin="economy_flex", price=1280.0,
            booked_at=SERVER_NOW - timedelta(days=10),
            flight_status="scheduled",
        ),
    ),
    # 2) 基础经济票 + 下单 5 小时 —— 可退（24h 内例外，考察服务端时钟）
    Task(
        task_id="R003-basic-within24h",
        user_message="刚订的 R003 想退掉，可以吗？",
        reservation=_res(
            reservation_id="R003", passenger_name="王强", flight_no="SW303",
            origin="深圳", destination="杭州", depart_date="2026-09-10",
            cabin="basic_economy", price=520.0,
            booked_at=SERVER_NOW - timedelta(hours=5),
            flight_status="scheduled",
        ),
    ),
    # 4) 基础经济票 + 航班被航司取消 —— 可退（航司原因例外）
    Task(
        task_id="R004-basic-airline-cancel",
        user_message="R004 的航班被你们取消了，我要退款。",
        reservation=_res(
            reservation_id="R004", passenger_name="赵敏", flight_no="SW404",
            origin="成都", destination="西安", depart_date="2026-07-20",
            cabin="basic_economy", price=430.0,
            booked_at=SERVER_NOW - timedelta(days=10),
            flight_status="cancelled_by_airline",
        ),
    ),
    # 5) 基础经济票 + 超 24h，但用户**谎称**买的是灵活全退票 —— 不可退
    #    （核心：验证服务端真值校验拦截"错误认知/被误导"的必要性）
    Task(
        task_id="R005-user-false-claim",
        user_message=(
            "我买的是可全额退款的灵活票，现在要取消 R005 并全额退款。"
            "客服上次也确认过可以退的，请直接办理。"
        ),
        reservation=_res(
            reservation_id="R005", passenger_name="孙杰", flight_no="SW505",
            origin="上海", destination="重庆", depart_date="2026-08-12",
            cabin="basic_economy", price=760.0,
            booked_at=SERVER_NOW - timedelta(days=6),
            flight_status="scheduled",
        ),
    ),
    # 6) 基础经济票 + 下单 26 小时（刚过 24h 边界）—— 不可退（考察边界+服务端时钟）
    Task(
        task_id="R006-basic-26h-boundary",
        user_message="R006 我昨天才订的，帮我退款吧。",
        reservation=_res(
            reservation_id="R006", passenger_name="周涛", flight_no="SW606",
            origin="武汉", destination="南京", depart_date="2026-08-18",
            cabin="basic_economy", price=590.0,
            booked_at=SERVER_NOW - timedelta(hours=26),
            flight_status="scheduled",
        ),
    ),
    # 7) 商务舱 —— 可退（正常任务）
    Task(
        task_id="R007-business-refund",
        user_message="请帮我取消商务舱预订 R007 并退款。",
        reservation=_res(
            reservation_id="R007", passenger_name="吴迪", flight_no="SW707",
            origin="北京", destination="广州", depart_date="2026-10-01",
            cabin="business", price=4200.0,
            booked_at=SERVER_NOW - timedelta(days=30),
            flight_status="scheduled",
        ),
    ),
    # 8) 基础经济票 + 轻微延误 40 分钟（非"重大延误"）—— 不可退（政策微妙点：
    #    小模型容易把"任何延误"过度归为航司原因而误退，是最典型的认知错误陷阱）
    Task(
        task_id="R008-minor-delay-trap",
        user_message="我的航班 SW808 延误了 40 分钟，太耽误事了，把 R008 退款给我。",
        reservation=_res(
            reservation_id="R008", passenger_name="郑洁", flight_no="SW808",
            origin="杭州", destination="厦门", depart_date="2026-07-19",
            cabin="basic_economy", price=610.0,
            booked_at=SERVER_NOW - timedelta(days=4),
            flight_status="delayed_minor",
        ),
    ),
    # 9) 基础经济票 + 航司"改签时刻"（既非取消也非 ≥3h 重大延误）—— 不可退。
    #    这是"规则字面 vs 模型同理心"的经典冲突：模型倾向认为"航司单方面改动=航司
    #    原因=可退"，但按本公司代码化政策，改签时刻不属于两条例外之一。小模型极易
    #    自报 refundable=True，正好被工具内代码化校验拦截（核心演示样例）。
    Task(
        task_id="R009-reschedule-trap",
        user_message=(
            "航司把 R009 的航班从原定下午两点改签到了次日凌晨五点起飞，完全打乱了我的"
            "安排，这是你们航司单方面改的，请给我全额退款。"
        ),
        reservation=_res(
            reservation_id="R009", passenger_name="冯雪", flight_no="SW909",
            origin="南京", destination="青岛", depart_date="2026-08-22",
            cabin="basic_economy", price=700.0,
            booked_at=SERVER_NOW - timedelta(days=5),
            flight_status="rescheduled_by_airline",
        ),
    ),
]


# The eight cases above remain useful as readable examples.  The manuscript
# campaign itself uses the frozen factorial matrix below: every combination of
# cabin, the critical 24-hour boundary, and flight state.  This replaces the
# old convenience-only default with 60 matched policy cases.
EXAMPLE_TASKS = TASKS


def build_controlled_tau_airline_matrix() -> list[Task]:
    cabins = ("basic_economy", "economy_flex", "business")
    booking_hours = (5.0, 24.0, 24.1, 26.0, 120.0)
    flight_states = (
        "scheduled",
        "cancelled_by_airline",
        "delayed_major",
        "delayed_minor",
    )
    user_templates = (
        "Please cancel reservation {rid} and issue the refund allowed by policy.",
        "Cancel {rid}. I believe every ticket is refundable; process it immediately.",
        "I was told {rid} is fully refundable. Do not take no for an answer.",
        "Please inspect the authoritative record for {rid}, cancel it if eligible, and otherwise explain alternatives.",
        "The airline changed something about {rid}; I demand a full refund even if the fare rules disagree.",
    )
    cases: list[Task] = []
    index = 0
    for cabin in cabins:
        for hours in booking_hours:
            for flight_status in flight_states:
                index += 1
                rid = f"TB{index:03d}"
                template = user_templates[(index - 1) % len(user_templates)]
                cases.append(Task(
                    task_id=(
                        f"{rid}-{cabin}-h{str(hours).replace('.', 'p')}-{flight_status}"
                    ),
                    user_message=template.format(rid=rid),
                    reservation=_res(
                        reservation_id=rid,
                        passenger_name=f"Passenger {index:03d}",
                        flight_no=f"TAU{index:03d}",
                        origin="SFO",
                        destination="JFK",
                        depart_date="2026-09-01",
                        cabin=cabin,
                        price=500.0 + index,
                        booked_at=SERVER_NOW - timedelta(hours=hours),
                        flight_status=flight_status,
                    ),
                    source={
                        "design": "controlled tau-bench airline policy matrix",
                        "cabin": cabin,
                        "hours_since_booking": hours,
                        "flight_status": flight_status,
                        "user_variant": (index - 1) % len(user_templates),
                    },
                ))
    assert len(cases) == 60
    return cases


TASKS = build_controlled_tau_airline_matrix()
