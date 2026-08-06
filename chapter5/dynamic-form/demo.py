"""实验 5-9：动态表单生成的意图澄清系统（★★）

核心思路
--------
当用户请求缺少关键信息时，Agent 不是逐条追问，而是**动态生成一个自包含的
HTML 表单**（含级联显示逻辑），让用户"一次提交"补全所有澄清点；前端把表单
汇总成 JSON 交回 Agent，Agent 解析后继续任务。

本 demo 分三步验证（不依赖真实浏览器）：
  1) 生成澄清表单 HTML，保存为 generated_form.html；
  2) 用 BeautifulSoup 结构化校验：确实含 出发城市/出发日期/旅行类型(单程,往返)/
     返程日期，且返程字段带"仅往返显示"的级联 JS 逻辑；
  3) 模拟一次用户提交（构造 JSON），喂回 Agent，Agent 解析后打印订票摘要。

两种运行模式（机制完全一致，只是"谁来写表单代码"不同）：
  * 默认（在线）：让 Agent 真实调用 OpenAI 生成表单 HTML，需 OPENAI_API_KEY；
  * --offline   ：不调用 LLM，用内置机票 schema **确定性渲染**级联表单，无需 API Key。
    离线渲染出的表单同样是真实可用、可在浏览器打开、含两类级联逻辑（显示/隐藏 +
    动态更新可选项）的自包含 HTML。

运行:
  python demo.py                       # 在线：Agent 调 OpenAI 生成（需 API Key）
  python demo.py --offline             # 离线：内置 schema 确定性渲染，无需 API Key
  python demo.py --offline --serve     # 离线渲染后启动本地服务，浏览器实时体验级联/提交
  python demo.py --help                # 查看全部参数

环境变量:
  OPENAI_API_KEY   （在线模式必填；未设置时自动回落到 --offline）
  OPENAI_BASE_URL  （可选，切换到兼容 OpenAI 协议的服务）
  MODEL            （可选，默认 gpt-5.6-luna）
"""

import os
import re
import json
import argparse

from bs4 import BeautifulSoup

# openai 仅在线模式需要；离线模式不导入，缺包也能跑（延迟到用时再 import）

# 加载 .env（若存在），方便本地运行
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv 是可选依赖
    pass


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_REQUEST = "我想订一张去北京的机票"


# ---------------------------------------------------------------------------
# 配置（在线模式）
# ---------------------------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _map_to_openrouter_model(model: str) -> str:
    """把直连模型名映射为 OpenRouter 上的 id（非可映射 id 统一兜底到当前廉价旗舰）。"""
    if not model or "/" in model:
        return model or "openai/gpt-5.6-luna"
    m = model.lower()
    if m.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai/" + model
    if m.startswith("claude"):
        if "haiku" in m:
            return "anthropic/claude-haiku-4.5"
        if "sonnet" in m:
            return "anthropic/claude-sonnet-4.6"
        return "anthropic/claude-opus-4.8"
    if m.startswith("gemini"):
        return "google/" + model
    return "openai/gpt-5.6-luna"


def build_client_and_model(model_override=None):
    """构造 OpenAI 客户端与模型名，含通用 OpenRouter 兜底。"""
    from openai import OpenAI  # 延迟导入：离线模式无需安装/配置 openai

    model = model_override or os.getenv("MODEL", "gpt-5.6-luna")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    orkey = os.getenv("OPENROUTER_API_KEY")
    # 无直连 key，或默认 gpt-5.x（直连需组织实名认证）时改走 OpenRouter。
    prefer_or = bool(orkey) and (model or "").lower().startswith("gpt-5")
    if prefer_or or (not api_key and orkey):
        api_key, base_url, model = orkey, OPENROUTER_BASE_URL, _map_to_openrouter_model(model)
    if not api_key:
        raise SystemExit("未找到 OPENAI_API_KEY（或 OPENROUTER_API_KEY 兜底），请先在环境变量或 .env 中设置，或改用 --offline。")

    client = (
        OpenAI(api_key=api_key, base_url=base_url)
        if base_url
        else OpenAI(api_key=api_key)
    )
    return client, model


def _temp_for(model):
    """推理模型（gpt-5 / o 系列等）不接受 temperature=0。"""
    return (1 if any(k in (model or "").lower()
                     for k in ("gpt-5", "o1", "o3", "o4", "thinking", "reasoner", "kimi-k3"))
            else 0)


