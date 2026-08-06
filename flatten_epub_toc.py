#!/usr/bin/env python3
"""Clean up an EPUB table of contents: strip section numbers from labels
and keep pandoc's nested chapter/section hierarchy in nav.xhtml and toc.ncx."""

import os
import re
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET


XHTML = "http://www.w3.org/1999/xhtml"
EPUB = "http://www.idpf.org/2007/ops"
NCX = "http://www.daisy.org/z3986/2005/ncx/"

ET.register_namespace("", XHTML)
ET.register_namespace("epub", EPUB)


def direct_children(element, tag):
    return [child for child in element if child.tag == tag]


def toc_item(identifier, href, label):
    item = ET.Element(f"{{{XHTML}}}li", {"id": identifier})
    link = ET.SubElement(item, f"{{{XHTML}}}a", {"href": href})
    link.text = label
    return item


def flatten_nav(data, title_label, toc_label, rtl=False):
    root = ET.fromstring(data)
    if rtl:
        root.set("dir", "rtl")
        root.set("{http://www.w3.org/XML/1998/namespace}lang", "ar")
    nav = next(
        element
        for element in root.iter(f"{{{XHTML}}}nav")
        if element.get(f"{{{EPUB}}}type") == "toc"
    )
    top_list = next(child for child in nav if child.tag == f"{{{XHTML}}}ol")

    # 先删掉所有 section-header-number（让目录只显示标题文字，不带 1.1 / 1.1.1 编号）
    # 关键：pandoc 把编号放在 <span class="section-header-number">1.1</span> 里，
    # 标题文字在 span.tail（span 之后的文本节点）。直接 remove(span) 会把 tail 也丢掉，
    # 导致 a 标签变空。所以要先保留 tail 文本。
    for a in root.iter(f"{{{XHTML}}}a"):
        for span in list(a):
            classes = (span.get("class") or "").split()
            if "section-header-number" in classes:
                # 保留 span 后的文本（标题正文）到 a 的 text
                tail_text = (span.tail or "").lstrip()
                if tail_text:
                    if a.text:
                        a.text = a.text + tail_text
                    else:
                        a.text = tail_text
                a.remove(span)

    for group in direct_children(top_list, f"{{{XHTML}}}li"):
        classes = group.get("class", "").split()
        if "chapter-group" not in classes:
            classes.append("chapter-group")
        group.set("class", " ".join(classes))

        # 保留 pandoc 原始的 H2→H3→H4 嵌套结构。
        # 侧边栏靠缩进显示层级。
        for nested_list in direct_children(group, f"{{{XHTML}}}ol"):
            nested_list.set("class", "toc subsections")
            for sub_li in direct_children(nested_list, f"{{{XHTML}}}li"):
                sub_classes = sub_li.get("class", "").split()
                if "subsection" not in sub_classes:
                    sub_classes.append("subsection")
                    sub_li.set("class", " ".join(sub_classes))

    top_list.insert(0, toc_item("toc-li-contents", "nav.xhtml#toc", toc_label))
    top_list.insert(0, toc_item("toc-li-title-page", "text/title_page.xhtml", title_label))
    ET.register_namespace("", XHTML)
    ET.register_namespace("epub", EPUB)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def set_page_progression(data):
    root = ET.fromstring(data)
    namespace = root.tag.partition("}")[0].lstrip("{")
    spine_tag = f"{{{namespace}}}spine" if namespace else "spine"
    spine = root.find(spine_tag)
    if spine is None:
        raise RuntimeError("EPUB package spine not found")
    spine.set("page-progression-direction", "rtl")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def set_xhtml_direction(data):
    root = ET.fromstring(data)
    root.set("dir", "rtl")
    root.set("lang", "ar")
    root.set("{http://www.w3.org/XML/1998/namespace}lang", "ar")
    for name in ("pre", "code", "kbd", "samp"):
        for element in root.iter(f"{{{XHTML}}}{name}"):
            element.set("dir", "ltr")
    ET.register_namespace("", XHTML)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def flatten_ncx(data, title_label, toc_label):
    ET.register_namespace("", NCX)
    root = ET.fromstring(data)
    nav_map = root.find(f"{{{NCX}}}navMap")

    # Apple Books 侧边栏读 toc.ncx（即使 EPUB3 也会回退到 ncx）。
    # 保留 pandoc 完整嵌套层级 + 删掉编号前缀（让侧边栏只显示标题文字）。

    # 1. 找到/补上「扉页」入口
    title_point = None
    for point in direct_children(nav_map, f"{{{NCX}}}navPoint"):
        content = point.find(f"{{{NCX}}}content")
        if content is not None and content.get("src") == "text/title_page.xhtml":
            title_point = point
            label = point.find(f"{{{NCX}}}navLabel/{{{NCX}}}text")
            if label is not None:
                label.text = title_label
            break

    # 2. 删掉每个 navLabel 里的编号前缀（如 "1.1 现代 Agent" → "现代 Agent"）
    for label_text in root.iter(f"{{{NCX}}}text"):
        if label_text.text:
            # 去掉开头的 "1.1.1 " 或 "1.1 " 或 "1 " 这种编号
            label_text.text = re.sub(r'^\d+(\.\d+)*\s+', '', label_text.text)

    # 3. 保留 pandoc 完整嵌套（不删任何 navPoint）

    # 4. 统一按深度优先顺序重排 playOrder。
    # NCX 规范要求 playOrder；缺失或乱序时部分阅读器（如 Apple Books）
    # 会把嵌套层级拍平显示。
    counter = [0]
    def assign_play_order(point):
        counter[0] += 1
        point.set("playOrder", str(counter[0]))
        for child in direct_children(point, f"{{{NCX}}}navPoint"):
            assign_play_order(child)
    for point in direct_children(nav_map, f"{{{NCX}}}navPoint"):
        assign_play_order(point)

    depth = root.find(f".//{{{NCX}}}meta[@name='dtb:depth']")
    if depth is not None:
        depth.set("content", "3")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def rewrite_epub(path, title_label, toc_label, rtl=False):
    replacements = {}
    with zipfile.ZipFile(path) as source:
        names = set(source.namelist())
        if "EPUB/nav.xhtml" not in names or "EPUB/toc.ncx" not in names:
            raise RuntimeError("EPUB navigation files not found")
        replacements["EPUB/nav.xhtml"] = flatten_nav(
            source.read("EPUB/nav.xhtml"), title_label, toc_label, rtl=rtl
        )
        replacements["EPUB/toc.ncx"] = flatten_ncx(
            source.read("EPUB/toc.ncx"), title_label, toc_label
        )
        if rtl:
            package_names = [
                name for name in names if name.endswith(".opf")
            ]
            if len(package_names) != 1:
                raise RuntimeError("Expected exactly one EPUB package document")
            package_name = package_names[0]
            replacements[package_name] = set_page_progression(source.read(package_name))
            for name in names:
                if name.endswith(".xhtml"):
                    replacements[name] = set_xhtml_direction(
                        replacements.get(name, source.read(name))
                    )

        directory = os.path.dirname(os.path.abspath(path))
        descriptor, temporary_path = tempfile.mkstemp(suffix=".epub", dir=directory)
        os.close(descriptor)
        try:
            with zipfile.ZipFile(temporary_path, "w") as target:
                for info in source.infolist():
                    target.writestr(info, replacements.get(info.filename, source.read(info.filename)))
            os.replace(temporary_path, path)
        except BaseException:
            os.unlink(temporary_path)
            raise


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        raise SystemExit(
            f"Usage: {sys.argv[0]} BOOK.epub TITLE_LABEL TOC_LABEL [rtl]"
        )
    rtl = len(sys.argv) == 5 and sys.argv[4].lower() == "rtl"
    rewrite_epub(sys.argv[1], sys.argv[2], sys.argv[3], rtl=rtl)
