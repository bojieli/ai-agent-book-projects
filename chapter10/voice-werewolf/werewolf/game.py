# -*- coding: utf-8 -*-
"""法官（主持人）Agent：代码驱动的游戏编排与信息权限控制中枢。

法官不是 LLM——它是**确定性的编排器**，负责：
1. 维护中心化游戏状态（身份、阵营、生死、阶段、历史）。
2. **信息权限控制**：决定每条信息投递给哪些玩家 Agent 的私有上下文
   （狼人才知道队友、预言家才知道查验结果、公开发言进所有人），并登记审计。
3. 编排昼夜循环：夜晚（狼人刀人 → 预言家查验 → 女巫用药）→ 白天（公布死讯 →
   依次发言 → 投票放逐）→ 结算胜负。
"""

import random
from collections import Counter
from typing import List, Optional

from .agent import PlayerAgent
from .audit import AuditLog
from .roles import Role, Faction


def build_roles(players: int = 7, wolves: Optional[int] = None) -> List[Role]:
    """按玩家总数推导身份组成：默认 7 人 = 2 狼人 + 1 预言家 + 1 女巫 + 3 村民。

    - wolves 未指定时按 max(1, players // 3) 估算（7 人得 2 狼，与书中默认一致）。
    - 4 人及以上配 1 预言家，5 人及以上再配 1 女巫，其余全为村民。
    """
    if players < 3:
        raise ValueError("玩家总数至少为 3")
    wolves = wolves if wolves is not None else max(1, players // 3)
    seer = 1 if players >= 4 else 0
    witch = 1 if players >= 5 else 0
    villagers = players - wolves - seer - witch
    if wolves < 1 or villagers < 0:
        raise ValueError(
            f"身份组成非法：{players} 人无法容纳 {wolves} 狼 + {seer} 预言家 + "
            f"{witch} 女巫（剩余村民 {villagers}）。请调小 --wolves 或调大 --players。")
    return ([Role.WEREWOLF] * wolves + [Role.SEER] * seer
            + [Role.WITCH] * witch + [Role.VILLAGER] * villagers)


def create_players(seed: int = 42, players: int = 7, wolves: Optional[int] = None,
                   offline: bool = False, human_seat: Optional[int] = None,
                   voice=None, simulated_user_seat: Optional[int] = None,
                   simulator_model: Optional[str] = None) -> List[PlayerAgent]:
    """创建一局游戏（默认 7 人：2 狼人 + 1 预言家 + 1 女巫 + 3 村民，控成本）。

    身份随机洗牌后分配给 P1~Pn，保证每局身份分布不同但可用 seed 复现。
    offline=True 时每个 Agent 用规则策略代替 LLM（零成本、可复现）；每个 Agent
    还会拿到一个按 seed 与序号种子化的独立随机源，保证离线对局完全可复现。
    """
    rng = random.Random(seed)
    roles = build_roles(players, wolves)
    rng.shuffle(roles)
    result = []
    if human_seat is not None and simulated_user_seat is not None:
        raise ValueError("human_seat and simulated_user_seat are mutually exclusive")
    for i, role in enumerate(roles):
        if human_seat == i + 1:
            if voice is None:
                raise ValueError("human_seat requires a live voice session")
            from .human import HumanPlayerAgent
            result.append(HumanPlayerAgent(f"P{i+1}", role, voice))
        elif simulated_user_seat == i + 1:
            if voice is None:
                raise ValueError("simulated_user_seat requires a simulated voice session")
            from .simulator import SimulatedUserPlayerAgent
            result.append(SimulatedUserPlayerAgent(
                f"P{i+1}", role, voice, model=simulator_model
            ))
        else:
            result.append(PlayerAgent(f"P{i+1}", role, offline=offline,
                                      rng=random.Random(seed * 1000 + i)))
    return result


class Judge:
    """法官：编排 + 信息权限控制。"""

    def __init__(self, players: List[PlayerAgent], seed: int = 42,
                 tts=None, max_rounds: int = 6):
        self.players = players
        self.names = [p.name for p in players]
        self.audit = AuditLog()
        self.rng = random.Random(seed + 1)
        self.tts = tts                 # 可选的 TTS 合成器（--voice 时注入）
        self.max_rounds = max_rounds
        self.round_no = 0
        self.phase = "初始化"
        self.completed_rounds = 0
        self.action_history = []
        # 女巫药剂状态
        self.witch_heal_available = True
        self.witch_poison_available = True

    # ------------------------------------------------------------------
    # 信息投递原语：每个原语都同时 (a) 写入相应 Agent 的私有上下文；
    #               (b) 在审计日志里登记「这条信息进了谁的上下文」。
    # ------------------------------------------------------------------
    def _log(self, category, content, visible_to):
        self.audit.add(self.round_no, self.phase, category, content, visible_to)

    @staticmethod
    def _decision_record(player, **record):
        """Attach the model's stated reason to evidence without exposing it publicly."""
        reason = getattr(player, "last_decision_reason", None)
        if reason:
            record["reason"] = reason
        player.last_decision_reason = None
        return record

    def broadcast(self, category: str, content: str):
        """公开信息：进入**所有玩家**（含已出局者）的上下文。"""
        for p in self.players:
            p.observe(content)
        self._log(category, content, self.names)

    def private_send(self, player: PlayerAgent, category: str, content: str):
        """私密信息：只进入**指定单个玩家**的上下文。"""
        player.observe(content)
        self._log(category, content, [player.name])

    def wolves_send(self, category: str, content: str):
        """狼人专属信息：只进入**所有狼人**的上下文。"""
        wolves = self.wolves()
        for w in wolves:
            w.observe(content)
        self._log(category, content, [w.name for w in wolves])

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------
    def alive(self) -> List[PlayerAgent]:
        return [p for p in self.players if p.alive]

    def wolves(self, alive_only=False) -> List[PlayerAgent]:
        ws = [p for p in self.players if p.role == Role.WEREWOLF]
        return [w for w in ws if w.alive] if alive_only else ws

    def by_name(self, name: str) -> Optional[PlayerAgent]:
        for p in self.players:
            if p.name == name:
                return p
        return None

    def _print_private(self, permitted: List[str], text: str):
        """Prevent private night logs leaking through the live player's terminal."""
        user = next((p for p in self.players if getattr(p, "is_user", False)), None)
        if user is None or user.name in permitted:
            print(text)

    # ------------------------------------------------------------------
    # 阶段 0：分配身份并投递「谁知道谁」的初始信息
    # ------------------------------------------------------------------
    def assign_identities(self):
        self.phase = "身份分配"
        print("\n" + "#" * 78)
        print("【阶段 0 · 身份分配】法官私下告知每人身份；狼人额外被告知队友是谁。")
        print("  信息隔离：每人只知道自己的身份；只有狼人上下文里有『队友身份』。")
        print("#" * 78)
        # 每个玩家私下知道自己的身份（只进本人上下文）
        for p in self.players:
            self.private_send(p, "身份分配", f"你的身份是：{p.role.value}")
        # 狼人互相知道队友是谁（只进狼人上下文）——这是信息不对称的关键
        wolves = self.wolves()
        team = "、".join(w.name for w in wolves)
        self.wolves_send("狼人队友身份", f"狼人阵营的玩家是：{team}（你们互为队友，夜晚共同行动）")
        user = next((p for p in self.players if getattr(p, "is_user", False)), None)
        if user:
            # The old all-AI observer table would be a side-channel leak to a real
            # player. In live mode only the human's permitted private facts are spoken.
            print("  [真人局] 上帝视角身份表已隐藏，防止终端侧信道泄露。")
            private = f"您的座位是{user.name}，您的身份是{user.role.value}。"
            if user.role == Role.WEREWOLF:
                private += f" 狼人队友是{team}。"
            user.voice.say("judge-private", private, 0, allow_barge_in=False)
        else:
            # All-AI diagnostic mode may show ground truth to the external evaluator.
            print("  [上帝视角/仅外部评测者可见] 真实身份表：")
            for p in self.players:
                print(f"    {p.name}: {p.role.value}（{p.faction.value}）")
            print(f"  狼队友（仅狼人 {team} 的上下文里有这条信息）")

    # ------------------------------------------------------------------
    # 夜晚
    # ------------------------------------------------------------------
    def night(self) -> List[str]:
        """执行一个夜晚，返回今晚出局玩家名列表。"""
        self.phase = "夜晚"
        print("\n" + "=" * 78)
        print(f"【第 {self.round_no} 回合 · 夜晚】天黑请闭眼。")
        print("  信息隔离：以下所有行动与结果都是私密的——狼人共识只进狼人上下文、")
        print("  预言家查验结果只进预言家上下文、女巫用药只进女巫上下文。")
        print("=" * 78)

        killed = self._wolves_act()
        self._seer_act()
        poisoned, saved = self._witch_act(killed)

        # 结算今晚死亡：被刀且未被救 + 被毒
        deaths = []
        if killed and not saved:
            deaths.append(killed)
        if poisoned and poisoned not in deaths:
            deaths.append(poisoned)
        for name in deaths:
            self.by_name(name).alive = False
        return deaths

    def _wolves_act(self) -> Optional[str]:
        wolves = self.wolves(alive_only=True)
        if not wolves:
            return None
        # 候选：所有存活的非狼人（狼人不刀自己人）
        candidates = [p.name for p in self.alive() if p.role != Role.WEREWOLF]
        if not candidates:
            return None
        votes = []
        for w in wolves:
            t = w.choose_target(
                "现在是夜晚，狼人行动。请与队友一致，选择今晚要击杀的一名好人玩家。",
                candidates, self.names, allow_none=False)
            if t:
                votes.append(t)
                self.action_history.append(self._decision_record(
                    w, round=self.round_no, phase="night", actor=w.name,
                    role=w.role.value, action="kill_proposal", target=t
                ))
                self._print_private(
                    [wolf.name for wolf in wolves],
                    f"  [仅法官+狼人可见] 狼人 {w.name} 提议击杀 → {t}",
                )
        if not votes:
            return None
        # 汇总：最高票；平票取第一名狼人的意见
        tally = Counter(votes)
        top = tally.most_common()
        best = [n for n, c in top if c == top[0][1]]
        killed = next((v for v in votes if v in best), best[0]) if len(best) > 1 else top[0][0]
        # 把「今晚狼人共识」写进狼人共享上下文（只有狼人看得到）
        self.wolves_send("狼人夜间共识", f"第{self.round_no}回合夜晚，狼人决定击杀 {killed}")
        self._print_private(
            [wolf.name for wolf in wolves],
            f"  → 狼人共识：击杀 {killed}（此共识只进狼人上下文）",
        )
        return killed

    def _seer_act(self):
        seers = [p for p in self.alive() if p.role == Role.SEER]
        if not seers:
            return
        seer = seers[0]
        candidates = [p.name for p in self.alive() if p.name != seer.name]
        target = seer.choose_target(
            "现在是夜晚，预言家行动。请选择一名玩家查验其真实阵营。",
            candidates, self.names, allow_none=False)
        if not target:
            target = self.rng.choice(candidates)
        tgt = self.by_name(target)
        result = "狼人" if tgt.role == Role.WEREWOLF else "好人"
        self.action_history.append(self._decision_record(
            seer, round=self.round_no, phase="night", actor=seer.name,
            role=seer.role.value, action="inspect", target=target, result=result
        ))
        # 查验结果只进预言家本人上下文——这是预言家独享的关键信息
        self.private_send(seer, "预言家查验结果",
                          f"第{self.round_no}回合你查验了 {target}，结果为【{result}】")
        if getattr(seer, "is_user", False):
            seer.voice.say(
                "judge-private",
                f"您查验了{target}，结果是{result}。",
                self.round_no,
                allow_barge_in=False,
            )
        self._print_private(
            [seer.name],
            f"  [仅法官+预言家 {seer.name} 可见] 预言家查验 {target} → {result}",
        )

    def _witch_act(self, killed: Optional[str]):
        witches = [p for p in self.alive() if p.role == Role.WITCH]
        if not witches:
            return None, False
        witch = witches[0]
        saved = False
        poisoned = None

        # 告知女巫今晚谁被刀（只进女巫上下文）
        if killed:
            self.private_send(witch, "女巫夜间信息", f"第{self.round_no}回合，今晚被狼人袭击的是 {killed}")
            self._print_private(
                [witch.name],
                f"  [仅法官+女巫 {witch.name} 可见] 女巫得知今晚被刀者：{killed}",
            )
            # 解药：是否救
            if self.witch_heal_available and killed != witch.name:
                dec = witch.choose_target(
                    f"今晚 {killed} 被狼人袭击。你是否使用【解药】救他？"
                    "（救则 target 填该玩家名，不救填 none）",
                    [killed], self.names, allow_none=True)
                if dec == killed:
                    saved = True
                    self.witch_heal_available = False
                    self.private_send(witch, "女巫用药", f"你在第{self.round_no}回合使用了解药，救活了 {killed}")
                    self._print_private(
                        [witch.name], f"  [仅法官+女巫可见] 女巫使用解药救 {killed}"
                    )
                    self.action_history.append(self._decision_record(
                        witch, round=self.round_no, phase="night", actor=witch.name,
                        role=witch.role.value, action="heal", target=killed
                    ))
                else:
                    witch.last_decision_reason = None
        else:
            self.private_send(witch, "女巫夜间信息", f"第{self.round_no}回合是平安夜（无人被狼人击杀，或你无从得知）")

        # 毒药：被狼人击杀且未救活的女巫今晚无法使用毒药
        if self.witch_poison_available and not (killed == witch.name and not saved):
            candidates = [p.name for p in self.alive() if p.name != witch.name]
            dec = witch.choose_target(
                "你是否使用【毒药】毒死一名你怀疑是狼人的玩家？（毒则填玩家名，不毒填 none）",
                candidates, self.names, allow_none=True)
            if dec and dec in candidates:
                poisoned = dec
                self.witch_poison_available = False
                self.private_send(witch, "女巫用药", f"你在第{self.round_no}回合使用了毒药，毒杀了 {poisoned}")
                self._print_private(
                    [witch.name], f"  [仅法官+女巫可见] 女巫使用毒药毒 {poisoned}"
                )
                self.action_history.append(self._decision_record(
                    witch, round=self.round_no, phase="night", actor=witch.name,
                    role=witch.role.value, action="poison", target=poisoned
                ))
            else:
                witch.last_decision_reason = None
        return poisoned, saved

    # ------------------------------------------------------------------
    # 白天
    # ------------------------------------------------------------------
    def day(self, night_deaths: List[str]) -> Optional[str]:
        """白天：公布死讯 → 依次发言 → 投票放逐。返回被放逐者名（或 None）。"""
        self.phase = "白天"
        print("\n" + "=" * 78)
        print(f"【第 {self.round_no} 回合 · 白天】天亮请睁眼。")
        print("  信息隔离：死讯、发言、投票结果都是公开信息，进入所有人上下文。")
        print("=" * 78)

        # 公布死讯（公开）
        if night_deaths:
            msg = f"天亮了。昨晚出局的玩家是：{'、'.join(night_deaths)}"
        else:
            msg = "天亮了。昨晚是平安夜，无人出局"
        self.broadcast("公开-死讯", msg)
        print(f"  法官宣布：{msg}")
        if self.tts and hasattr(self.tts, "say"):
            self.tts.say("judge", msg, self.round_no, allow_barge_in=False)

        if self._check_winner():
            return None

        # 依次发言（公开）
        print("\n  —— 发言阶段（按座位顺序，公开发言进入所有人上下文）——")
        for p in self.alive():
            speech = p.speak(self.names)
            line = f"{p.name}（发言）：{speech}"
            self.broadcast("公开发言", f"{p.name} 说：{speech}")
            self.action_history.append({"round": self.round_no, "phase": "day", "actor": p.name, "role": p.role.value, "action": "speech", "text": speech})
            print(f"  {line}")
            if self.tts and not getattr(p, "is_user", False):
                interruption = self.tts.synth(p.name, speech, self.round_no)
                if interruption:
                    human = next((q for q in self.alive() if getattr(q, "is_human", False)), None)
                    if human:
                        self.broadcast("公开发言-真人打断", f"{human.name} 打断说：{interruption}")
                        self.action_history.append({"round": self.round_no, "phase": "day", "actor": human.name, "role": human.role.value, "action": "interruption", "text": interruption, "interrupted": p.name})
                        print(f"  [实时打断] {human.name}：{interruption}")

        # 投票放逐（公开）
        print("\n  —— 投票阶段 ——")
        exiled = self._vote()
        return exiled

    def _vote(self) -> Optional[str]:
        alive = self.alive()
        tally = Counter()
        for p in alive:
            candidates = [q.name for q in alive if q.name != p.name]
            t = p.vote(candidates, self.names)
            if t:
                tally[t] += 1
                self.action_history.append(self._decision_record(
                    p, round=self.round_no, phase="vote", actor=p.name,
                    role=p.role.value, action="vote", target=t
                ))
                print(f"  {p.name} 投票 → {t}")
            else:
                p.last_decision_reason = None
                print(f"  {p.name} 弃票")
        if not tally:
            self.broadcast("公开-放逐", "本轮无人被放逐（全部弃票）")
            print("  本轮无人被放逐")
            return None
        top = tally.most_common()
        best = [n for n, c in top if c == top[0][1]]
        exiled = self.rng.choice(best) if len(best) > 1 else top[0][0]
        ex = self.by_name(exiled)
        ex.alive = False
        result = f"投票结果：{exiled} 被放逐出局，其真实身份是【{ex.role.value}】。计票：" + \
                 "，".join(f"{n}={c}票" for n, c in top)
        self.broadcast("公开-放逐", result)
        print(f"  → {result}")
        if self.tts and hasattr(self.tts, "say"):
            self.tts.say("judge", result, self.round_no, allow_barge_in=False)
        return exiled

    # ------------------------------------------------------------------
    # 结算
    # ------------------------------------------------------------------
    def _check_winner(self) -> Optional[Faction]:
        """判定当前是否已分出胜负：狼人全灭则好人胜；狼人数≥好人数则狼人胜；
        否则返回 None（继续游戏）。"""
        w = len(self.wolves(alive_only=True))
        g = len([p for p in self.alive() if p.role != Role.WEREWOLF])
        if w == 0 and g == 0:
            return Faction.UNDECIDED
        if w == 0:
            return Faction.GOOD
        if w >= g:  # 狼人数不少于好人数 → 狼人胜（屠边简化规则）
            return Faction.WEREWOLF
        return None

    def run(self) -> Faction:
        """跑完整一局，返回获胜阵营。"""
        self.assign_identities()
        winner = None
        while winner is None and self.round_no < self.max_rounds:
            self.round_no += 1
            for player in self.players:
                player.current_round = self.round_no
            deaths = self.night()
            winner = self._check_winner()
            if winner:
                break
            self.day(deaths)
            self.completed_rounds += 1
            winner = self._check_winner()
        if winner is None:
            # A safety round limit is not a game-rule victory condition. Report an
            # unresolved game honestly instead of awarding Good an invented win.
            winner = self._check_winner() or Faction.UNDECIDED
        self._announce(winner)
        return winner

    def _announce(self, winner: Faction):
        self.phase = "结算"
        print("\n" + "#" * 78)
        print("【游戏结束 · 结算】")
        alive = [f"{p.name}({p.role.value})" for p in self.alive()]
        print(f"  存活玩家：{'、'.join(alive) if alive else '无'}")
        if winner == Faction.UNDECIDED:
            print("  >>> 本局未决：达到安全回合上限时仍无阵营满足胜利条件 <<<")
        else:
            print(f"  >>> 获胜阵营：{winner.value} <<<")
        print("#" * 78)
        if self.tts and hasattr(self.tts, "say"):
            message = (
                "游戏结束，本局未在回合上限内分出胜负"
                if winner == Faction.UNDECIDED
                else f"游戏结束，获胜阵营是{winner.value}"
            )
            self.tts.say("judge", message, self.round_no, allow_barge_in=False)