# ---------------------------------------------------------------------------
# 步骤 1（在线）：让 Agent 生成澄清表单
# ---------------------------------------------------------------------------
FORM_SYSTEM_PROMPT = """你是一个"意图澄清"助手。用户会给出一个信息不完整的请求，
你的任务不是直接追问，而是**生成一个自包含的 HTML 表单**，让用户一次性补全所有
缺失信息。

严格要求（订机票场景）：
1. 表单必须包含以下字段，字段的 name 属性必须使用给定的英文标识：
   - 出发城市：文本输入框，name="departure_city"
   - 出发日期：日期选择器 <input type="date">，name="departure_date"
   - 旅行类型：单选按钮 <input type="radio" name="trip_type">，两个选项
     value="one_way"（单程）和 value="round_trip"（往返）
   - 返程日期：日期选择器，name="return_date"，放在 id="return_date_field" 的
     容器里
2. **级联逻辑（关键）**：返程日期字段默认隐藏，只有当旅行类型选择"往返"
   (round_trip) 时才通过 JavaScript 显示出来；选回"单程"时再次隐藏。
3. 提交时用 JavaScript 阻止默认提交，把所有字段汇总为一个 JSON 对象，
   key 使用上面的英文 name，并显示在 id="result" 的元素里
   （例如 <pre id="result"></pre>）。
4. 输出必须是**完整、自包含**的 HTML（含 <style> 和 <script>，内联，不引用外部
   资源），可直接保存为 .html 文件在浏览器打开。

只输出 HTML 代码本身，不要任何解释文字，不要用 markdown 代码块包裹。"""


def generate_form(client, model, user_request):
    """调用模型生成澄清表单的 HTML。"""
    resp = client.chat.completions.create(
        model=model,
        temperature=_temp_for(model),
        messages=[
            {"role": "system", "content": FORM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"用户请求：{user_request}\n请为其中缺失的信息生成澄清表单。",
            },
        ],
    )
    html = resp.choices[0].message.content.strip()
    # 模型偶尔会用 ```html ... ``` 包裹，稳妥起见剥掉围栏
    html = re.sub(r"^```(?:html)?\s*", "", html)
    html = re.sub(r"\s*```$", "", html)
    return html.strip()


# ---------------------------------------------------------------------------
# 步骤 1（离线）：内置机票 schema + 确定性级联表单渲染器
# ---------------------------------------------------------------------------
# schema 用声明式方式描述澄清点，渲染器把它变成自包含的级联 HTML。
# 支持两类"级联"：
#   show_when   —— 某字段仅当另一字段等于某值时才显示（返程日期 = 仅往返显示）；
#   options_when —— 某下拉框的可选项随另一字段的取值动态更新（行李额度 = 随舱位变化）。
FLIGHT_FORM_SCHEMA = {
    "title": "机票预订 · 意图澄清表单",
    "fields": [
        {
            "name": "departure_city",
            "label": "出发城市",
            "type": "text",
            "placeholder": "如：上海",
            "required": True,
        },
        {
            "name": "departure_date",
            "label": "出发日期",
            "type": "date",
            "required": True,
        },
        {
            "name": "trip_type",
            "label": "旅行类型",
            "type": "radio",
            "default": "one_way",
            "options": [
                {"value": "one_way", "label": "单程"},
                {"value": "round_trip", "label": "往返"},
            ],
        },
        {
            "name": "return_date",
            "label": "返程日期",
            "type": "date",
            "container_id": "return_date_field",
            # 级联①：仅当 trip_type == round_trip 时显示
            "show_when": {"field": "trip_type", "equals": "round_trip"},
        },
        {
            "name": "cabin_class",
            "label": "舱位",
            "type": "select",
            "default": "economy",
            "options": [
                {"value": "economy", "label": "经济舱"},
                {"value": "business", "label": "公务舱"},
                {"value": "first", "label": "头等舱"},
            ],
        },
        {
            "name": "baggage_count",
            "label": "免费托运行李额度",
            "type": "select",
            # 级联②：可选项随舱位（cabin_class）动态变化
            "options_when": {
                "field": "cabin_class",
                "map": {
                    "economy": [
                        {"value": "0", "label": "仅手提行李"},
                        {"value": "1", "label": "1 件（≤23kg）"},
                    ],
                    "business": [
                        {"value": "0", "label": "仅手提行李"},
                        {"value": "1", "label": "1 件（≤32kg）"},
                        {"value": "2", "label": "2 件（≤32kg）"},
                    ],
                    "first": [
                        {"value": "1", "label": "1 件（≤32kg）"},
                        {"value": "2", "label": "2 件（≤32kg）"},
                        {"value": "3", "label": "3 件（≤32kg）"},
                    ],
                },
            },
        },
    ],
}


