#!/usr/bin/env python3
"""Serve an HTML report visualizing experiment arms from validation/latest.json.

Reads validation/latest.json (next to this script), then serves a report over
HTTP and opens it in the browser. The report shows:
  1. A summary table with task_success / iterations / repeated_tool_calls per arm.
  2. One section per arm showing tool_call_signatures and reasoning_steps,
     with every reasoning step collapsed by default.
"""

import argparse
import html
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_JSON = SCRIPT_DIR / "validation" / "latest.json"


def esc(value):
    return html.escape(str(value))


def fmt(value):
    if value is None:
        return "&mdash;"
    if isinstance(value, bool):
        return str(value)
    return html.escape(str(value))


def status_badge(value):
    if value is True:
        return '<span class="badge ok">&#10003;</span>'
    if value is False:
        return '<span class="badge fail">&#10007;</span>'
    return '<span class="badge na">n/a</span>'


def render_arm_section(arm):
    mode = esc(arm.get("mode", "?"))
    model = esc(arm.get("model", ""))
    provider = esc(arm.get("provider", ""))
    elapsed = arm.get("elapsed_seconds")
    elapsed_s = f"{elapsed:.2f} s" if isinstance(elapsed, (int, float)) else "&mdash;"
    final_answer = arm.get("final_answer")

    parts = [f'<section class="arm" id="arm-{esc(arm.get("mode", "unknown"))}">']
    parts.append(f"<h2>Mode: {mode}</h2>")
    parts.append(
        f'<p class="meta">{provider} / {model} &middot; {elapsed_s} '
        f'&middot; completed={fmt(arm.get("completed"))} '
        f'success={fmt(arm.get("success"))}</p>'
    )

    if final_answer:
        parts.append(
            f'<h3>Final answer</h3><div class="final-answer"><pre>{esc(final_answer)}</pre></div>'
        )

    signatures = arm.get("tool_call_signatures") or []
    parts.append(f"<h3>Tool call signatures ({len(signatures)})</h3>")
    if signatures:
        parts.append('<ol class="signatures">')
        for i, sig in enumerate(signatures, start=1):
            parts.append(
                f'<li><span class="idx">{i}</span>'
                f'<code>{esc(sig)}</code></li>'
            )
        parts.append("</ol>")
    else:
        parts.append("<p class=\"muted\">No tool calls.</p>")

    reasoning = arm.get("reasoning_steps") or []
    parts.append(f"<h3>Reasoning steps ({len(reasoning)})</h3>")
    if reasoning:
        parts.append('<div class="reasoning">')
        for i, step in enumerate(reasoning, start=1):
            if isinstance(step, str):
                body = esc(step)
            else:
                body = esc(json.dumps(step, ensure_ascii=False, indent=2))
            parts.append(
                f"<details class=\"step\">"
                f"<summary>Step {i}</summary>"
                f"<pre>{body}</pre>"
                f"</details>"
            )
        parts.append("</div>")
    else:
        parts.append("<p class=\"muted\">No reasoning steps recorded.</p>")

    parts.append("</section>")
    return "\n".join(parts)


