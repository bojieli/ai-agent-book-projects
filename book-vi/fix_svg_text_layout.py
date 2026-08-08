#!/usr/bin/env python3
"""Repair and validate Vietnamese text layout in the book's SVG diagrams.

The Vietnamese labels are usually wider than their Chinese counterparts.  This
tool restores the original type sizes and wraps labels with SVG ``tspan``
elements.  It deliberately does not use ``textLength`` because librsvg squeezes
the glyphs, making the PDF hard to read.

Usage:
    python3 fix_svg_text_layout.py --write
    python3 fix_svg_text_layout.py --check
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
NUM = re.compile(r"-?\d+(?:\.\d+)?")
FONT_SIZE_DECL = re.compile(r"font-size\s*:\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
MIN_FONT = 10.0
LINE_HEIGHT = 1.18

# Undo lossy substitutions made by the previous fitter.  Keeping this table
# also makes --write able to repair SVGs that were already processed by it.
RESTORE_TEXT = {
    '"Kết quả chưa đủ; tìm thêm"': '"Đang phân tích kết quả tìm kiếm... Thông tin chưa đầy đủ, cần tìm kiếm thêm"',
    "Lặp tiếp": "Tiếp tục chu kỳ",
    "Tìm mã → định vị bug → sửa tệp → chạy test → sửa lại → test đạt → xong":
        "Tìm kiếm mã → Xác định vị trí bug → Chỉnh sửa tệp → Chạy kiểm tra → "
        "Sửa lỗi → Chỉnh sửa lại → Kiểm tra đạt → Hoàn thành",
    "(5 vòng, 12 tool calls)": "(Lặp lại 5 lần, gọi công cụ 12 lần)",
    "③ Không gọi tool": "③ Trở về mà không gọi công cụ",
    "⑤ Quá giới hạn lỗi": "⑤ Số lỗi vượt quá giới hạn",
    "① Attention weight của query “How”":
        '① Trọng số chú ý của “How” đối với từng từ trong văn bản trước',
    "Query–Key score → softmax weight → weighted Value (chủ yếu “weather”)":
        "Điểm Query–Key → chuẩn hóa trọng số → tổng có trọng số của Value "
        "(chủ yếu tham chiếu đến “Thời tiết”)",
    "② Causal attention heatmap: chỉ nhìn token hiện tại và quá khứ":
        "② Bản đồ nhiệt chú ý nhân quả: mỗi từ chỉ nhìn thấy chính nó và văn bản trước đó",
    "Đậm hơn = chú ý cao; tam giác trên = token tương lai bị ẩn":
        "Ô càng đậm = chú ý càng cao; tam giác phía trên trống = không thấy từ chưa được tạo",
    "No status bar": "Không có thanh trạng thái",
    "With status bar": "Có thanh trạng thái",
    '"Negotiate Xfinity"': '"Liên hệ Xfinity để thương lượng giá"',
    "Result: 45m wait, no answer": "Kết quả: Đợi 45 phút, không kết nối",
    "Result: lots of search text...": "Kết quả: [Rất nhiều nội dung tìm kiếm...]",
    "Result: connected, $65/mo": "Kết quả: Đã kết nối, báo giá $65/tháng",
    "Result: confirmed $59/mo": "Kết quả: Xác nhận giảm giá xuống $59/tháng",
    '"Call again to follow up?"': '"Có thể gọi lại để nhắc họ không?"',
    "→ Model must scan context to count calls":
        "→ Mô hình phải quét toàn bộ ngữ cảnh để đếm số cuộc gọi",
    "Easy to miscount calls.": "Việc đếm số cuộc gọi rất dễ sai.",
    "[same trajectory]": "[Cùng nội dung trajectory]",
    "phone_call called 3 times (Xfinity: 3)": "phone_call đã được gọi 3 lần (Xfinity: 3)",
    "Constraint: limit reached (3/3) ✗": "Kiểm tra ràng buộc: Đã đạt giới hạn (3/3) ✗",
    "TODO: [✓] contact Xfinity [✓] confirm discount":
        "TODO: [✓] Liên hệ Xfinity [✓] Xác nhận giảm giá",
    "Time: 2025-09-14 10:30": "Thời gian hiện tại: 2025-09-14 10:30",
    "State: waiting for user confirmation":
        "Trạng thái hiện tại: Đang chờ người dùng xác nhận",
    "→ Model reads distilled state directly": "→ Mô hình đọc trực tiếp trạng thái đã cô đọng",
    "Follows constraints; no extra call":
        "Tuân thủ chính xác ràng buộc và không gọi thêm",
    "Tokens": "Số Token",
    "Compress": "Tỷ lệ nén",
    "Iter.": "Số lần lặp",
    "Result": "Kết quả",
    "Token usage comparison": "Trực quan hóa so sánh mức sử dụng Token",
    "individual summary": "tóm tắt riêng lẻ",
    "portfolio summary": "tóm tắt tổng hợp",
    "context-aware": "nhận biết ngữ cảnh",
    "aware + refs": "nhận biết + tham chiếu",
    "adaptive window": "cửa sổ thích ứng",
    "Context-aware compression: 77% fewer tokens, highest success, fewest iterations":
        "Nén theo ngữ cảnh: giảm 77% token, tỷ lệ thành công cao nhất, số lần lặp thấp nhất",
    "Key: include query intent and existing info in compression decisions":
        "Điểm mấu chốt: kết hợp ý định truy vấn và thông tin hiện có khi quyết định nén",
    '"Who to invite?"': '"Mời ai?"',
    "09:00 opens": "09:00 mở cửa",
}

# fig2-9 had previously been replaced wholesale with English labels.
FIG2_9_TEXTS = [
    "Cấp API (góc nhìn nhà phát triển)", "{", '"role"', ":", '"system"', ",",
    '"content"', ":", '"Bạn là một trợ lý"', "}", "{", '"role"', ":", '"user"',
    ",", '"content"', ":", '"Xin chào"', "}", "Cấp mô hình (sau Chat Template)",
    "<|im_start|>", "system", "Bạn là một trợ lý", "<|im_end|>", "<|im_start|>",
    "user", "Xin chào", "<|im_end|>", "<|im_start|>", "assistant",
    "(mô hình tạo nội dung từ đây)",
]


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def number(value, default=None):
    if value is None:
        return default
    match = NUM.search(str(value))
    return float(match.group()) if match else default


def fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def text_nodes(root):
    return [node for node in root.iter() if local(node.tag) == "text"]


def css_font_sizes(root):
    """Return ``.class`` → font-size mappings from SVG ``<style>`` blocks.

    Recent diagrams use semantic CSS classes (for example ``class="heading"``)
    instead of repeating a ``font-size`` attribute on every text node.  The
    preflight must inspect the *effective* typography, otherwise those valid
    diagrams look like they have a zero-sized font.
    """
    sizes = {}
    for node in root.iter():
        if local(node.tag) != "style":
            continue
        stylesheet = "".join(node.itertext())
        for selector, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", stylesheet):
            match = FONT_SIZE_DECL.search(declarations)
            if not match:
                continue
            size = float(match.group(1))
            for token in selector.split(","):
                token = token.strip()
                if token.startswith("."):
                    # Keep only the simple class portion; selectors in the
                    # book's SVGs are intentionally small and class-based.
                    class_name = re.match(r"\.([A-Za-z_][\w-]*)", token)
                    if class_name:
                        sizes[class_name.group(1)] = size
    return sizes


def effective_font_size(node, root, class_sizes=None):
    """Read a text node's effective font size, including CSS class rules."""
    direct = node.get("font-size")
    if direct is not None:
        return number(direct, 0.0)
    inline = FONT_SIZE_DECL.search(node.get("style", ""))
    if inline:
        return float(inline.group(1))
    class_sizes = class_sizes if class_sizes is not None else css_font_sizes(root)
    for class_name in node.get("class", "").split():
        if class_name in class_sizes:
            return class_sizes[class_name]
    return 0.0