def _extract_destination(user_request):
    """从"去XX的机票"里粗抽目的地，作为表单常量随提交一起带回。抽不到就回落 None。"""
    m = re.search(r"去(.+?)(?:的?(?:单程|往返))?的?(?:机票|航班|票)", user_request)
    if m:
        return m.group(1).strip()
    return None


def _render_field_html(f):
    """把单个字段 schema 渲染成 HTML 片段。"""
    ftype = f["type"]
    name = f["name"]
    label = f.get("label", "")
    required = " required" if f.get("required") else ""

    if ftype in ("text", "date"):
        ph = f' placeholder="{f["placeholder"]}"' if f.get("placeholder") else ""
        inner = (
            f'<label class="fld-label" for="{name}">{label}</label>'
            f'<input class="fld-input" type="{ftype}" id="{name}" name="{name}"{ph}{required}>'
        )
    elif ftype == "radio":
        opts = []
        for o in f["options"]:
            checked = " checked" if f.get("default") == o["value"] else ""
            opts.append(
                f'<label class="radio"><input type="radio" name="{name}" '
                f'value="{o["value"]}"{checked}> {o["label"]}</label>'
            )
        inner = (
            f'<span class="fld-label">{label}</span>'
            f'<div class="radio-row">{"".join(opts)}</div>'
        )
    elif ftype == "select":
        opts = ""
        for o in f.get("options", []):
            selected = " selected" if f.get("default") == o["value"] else ""
            opts += f'<option value="{o["value"]}"{selected}>{o["label"]}</option>'
        inner = (
            f'<label class="fld-label" for="{name}">{label}</label>'
            f'<select class="fld-input" id="{name}" name="{name}">{opts}</select>'
        )
    else:
        raise ValueError(f"未知字段类型：{ftype}")

    container_id = f.get("container_id")
    cid = f' id="{container_id}"' if container_id else ""
    # 带 show_when 的字段默认隐藏，交给 JS 在加载时按当前取值决定是否显示（避免闪现）
    hidden = ' style="display:none"' if f.get("show_when") else ""
    return f'<div class="field"{cid}{hidden}>{inner}</div>'