def render(data):
    arms = data.get("arms", [])
    expected = data.get("expected_numbers", [])

    rows = []
    for arm in arms:
        behavior = arm.get("behavior") or {}
        elapsed = arm.get("elapsed_seconds")
        elapsed_s = f"{elapsed:.2f}" if isinstance(elapsed, (int, float)) else "&mdash;"
        rows.append(
            "".join(
                [
                    "<tr>",
                    f'<td class="mode"><a href="#arm-{esc(arm.get("mode", ""))}">{esc(arm.get("mode", "?"))}</a></td>',
                    f"<td>{status_badge(arm.get('task_success'))}</td>",
                    f"<td>{fmt(arm.get('iterations'))}</td>",
                    f"<td>{fmt(arm.get('repeated_tool_calls'))}</td>",
                    f"<td>{fmt(behavior.get('tool_action_count'))}</td>",
                    f"<td>{elapsed_s}</td>",
                    "</tr>",
                ]
            )
        )

    table = (
        "<table>"
        "<thead><tr>"
        "<th>mode</th>"
        "<th>task_success</th>"
        "<th>iterations</th>"
        "<th>repeated_tool_calls</th>"
        "<th>tool actions</th>"
        "<th>elapsed (s)</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )

    sections = "\n".join(render_arm_section(arm) for arm in arms)

    expected_html = ""
    if expected:
        items = "".join(f"<li><code>{esc(n)}</code></li>" for n in expected)
        expected_html = (
            '<h3>Expected numbers</h3>'
            f'<ul class="expected">{items}</ul>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Experiment {esc(data.get('experiment_id', ''))} &mdash; arm comparison</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 1000px; margin: 0 auto; padding: 24px; line-height: 1.55;
         color: #1c2733; background: #fff; }}
  h1, h2, h3 {{ color: #0b3d66; }}
  h2 {{ border-bottom: 2px solid #e3e8ee; padding-bottom: 6px; margin-top: 40px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0 8px; }}
  th, td {{ border: 1px solid #d5dce3; padding: 8px 10px; text-align: left; }}
  th {{ background: #f2f5f8; }}
  tbody tr:nth-child(even) {{ background: #f8fafc; }}
  td.mode a {{ font-weight: 600; color: #0b3d66; }}
  .badge {{ display: inline-block; padding: 1px 8px; border-radius: 10px;
            font-size: 13px; color: #fff; }}
  .badge.ok {{ background: #1a7f37; }}
  .badge.fail {{ background: #c0392b; }}
  .badge.na {{ background: #9aa7b4; }}
  .meta {{ color: #5a6b7b; font-size: 13px; }}
  .final-answer pre {{ background: #f4f6f8; border-left: 4px solid #0b3d66;
         padding: 10px 12px; overflow-x: auto; }}
  .signatures {{ padding-left: 0; list-style: none; }}
  .signatures li {{ display: flex; align-items: baseline; margin: 4px 0; }}
  .signatures .idx {{ display: inline-block; min-width: 26px; color: #9aa7b4;
         font-size: 12px; }}
  .signatures code, .reasoning pre {{ font-family: ui-monospace, SFMono-Regular,
         Menlo, monospace; font-size: 13px; }}
  .reasoning .step {{ margin: 6px 0; border: 1px solid #e3e8ee; border-radius: 6px;
         background: #fafbfc; }}
  .reasoning summary {{ cursor: pointer; padding: 8px 12px; font-weight: 600;
         color: #0b3d66; user-select: none; }}
  .reasoning pre {{ margin: 0; padding: 10px 12px; border-top: 1px solid #e3e8ee;
         white-space: pre-wrap; word-break: break-word; overflow-x: auto; }}
  .muted {{ color: #9aa7b4; }}
  .expected li {{ margin: 2px 0; }}
  .task {{ background: #f2f5f8; border: 1px solid #d5dce3; border-left: 4px solid
         #0b3d66; border-radius: 6px; padding: 12px 16px; margin: 16px 0;
         white-space: pre-wrap; }}
  .task-label {{ font-weight: 700; color: #0b3d66; margin-bottom: 6px; }}
</style>
</head>
<body>
<h1>Experiment {esc(data.get('experiment_id', ''))}</h1>
<p class="meta">source: {esc(data.get('canonical_source', ''))} &middot; created: {esc(data.get('created_at', ''))}</p>
<div class="task"><div class="task-label">Task</div>{esc(data.get('task', ''))}</div>
{expected_html}
<h2>Summary</h2>
{table}
{sections}
</body>
</html>
"""


def serve(data, port):
    import http.server
    import threading
    import webbrowser

    html_body = render(data)
    url = f"http://127.0.0.1:{port}"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/", "/index.html"):
                self.send_error(404)
                return
            body = html_body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            print("[http] %s - %s" % (self.address_string(), fmt % args))

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"Serving on {url}  (Ctrl+C to stop)")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", nargs="?", default=str(DEFAULT_JSON),
                        help="Path to the validation JSON (default: %(default)s)")
    parser.add_argument("-p", "--port", type=int, default=8000,
                        help="Port to serve on (default: 8000)")
    args = parser.parse_args()

    json_file = Path(args.json_path)
    with open(json_file, encoding="utf-8") as fh:
        data = json.load(fh)

    serve(data, args.port)


if __name__ == "__main__":
    main()