def text_of(node) -> str:
    tspans = [child for child in node if local(child.tag) == "tspan"]
    if tspans:
        return " ".join("".join(child.itertext()).strip() for child in tspans).strip()
    return "".join(node.itertext()).strip()


def replace_text(node, value: str) -> None:
    for child in list(node):
        node.remove(child)
    node.text = value


def char_weight(char: str) -> float:
    if char.isspace():
        return 0.31
    if char in "·.,:;|/\\()[]{}'\"-–—_+$→←✓✗<>":
        return 0.38
    if ord(char) > 0x2E7F:
        return 0.95
    if char.isupper():
        return 0.64
    return 0.54


def estimated_width(value: str, font_size: float) -> float:
    # A small safety factor tracks librsvg/Pango more closely for Vietnamese
    # diacritics and avoids lines that technically fit but touch the border.
    return sum(char_weight(char) for char in value) * font_size * 1.08


def viewbox(root):
    values = [float(value) for value in NUM.findall(root.get("viewBox", ""))]
    if len(values) == 4:
        return values
    return [
        0.0,
        0.0,
        number(root.get("width"), 1000.0),
        number(root.get("height"), 600.0),
    ]


def shapes(root):
    result = []
    for node in root.iter():
        kind = local(node.tag)
        if kind == "rect":
            x = number(node.get("x"), 0.0)
            y = number(node.get("y"), 0.0)
            width = number(node.get("width"), 0.0)
            height = number(node.get("height"), 0.0)
            if width >= 18 and height >= 10:
                result.append(("rect", x, y, width, height, width * height))
        elif kind == "circle":
            cx = number(node.get("cx"), 0.0)
            cy = number(node.get("cy"), 0.0)
            radius = number(node.get("r"), 0.0)
            if radius >= 10:
                result.append((
                    "circle", cx - radius, cy - radius, 2 * radius, 2 * radius,
                    math.pi * radius * radius,
                ))
    return result


