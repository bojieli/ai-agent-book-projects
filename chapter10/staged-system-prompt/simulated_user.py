"""
模拟用户：在需求澄清阶段自动回答 Agent 的提问，实现无人值守跑通三阶段。

真实产品里，ask_clarifying_question 会把问题抛给真人；这里用一组预设答案，
按关键词“打分匹配”Agent 的问题并给出回答（命中关键词最多者胜）。
另外内置一个防重复机制：如果同一个问题被反复追问，就明确告诉 Agent
“已经回答过、没别的要求了，请开始实现”，避免澄清阶段陷入死循环。
"""

from typing import Dict, List, Tuple


class SimulatedUser:
    def __init__(self) -> None:
        # (关键词列表, 预设答案)。命中关键词越多，越优先采用。
        self.playbook: List[Tuple[List[str], str]] = [
            (["类型", "格式", "扩展名", "分类", "type", "kind"],
             "按文件类型分类：图片(jpg/png/gif)、文档(pdf/doc/txt)、"
             "音频(mp3/wav)、视频(mp4/mov)、压缩包(zip/rar)，其余归到 Others。"),
            (["递归", "子目录", "子文件夹", "recursive", "subfolder"],
             "不需要递归，只整理下载文件夹当前这一层，忽略里面已有的子文件夹。"),
            (["原文件名", "重命名", "保留名", "同名", "冲突", "重复", "覆盖", "rename", "conflict"],
             "保留原文件名；如果同名文件已存在，就在文件名后加 _1、_2 避免覆盖。"),
            (["移动", "复制", "剪切", "move", "copy"],
             "用移动（move）而不是复制，整理完原位置就不再保留这些文件。"),
            (["目标", "目的地", "存到", "保存到", "路径", "位置", "哪个文件夹", "destination", "location", "path"],
             "不用单独指定目标目录：就在下载文件夹内部按类别创建子文件夹"
             "（Images/Documents/Audio/Video/Archives/Others），把文件移动进对应子文件夹即可。"
             "下载文件夹本身的路径用命令行参数传入，不传则默认 ~/Downloads。"),
            (["日期", "时间", "date", "time"],
             "不用按日期分，只按类型分类就行。"),
            (["确认", "开始", "还有", "其他", "别的", "补充", "proceed", "anything else"],
             "没有其他要求了，需求就这些，可以开始实现。"),
        ]
        self.default_answer = "按常识处理即可，不用太复杂，保持脚本简单可读。"
        self.qa_log: List[Tuple[str, str]] = []
        self._asked_count: Dict[str, int] = {}

    def _match(self, q: str) -> str:
        best_reply, best_score = self.default_answer, 0
        q_lower = q.lower()  # 关键词已小写，问题也必须小写，否则 "Move or Copy?" 匹配不上 "move"
        for keywords, reply in self.playbook:
            score = sum(1 for kw in keywords if kw.lower() in q_lower)
            if score > best_score:
                best_reply, best_score = reply, score
        return best_reply

    def answer(self, question: str) -> str:
        norm = "".join(question.lower().split())
        self._asked_count[norm] = self._asked_count.get(norm, 0) + 1

        # 防重复：同一问题问到第 2 次，就催促 Agent 结束澄清、进入实现
        if self._asked_count[norm] >= 2:
            reply = (
                "这个问题我刚才已经回答过了，没有别的要求了。"
                "需求已经足够清楚，请直接调用 complete_requirements_analysis 进入实现阶段。"
            )
        else:
            reply = self._match(question)

        self.qa_log.append((question, reply))
        return reply
