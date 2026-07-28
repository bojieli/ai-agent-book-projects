"""
五个基础工具中的「非工具库」部分：web_search / read_webpage / code_interpreter。

设计原则（对应补充案例“最小预定义，最大自我进化”）：
- 这里 **不包含任何领域工具**（没有 get_stock_price、没有 get_youtube_transcript ...）。
- Agent 只能靠 web_search 找开源库/API，read_webpage 读文档，
  code_interpreter 在子进程沙箱里真实执行代码来验证方案是否可行。
- 所有输出都基于「真实网络结果 / 真实执行结果」，从而抑制大模型的幻觉。
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 沙箱内 pip install --target 的目标目录：安装的第三方包会持久化到这里，
# 后续被封装的工具在同一个 PYTHONPATH 下也能直接 import 使用。
PROJECT_DIR = Path(__file__).resolve().parent
SANDBOX_PKG_DIR = PROJECT_DIR / ".sandbox_packages"


# --------------------------------------------------------------------------- #
# 工具 1：web_search —— DuckDuckGo（无需 API key）
# --------------------------------------------------------------------------- #
def web_search(query: str, num_results: int = 6) -> dict:
    """
    使用 DuckDuckGo 进行网页搜索（免费、无需 key）。

    实现要点（参考 chapter4/perception-tools 的风格）：
    - 主用 lite.duckduckgo.com（返回更稳定、不易被限流）；
    - 备用 html.duckduckgo.com；
    - 带指数退避重试，DDG 偶发返回 202（限流）时自动重试，避免「网络抖动即失败」。
    """
    query = (query or "").strip()
    if not query:
        return {"success": False, "error": "search query is empty", "results": []}

    try:  # 模型可能传 null 或非数字字符串，兜底为默认值
        num_results = max(1, min(int(num_results or 6), 10))
    except (TypeError, ValueError):
        num_results = 6
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
        )
    }

    last_err = None
    # 两个端点各重试若干次
    for endpoint in ("https://lite.duckduckgo.com/lite/", "https://html.duckduckgo.com/html/"):
        for attempt in range(3):
            try:
                resp = requests.post(
                    endpoint, data={"q": query, "kl": "wt-wt"}, headers=headers, timeout=15
                )
                if resp.status_code == 202:  # DDG 限流信号
                    raise RuntimeError("rate limited (202)")
                resp.raise_for_status()
                results = _parse_ddg(endpoint, resp.text, num_results)
                if results:
                    return {"success": True, "query": query, "count": len(results), "results": results}
                last_err = "no results parsed"
            except Exception as e:  # noqa: BLE001
                last_err = str(e)
            time.sleep(1.5 * (attempt + 1))  # 退避

    return {"success": False, "error": f"search failed: {last_err}", "results": []}


def _parse_ddg(endpoint: str, html: str, num_results: int) -> list:
    """解析 DuckDuckGo 的两种页面结构。"""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    if "html.duckduckgo" in endpoint:
        for div in soup.find_all("div", class_="result")[:num_results]:
            a = div.find("a", class_="result__a")
            if not a:
                continue
            snip = div.find("a", class_="result__snippet")
            results.append(
                {
                    "title": a.get_text(strip=True),
                    "url": a.get("href", ""),
                    "snippet": snip.get_text(strip=True) if snip else "",
                }
            )
    else:  # lite 版：结果是普通 <a href="http...">
        for a in soup.find_all("a"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            if href.startswith("http") and text:
                results.append({"title": text, "url": href, "snippet": ""})
            if len(results) >= num_results:
                break
    return results


# --------------------------------------------------------------------------- #
# 工具 2：read_webpage —— 抓取网页并抽取正文
# --------------------------------------------------------------------------- #
def read_webpage(url: str, max_chars: int = 6000) -> dict:
    """抓取网页并抽取纯文本正文，供 Agent 阅读 README / API 文档。"""
    if not url or not url.startswith(("http://", "https://")):
        return {"success": False, "error": "invalid url"}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        return {"success": False, "error": f"fetch failed: {e}", "url": url}

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    truncated = len(text) > max_chars
    return {
        "success": True,
        "url": url,
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "text": text[:max_chars],
        "truncated": truncated,
    }


# --------------------------------------------------------------------------- #
# 工具 3：code_interpreter —— 子进程沙箱执行 Python
# --------------------------------------------------------------------------- #
def code_interpreter(code: str, pip_install: list | None = None, timeout: int = 60) -> dict:
    """
    在 **独立子进程** 中执行 Python 代码（沙箱），用于验证从网上找到的库 / API。

    - pip_install: 需要先安装的第三方包列表；安装到临时目录 .sandbox_packages（--target），
      不污染系统环境，并通过 PYTHONPATH 让子进程可 import。
    - timeout: 超时强制终止，避免死循环 / 挂起。

    安全边界提醒：这是「演示级」沙箱（仅进程隔离 + 超时），不是安全沙箱。
    生产环境请使用容器 / gVisor / 无网络命名空间等强隔离，并审计要安装的包（供应链风险）。
    """
    SANDBOX_PKG_DIR.mkdir(exist_ok=True)
    logs = []

    # 子进程环境：把沙箱包目录加入 PYTHONPATH（系统 site-packages 仍可用）
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SANDBOX_PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")

    # 1) 按需 pip install --target
    if pip_install:
        for pkg in pip_install:
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--quiet",
                     "--target", str(SANDBOX_PKG_DIR), pkg],
                    capture_output=True, text=True, timeout=180, env=env,
                )
                if r.returncode != 0:
                    logs.append(f"[pip install {pkg}] FAILED: {r.stderr.strip()[-500:]}")
                else:
                    logs.append(f"[pip install {pkg}] ok")
            except Exception as e:  # noqa: BLE001
                logs.append(f"[pip install {pkg}] error: {e}")

    # 2) 执行代码
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=SANDBOX_PKG_DIR) as f:
        f.write(code)
        script = f.name
    try:
        r = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        out = r.stdout[-8000:]
        result = {
            "success": r.returncode == 0,
            "stdout": out,
            "stderr": r.stderr[-4000:],
            "returncode": r.returncode,
            "pip_logs": logs,
        }
        # 提醒模型：跑通但没有任何 print 输出 = 没有拿到真实数据，不能据此作答或封装工具。
        if r.returncode == 0 and not out.strip():
            result["note"] = (
                "代码执行成功但 stdout 为空——你没有打印出任何真实数据。"
                "这不算验证通过：请修改代码，真正调用库并 print 出真实数字。"
            )
        return result
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"timeout after {timeout}s", "pip_logs": logs}
    finally:
        try:
            os.unlink(script)
        except OSError:
            pass


def run_python_snippet(code: str, timeout: int = 60) -> dict:
    """供 tool_manager 复用：在同一沙箱环境执行一段脚本并返回结果（不做 pip）。"""
    return code_interpreter(code, pip_install=None, timeout=timeout)