def containing_shape(all_shapes, x: float, y: float):
    candidates = []
    for shape in all_shapes:
        _, sx, sy, width, height, _ = shape
        if sx - 2 <= x <= sx + width + 2 and sy - 2 <= y <= sy + height + 2:
            candidates.append(shape)
    return min(candidates, key=lambda item: item[5]) if candidates else None


def same_row_regions(root, all_shapes):
    """Return horizontal limits inferred from neighbouring labels on each row."""
    nodes = text_nodes(root)
    result = {}
    buckets = {}
    for node in nodes:
        x = number(node.get("x"), 0.0)
        y = number(node.get("y"), 0.0)
        shape = containing_shape(all_shapes, x, y)
        key = (id(shape), round(y / 3.0))
        buckets.setdefault(key, []).append((x, node, shape))

    for row in buckets.values():
        row.sort(key=lambda item: item[0])
        for index, (x, node, shape) in enumerate(row):
            if not shape:
                continue
            _, sx, _, width, _, _ = shape
            anchor = node.get("text-anchor", "start")
            previous_x = row[index - 1][0] if index else sx
            next_x = row[index + 1][0] if index + 1 < len(row) else sx + width
            if anchor == "middle":
                left = (previous_x + x) / 2 if index else sx
                right = (x + next_x) / 2 if index + 1 < len(row) else sx + width
            elif anchor == "end":
                left, right = previous_x, x
            else:
                left, right = x, next_x
            result[id(node)] = (left + 5, right - 5)
    return result


