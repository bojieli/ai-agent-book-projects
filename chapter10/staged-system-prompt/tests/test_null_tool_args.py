"""回归测试：模型对必填工具参数显式传 null 时，工具分发不应崩溃。

此前 write_file 的 content 为 null 时 len(None) -> TypeError，
execute_code 的 code 为 null 时在日志切片处就 None[:80] -> TypeError；
现在分发处统一把 None 归一化为空串。不实例化 StagedAgent.__init__
（避免 Config 校验 API Key），只测 _dispatch_tool 本身。
"""

import tools as T
from agent import StagedAgent
from simulated_user import SimulatedUser


def _bare_agent():
    ag = object.__new__(StagedAgent)
    ag.workspace = T.Workspace()
    ag.logs = []
    ag.verbose = False
    ag.stage = "implementation"
    ag.interactive = False
    ag.sim_user = SimulatedUser()
    return ag


def test_write_file_null_content_coerced_to_empty_string():
    ag = _bare_agent()
    res = ag._dispatch_tool("write_file", {"path": "a.py", "content": None})
    assert "已写入文件 a.py" in res
    assert ag.workspace.files["a.py"] == ""


def test_execute_code_null_code_coerced_to_empty_string():
    ag = _bare_agent()
    res = ag._dispatch_tool("execute_code", {"code": None})
    assert isinstance(res, str)
    assert "退出码: 0" in res


def test_write_file_normal_content_unchanged():
    ag = _bare_agent()
    res = ag._dispatch_tool(
        "write_file", {"path": "a.py", "content": "print('hi')\n"})
    assert "已写入文件 a.py" in res
    assert ag.workspace.files["a.py"] == "print('hi')\n"