# 通用级联运行时：读取内联的 FORM_CONFIG，处理 show_when / options_when，
# 并在提交时把"当前可见字段"汇总成 JSON。纯原生 JS，无外部依赖。
_RUNTIME_JS = """
const FORM_CONFIG = __CONFIG__;
const form = document.getElementById('clarify-form');

function valueOf(name) {
  const el = form.elements[name];
  if (!el) return '';
  return el.value || '';
}

function applyCascade() {
  FORM_CONFIG.fields.forEach(function (f) {
    // 级联①：show_when —— 控制字段容器显示/隐藏
    if (f.show_when) {
      const box = document.getElementById(f.container_id);
      if (box) {
        const show = valueOf(f.show_when.field) === f.show_when.equals;
        box.style.display = show ? '' : 'none';
      }
    }
    // 级联②：options_when —— 根据另一字段的取值动态重建下拉可选项
    if (f.options_when) {
      const sel = form.elements[f.name];
      if (sel) {
        const key = valueOf(f.options_when.field);
        const opts = f.options_when.map[key] || [];
        const prev = sel.value;
        sel.innerHTML = '';
        opts.forEach(function (o) {
          const opt = document.createElement('option');
          opt.value = o.value;
          opt.textContent = o.label;
          sel.appendChild(opt);
        });
        if (opts.some(function (o) { return o.value === prev; })) sel.value = prev;
      }
    }
  });
}

form.addEventListener('change', applyCascade);
applyCascade();  // 首次加载即应用一次

form.addEventListener('submit', function (e) {
  e.preventDefault();
  const data = {};
  FORM_CONFIG.fields.forEach(function (f) {
    // 隐藏（未展开）的级联字段不计入提交结果
    if (f.container_id) {
      const box = document.getElementById(f.container_id);
      if (box && box.style.display === 'none') return;
    }
    const v = valueOf(f.name);
    if (v !== '') data[f.name] = v;
  });
  Object.assign(data, FORM_CONFIG.constants || {});
  document.getElementById('result').textContent = JSON.stringify(data, null, 2);
});
"""

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         max-width: 560px; margin: 32px auto; padding: 0 20px; line-height: 1.6; }
  h1 { font-size: 20px; }
  .req { color: #666; font-size: 13px; margin: -6px 0 18px; }
  .field { margin-bottom: 16px; }
  .fld-label { display: block; font-weight: 600; margin-bottom: 6px; }
  .fld-input { width: 100%; box-sizing: border-box; padding: 8px 10px;
               border: 1px solid #bbb; border-radius: 6px; font-size: 15px; }
  .radio-row { display: flex; gap: 18px; }
  .radio { font-weight: normal; }
  button { margin-top: 8px; padding: 10px 18px; font-size: 15px; border: 0;
           border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; }
  #result { background: #f5f5f5; color: #111; padding: 12px; border-radius: 6px;
            white-space: pre-wrap; margin-top: 18px; min-height: 1em; }
</style>
</head>
<body>
<h1>__TITLE__</h1>
<p class="req">原始请求：__REQUEST__ —— 请一次性补全以下信息（返程日期仅在选择"往返"时出现；行李额度随舱位变化）。</p>
<form id="clarify-form">
__FIELDS__
  <button type="submit">提交</button>
</form>
<pre id="result"></pre>
<script>
__SCRIPT__
</script>
</body>
</html>
"""


def render_form_html(schema, user_request):
    """把声明式 schema 确定性渲染成自包含的级联 HTML（离线路径，不调用 LLM）。"""
    fields_html = "\n".join(_render_field_html(f) for f in schema["fields"])

    # 供 JS 运行时使用的精简配置（只保留级联所需的键）
    js_fields = []
    for f in schema["fields"]:
        entry = {"name": f["name"]}
        if f.get("container_id"):
            entry["container_id"] = f["container_id"]
        if f.get("show_when"):
            entry["show_when"] = f["show_when"]
        if f.get("options_when"):
            entry["options_when"] = f["options_when"]
        js_fields.append(entry)

    constants = {}
    dest = _extract_destination(user_request)
    if dest:
        constants["destination_city"] = dest  # 目的地已在原始请求里给出，随提交一起带回
    config = {"fields": js_fields, "constants": constants}

    script = _RUNTIME_JS.replace("__CONFIG__", json.dumps(config, ensure_ascii=False))
    return (
        _PAGE_TEMPLATE.replace("__TITLE__", schema["title"])
        .replace("__REQUEST__", user_request)
        .replace("__FIELDS__", fields_html)
        .replace("__SCRIPT__", script)
    )


# ---------------------------------------------------------------------------
# 步骤 2：结构化校验表单
# ---------------------------------------------------------------------------
def validate_form(html):
    """用 BeautifulSoup + 正则做鲁棒校验。

    由于模型生成的具体标签写法不完全可控，这里采用"关键词/属性匹配"的鲁棒策略：
    只要能定位到语义等价的控件即算通过，并把每一项证据打印出来。
    返回 (是否全部通过, 报告字典, 脚本文本)。
    """
    soup = BeautifulSoup(html, "html.parser")
    report = {}

    # (a) 出发城市：文本输入
    dep_city = soup.find("input", attrs={"name": re.compile("departure_city", re.I)})
    if dep_city is None:
        # 退化匹配：任意与"出发城市"相关的文本框
        dep_city = soup.find(
            "input", attrs={"name": re.compile("depart.*city|from.*city|city", re.I)}
        )
    report["出发城市(文本输入)"] = bool(
        dep_city is not None
        and (dep_city.get("type") in (None, "text"))
    )

    # (b) 出发日期：日期选择器
    dep_date = soup.find(
        "input",
        attrs={"type": "date", "name": re.compile("departure_date|depart.*date", re.I)},
    )
    if dep_date is None:
        dep_date = soup.find("input", attrs={"type": "date"})
    report["出发日期(日期选择器)"] = bool(dep_date is not None)

    # (c) 旅行类型：单选，含 单程/往返
    radios = soup.find_all("input", attrs={"type": "radio"})
    radio_values = {r.get("value", "").lower() for r in radios}
    has_one_way = any("one" in v or "单程" in v for v in radio_values)
    has_round = any("round" in v or "往返" in v for v in radio_values)
    # 也允许通过文本判断
    text_all = html.lower()
    has_one_way = has_one_way or ("单程" in html)
    has_round = has_round or ("往返" in html)
    report["旅行类型(单选:单程)"] = bool(len(radios) >= 2 and has_one_way)
    report["旅行类型(单选:往返)"] = bool(len(radios) >= 2 and has_round)

    # (d) 返程日期：日期选择器
    ret_date = soup.find(
        "input", attrs={"name": re.compile("return_date|return.*date", re.I)}
    )
    report["返程日期(日期选择器)"] = bool(
        ret_date is not None or "return_date" in text_all
    )

    # (e) 级联逻辑：返程字段有"仅往返显示"的 JS toggle
    #     鲁棒判断：脚本里同时出现 (round_trip 或 往返) 与 (显示/隐藏控制) 及
    #     返程字段的引用。
    script_text = " ".join(s.get_text() for s in soup.find_all("script"))
    cond_display = bool(
        re.search(r"round_trip|往返", script_text)
        and re.search(
            r"return_date|return_date_field|returnDate", script_text, re.I
        )
        and re.search(
            r"display|hidden|style|classList|\.hide|\.show|toggle", script_text, re.I
        )
    )
    report["返程字段级联逻辑(仅往返显示)"] = cond_display

    all_pass = all(report.values())
    return all_pass, report, script_text


# ---------------------------------------------------------------------------
# 步骤 3：模拟用户提交，喂回 Agent 继续任务
# ---------------------------------------------------------------------------
PARSE_SYSTEM_PROMPT = """你是订机票助手。用户已经通过澄清表单一次性提交了 JSON 格式
的补全信息。请解析这些信息并给出一段简洁的中文"订票摘要"，确认航段、日期、行程类型。
如果是单程(one_way)则不要提返程；如果是往返(round_trip)则必须包含返程日期。
最后追加一句下一步操作提示（如"正在为您检索航班..."）。只输出摘要文本。"""


def continue_task(client, model, original_request, submitted_json):
    """把用户提交的 JSON 交回 Agent（在线），生成订票摘要。"""
    resp = client.chat.completions.create(
        model=model,
        temperature=_temp_for(model),
        messages=[
            {"role": "system", "content": PARSE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"原始请求：{original_request}\n"
                    f"表单提交的 JSON 数据：\n{json.dumps(submitted_json, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
    )
    return resp.choices[0].message.content.strip()


_CABIN_CN = {"economy": "经济舱", "business": "公务舱", "first": "头等舱"}


def summarize_offline(submitted):
    """离线路径：不调用 LLM，用确定性模板把提交 JSON 解析成订票摘要。

    这一步只是字符串格式化（不是伪造 LLM 输出），用来演示"解析 JSON → 继续任务"
    的闭环；在线模式下这段由 continue_task() 交给模型完成。
    """
    dep = submitted.get("departure_city", "?")
    dest = submitted.get("destination_city", "目的地")
    ddate = submitted.get("departure_date", "?")
    lines = [f"已收到您的订票信息：{dep} → {dest}，出发日期 {ddate}。"]
    if submitted.get("trip_type") == "round_trip":
        lines.append(f"行程类型：往返，返程日期 {submitted.get('return_date', '?')}。")
    else:
        lines.append("行程类型：单程。")
    if submitted.get("cabin_class"):
        cabin = _CABIN_CN.get(submitted["cabin_class"], submitted["cabin_class"])
        bag = submitted.get("baggage_count")
        bag_txt = f"，免费托运 {bag} 件" if bag not in (None, "", "0", 0) else "，无免费托运"
        lines.append(f"舱位：{cabin}{bag_txt}。")
    lines.append("正在为您检索航班...")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 可选：本地起 HTTP 服务，真实体验级联/提交
# ---------------------------------------------------------------------------
def serve_html(path, port):
    """在 path 所在目录起一个本地静态服务，并打开浏览器指向该 HTML。"""
    import http.server
    import socketserver
    import functools
    import webbrowser

    directory = os.path.dirname(os.path.abspath(path))
    fname = os.path.basename(path)
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=directory
    )
    url = f"http://127.0.0.1:{port}/{fname}"
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print("\n" + "=" * 68)
        print(f"本地服务已启动：{url}")
        print("在浏览器里切换 单程/往返 看返程字段级联显示；切换舱位看行李额度动态更新；")
        print("点『提交』在页面底部看到汇总的 JSON。按 Ctrl+C 停止服务。")
        print("=" * 68)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止本地服务。")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def build_arg_parser():
    """构造命令行参数解析器（提供中文 --help）。"""
    parser = argparse.ArgumentParser(
        description="实验 5-9：动态表单生成的意图澄清系统 —— 从一个模糊请求生成含级联逻辑的"
        "自包含 HTML 表单，用户一次提交，Agent 解析 JSON 继续任务。默认走 OpenAI（需 "
        "OPENAI_API_KEY）；加 --offline 用内置 schema 确定性渲染同样的级联表单，无需 API Key。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-r",
        "--request",
        default=USER_REQUEST,
        metavar="TEXT",
        help=f"用户的模糊请求（意图）。默认：{USER_REQUEST}。"
        "（--offline 下渲染的是内置机票 schema，此项主要用于抽取目的地并展示。）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="generated_form.html",
        metavar="PATH",
        help="生成的 HTML 表单输出路径（相对路径按脚本所在目录解析）。默认：generated_form.html。",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="覆盖模型名（否则读环境变量 MODEL，默认 gpt-5.6-luna）。--offline 下忽略此项。",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="离线模式：不调用 LLM，用内置机票 schema 确定性渲染级联表单，无需 API Key。",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="生成后启动本地 HTTP 服务并打开浏览器，真实体验级联显示与提交汇总。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        metavar="N",
        help="--serve 使用的端口（默认 8000）。",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()

    out_path = args.output
    if not os.path.isabs(out_path):
        out_path = os.path.join(SCRIPT_DIR, out_path)

    # 离线判定：显式 --offline，或既无 OPENAI_API_KEY 也无 OPENROUTER_API_KEY 时自动回落
    offline = args.offline
    if not offline and not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")):
        print("未检测到 OPENAI_API_KEY（或 OPENROUTER_API_KEY 兜底），自动切换到离线模式（等价于 --offline）。\n")
        offline = True

    client = model = None
    if offline:
        mode_desc = "离线（内置 schema 确定性渲染，无需 API Key）"
    else:
        client, model = build_client_and_model(args.model)
        mode_desc = f"在线（Agent 调用 OpenAI，模型 {model}）"

    print("=" * 68)
    print(f"用户请求: {args.request}")
    print(f"运行模式: {mode_desc}")
    print("=" * 68)

    # --- 步骤 1：生成表单 ---
    print("\n[步骤 1] 生成澄清表单 HTML ...")
    if offline:
        html = render_form_html(FLIGHT_FORM_SCHEMA, args.request)
    else:
        html = generate_form(client, model, args.request)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  已保存到 {out_path} （共 {len(html)} 字符，可手动在浏览器打开看级联效果）")

    # --- 步骤 2：结构化校验 ---
    print("\n[步骤 2] 结构化校验表单字段与级联逻辑：")
    all_pass, report, script_text = validate_form(html)
    for name, ok in report.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    # 打印级联逻辑证据（脚本中相关片段）
    evidence_lines = [
        ln.strip()
        for ln in script_text.splitlines()
        if re.search(r"round_trip|往返|return_date|display|hidden|toggle|classList", ln, re.I)
    ]
    if evidence_lines:
        print("\n  级联逻辑证据（脚本节选）:")
        for ln in evidence_lines[:8]:
            print(f"    | {ln}")

    if not all_pass:
        print("\n  警告：部分字段校验未通过（模型输出不稳定）。可查看生成的 HTML 排查。")

    # --- 步骤 3：模拟一次提交，Agent 继续任务 ---
    print("\n[步骤 3] 模拟用户一次性提交表单（往返场景）：")
    submitted = {
        "departure_city": "上海",
        "departure_date": "2026-08-01",
        "trip_type": "round_trip",
        "return_date": "2026-08-07",
        "cabin_class": "business",
        "baggage_count": "2",
        # 目的地来自原始请求（北京），一并带上
        "destination_city": _extract_destination(args.request) or "北京",
    }
    print(json.dumps(submitted, ensure_ascii=False, indent=2))

    print("\n[步骤 3] 解析 JSON 并继续任务，输出订票摘要：")
    if offline:
        summary = summarize_offline(submitted)
        note = "（离线确定性模板）"
    else:
        summary = continue_task(client, model, args.request, submitted)
        note = f"（模型 {model}）"
    print("-" * 68)
    print(summary)
    print("-" * 68 + f"  {note}")

    # 结果汇总
    print("\n" + "=" * 68)
    print(f"表单字段/级联校验: {'全部通过' if all_pass else '部分未通过'}")
    print("提交 JSON 解析: 成功（见上方订票摘要）")
    print("=" * 68)

    # --- 可选：本地起服务，真实体验 ---
    if args.serve:
        serve_html(out_path, args.port)


if __name__ == "__main__":
    main()