def available_width(node, shape, row_regions, root) -> float:
    x = number(node.get("x"), 0.0)
    if id(node) in row_regions:
        left, right = row_regions[id(node)]
        # Ignore a neighbour boundary when it would describe only a short bold
        # prefix followed by its body; that prefix legitimately owns its width.
        return max(8.0, right - left)
    if shape:
        kind, sx, sy, width, height, _ = shape
        pad = min(10.0, max(4.0, width * 0.04))
        if kind == "circle":
            cy = sy + height / 2
            radius = width / 2
            dy = abs(number(node.get("y"), cy) - cy)
            chord = 2 * math.sqrt(max(0.0, radius * radius - dy * dy))
            return max(8.0, chord - 2 * pad)
        return max(8.0, width - 2 * pad)
    vx, _, width, _ = viewbox(root)
    anchor = node.get("text-anchor", "start")
    if anchor == "middle":
        return max(8.0, 2 * min(x - vx, vx + width - x) - 10)
    if anchor == "end":
        return max(8.0, x - vx - 8)
    return max(8.0, vx + width - x - 8)


def wrap_words(value: str, font_size: float, width: float):
    words = value.split()
    if len(words) < 2 or estimated_width(value, font_size) <= width:
        return [value]
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if current and estimated_width(candidate, font_size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def restore_source_typography(source_root, target_root):
    source = text_nodes(source_root)
    target = text_nodes(target_root)
    if len(source) != len(target):
        raise ValueError(f"text-node mismatch: source={len(source)}, target={len(target)}")
    for source_node, target_node in zip(source, target):
        if source_node.get("font-size"):
            target_node.set("font-size", source_node.get("font-size"))
        target_node.attrib.pop("textLength", None)
        target_node.attrib.pop("lengthAdjust", None)


def restore_content(name: str, root):
    changed = 0
    for node in text_nodes(root):
        value = text_of(node)
        if value in RESTORE_TEXT:
            replace_text(node, RESTORE_TEXT[value])
            changed += 1
    if name == "fig2-9.svg":
        nodes = text_nodes(root)
        if len(nodes) != len(FIG2_9_TEXTS):
            raise ValueError("fig2-9.svg text-node count changed")
        for node, value in zip(nodes, FIG2_9_TEXTS):
            if text_of(node) != value:
                replace_text(node, value)
                changed += 1
    return changed


def apply_figure_overrides(name: str, root):
    """Fix regions whose flat SVG structure cannot express their layout."""
    changed = 0
    if name == "fig10-13.svg" and root.get("viewBox") != "0 40 780 690":
        # Give both dense lower panels enough vertical space for wrapped text.
        for node in root.iter():
            kind = local(node.tag)
            y_attr = "y" if kind in {"rect", "text"} else None
            if not y_attr:
                continue
            y = number(node.get(y_attr))
            if y is None:
                continue
            if kind == "rect" and abs(y - 355) < 1:
                node.set("height", "150")
                changed += 1
            elif y >= 468:
                node.set(y_attr, fmt(y + 65))
                if kind == "rect" and abs(y - 468) < 1:
                    node.set("height", "155")
                changed += 1
        root.set("viewBox", "0 40 780 690")
        root.set("height", "690")
    return changed


def fit_root(root):
    all_shapes = shapes(root)
    row_regions = same_row_regions(root, all_shapes)
    changed = 0
    for node in text_nodes(root):
        value = text_of(node)
        if not value:
            continue
        # Clear old tspans before calculating the new layout.
        replace_text(node, value)
        node.attrib.pop("textLength", None)
        node.attrib.pop("lengthAdjust", None)
        font_size = max(MIN_FONT, number(node.get("font-size"), 12.0))
        node.set("font-size", fmt(font_size))
        x = number(node.get("x"), 0.0)
        y = number(node.get("y"), 0.0)
        shape = containing_shape(all_shapes, x, y)
        width = available_width(node, shape, row_regions, root)
        lines = wrap_words(value, font_size, width)
        # A very long unbreakable code token is the only case where modest
        # shrinking is preferable to clipping.
        longest = max(estimated_width(line, font_size) for line in lines)
        if longest > width:
            font_size = max(MIN_FONT, font_size * width / longest * 0.98)
            node.set("font-size", fmt(font_size))
            lines = wrap_words(value, font_size, width)
        if len(lines) == 1:
            node.text = lines[0]
            continue
        node.text = None
        line_step = font_size * LINE_HEIGHT
        first_dy = -line_step * (len(lines) - 1) / 2
        for index, line in enumerate(lines):
            tspan = ET.SubElement(node, f"{{{SVG_NS}}}tspan")
            tspan.set("x", fmt(x))
            tspan.set("dy", fmt(first_dy if index == 0 else line_step))
            tspan.text = line
        changed += 1
    reflow_wrapped_shapes(root)
    ensure_viewbox_contains_shapes(root)
    return changed


def ensure_viewbox_contains_shapes(root):
    vx, vy, width, height = viewbox(root)
    right = vx + width
    bottom = vy + height
    for shape in shapes(root):
        _, x, y, shape_width, shape_height, _ = shape
        right = max(right, x + shape_width + 4)
        bottom = max(bottom, y + shape_height + 4)
    new_width = right - vx
    new_height = bottom - vy
    if new_width > width + 0.1 or new_height > height + 0.1:
        root.set("viewBox", f"{fmt(vx)} {fmt(vy)} {fmt(new_width)} {fmt(new_height)}")
        if root.get("width"):
            root.set("width", fmt(new_width))
        if root.get("height"):
            root.set("height", fmt(new_height))


def reflow_wrapped_shapes(root):
    """Lay wrapped labels out as columns so adjacent rows cannot collide."""
    all_shapes = shapes(root)
    grouped = {}
    for node in text_nodes(root):
        x = number(node.get("x"), 0.0)
        y = number(node.get("y"), 0.0)
        shape = containing_shape(all_shapes, x, y)
        if shape:
            grouped.setdefault(shape, []).append(node)

    for shape, nodes in grouped.items():
        if not any(any(local(child.tag) == "tspan" for child in node) for node in nodes):
            continue
        _, sx, sy, width, height, _ = shape
        ordered_x = sorted({number(node.get("x"), 0.0) for node in nodes})
        split_points = [
            (left + right) / 2
            for left, right in zip(ordered_x, ordered_x[1:])
            if right - left > width * 0.22
        ]
        columns = [[] for _ in range(len(split_points) + 1)]
        for node in nodes:
            x = number(node.get("x"), 0.0)
            column = sum(x > point for point in split_points)
            columns[column].append(node)

        for column_nodes in columns:
            column_nodes.sort(key=lambda node: (
                number(node.get("y"), 0.0), number(node.get("x"), 0.0)
            ))
            rows = []
            for node in column_nodes:
                tspans = [child for child in node if local(child.tag) == "tspan"]
                lines = tspans if tspans else [node]
                font_size = number(node.get("font-size"), 12.0)
                for line in lines:
                    rows.append((node, line, font_size))
            if not rows:
                continue
            line_heights = [font_size * 1.08 for _, _, font_size in rows]
            total_height = sum(line_heights)
            usable_height = max(1.0, height - 10)
            if total_height > usable_height:
                scale = usable_height / total_height
                for node in column_nodes:
                    old_size = number(node.get("font-size"), 12.0)
                    node.set("font-size", fmt(max(MIN_FONT, old_size * scale)))
                line_heights = [
                    number(node.get("font-size"), font_size) * 1.08
                    for node, _, font_size in rows
                ]
                total_height = sum(line_heights)
            cursor = sy + (height - total_height) / 2
            seen = set()
            for (node, line, _), line_height in zip(rows, line_heights):
                baseline = cursor + line_height / 2
                if line is node:
                    node.set("y", fmt(baseline))
                else:
                    if id(node) not in seen:
                        node.set("y", "0")
                        line.set("dy", fmt(baseline))
                        seen.add(id(node))
                    else:
                        line.set("dy", fmt(line_height))
                cursor += line_height


def validate_file(path: Path):
    errors = []
    root = ET.parse(path).getroot()
    class_sizes = css_font_sizes(root)
    all_shapes = shapes(root)
    row_regions = same_row_regions(root, all_shapes)
    for index, node in enumerate(text_nodes(root)):
        value = text_of(node)
        if node.get("textLength") or node.get("lengthAdjust"):
            errors.append(f"text #{index}: forbidden textLength/lengthAdjust")
        font_size = effective_font_size(node, root, class_sizes)
        if value and font_size < MIN_FONT:
            errors.append(f"text #{index}: font-size {font_size:g} < {MIN_FONT:g}")
        x = number(node.get("x"), 0.0)
        y = number(node.get("y"), 0.0)
        shape = containing_shape(all_shapes, x, y)
        width = available_width(node, shape, row_regions, root)
        tspans = [child for child in node if local(child.tag) == "tspan"]
        lines = ["".join(child.itertext()).strip() for child in tspans] if tspans else [value]
        for line in lines:
            shape_width = shape[3] - 8 if shape else width
            if (
                " " not in line
                and estimated_width(line, font_size) > width * 1.12
                and estimated_width(line, font_size) > shape_width * 1.12
            ):
                errors.append(f"text #{index}: unbreakable token exceeds its region")
                break
    return errors


def render_check(files):
    errors = []
    with tempfile.TemporaryDirectory(prefix="svg-vi-check-") as directory:
        output = Path(directory) / "preview.png"
        for path in files:
            result = subprocess.run(
                ["rsvg-convert", "-f", "png", "-w", "300", str(path), "-o", str(output)],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                errors.append(f"{path}: rsvg-convert failed: {result.stderr.strip()}")
    return errors


def write_all(files):
    total_wrapped = 0
    total_restored = 0
    for target in files:
        source = Path("../book/images") / target.name
        if not source.exists():
            raise FileNotFoundError(f"missing source SVG: {source}")
        target_root = ET.parse(target).getroot()
        source_root = ET.parse(source).getroot()
        translated = [text_of(node) for node in text_nodes(target_root)]
        source_text = text_nodes(source_root)
        if len(source_text) != len(translated):
            raise ValueError(
                f"{target}: text-node mismatch: "
                f"source={len(source_text)}, target={len(translated)}"
            )
        # Always start from pristine source geometry.  This is what makes the
        # repair idempotent even though wrapped tspans use temporary y/dy values.
        root = source_root
        for node, value in zip(source_text, translated):
            replace_text(node, value)
        total_restored += restore_content(target.name, root)
        apply_figure_overrides(target.name, root)
        total_wrapped += fit_root(root)
        ET.ElementTree(root).write(target, encoding="unicode", xml_declaration=False)
    print(
        f"Updated {len(files)} SVGs: restored {total_restored} labels, "
        f"wrapped {total_wrapped} labels."
    )


def check_all(files):
    failures = []
    for path in files:
        try:
            for error in validate_file(path):
                failures.append(f"{path}: {error}")
        except (ET.ParseError, ValueError) as error:
            failures.append(f"{path}: {error}")
    failures.extend(render_check(files))
    if failures:
        print("Vietnamese SVG preflight failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"Vietnamese SVG preflight passed: {len(files)} files.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="repair SVG files in place")
    mode.add_argument("--check", action="store_true", help="validate without editing files")
    args = parser.parse_args()
    files = sorted(Path("images").glob("*.svg"))
    if not files:
        print("No Vietnamese SVGs found under images/.", file=sys.stderr)
        return 1
    if args.write:
        write_all(files)
    return check_all(files)


if __name__ == "__main__":
    raise SystemExit(main())
