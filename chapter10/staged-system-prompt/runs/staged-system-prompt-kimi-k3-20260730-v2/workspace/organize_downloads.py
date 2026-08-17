#!/usr/bin/env python3
"""整理下载文件夹：按文件类型把顶层文件移动到分类子文件夹中。

用法：
    python organize_downloads.py [下载文件夹路径]

不传路径时默认使用 ~/Downloads。分类子文件夹（Images、Documents、Audio、
Videos、Archives、Others）会创建在下载文件夹内部，文件被移动（而非复制）
到对应子文件夹中；同名冲突时自动追加 _1、_2 序号，绝不覆盖已有文件。
"""

import argparse
import shutil
import sys
from pathlib import Path

# 扩展名（小写、不含点）到分类文件夹名的映射
EXTENSION_TO_CATEGORY = {
    "jpg": "Images",
    "png": "Images",
    "gif": "Images",
    "pdf": "Documents",
    "doc": "Documents",
    "txt": "Documents",
    "mp3": "Audio",
    "wav": "Audio",
    "mp4": "Videos",
    "mov": "Videos",
    "zip": "Archives",
    "rar": "Archives",
}

# 无法识别的扩展名（包括无扩展名文件）归入此分类
DEFAULT_CATEGORY = "Others"


def get_category(file_path: Path) -> str:
    """根据文件扩展名返回对应的分类文件夹名。

    扩展名比较不区分大小写；不在映射表中的类型一律归入 Others。
    """
    extension = file_path.suffix.lstrip(".").lower()
    return EXTENSION_TO_CATEGORY.get(extension, DEFAULT_CATEGORY)


def build_unique_destination(category_dir: Path, filename: str) -> Path:
    """在分类文件夹中为文件生成不冲突的目标路径。

    保留原文件名；若同名文件已存在，则在扩展名前依次追加 _1、_2……，
    直到找到不存在的名字为止，保证绝不覆盖已有文件。
    """
    destination = category_dir / filename
    if not destination.exists():
        return destination

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = category_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def organize_downloads(downloads_dir: Path) -> int:
    """整理下载文件夹的顶层文件，返回成功移动的文件数量。

    只处理顶层文件，忽略所有子文件夹（包括脚本创建的分类文件夹）；
    按类型移动到下载文件夹内部的分类子文件夹中，并逐个打印移动情况；
    单个文件移动失败时打印提示并继续处理其余文件。
    """
    moved_count = 0
    # sorted() 会先完整取出目录快照，之后新建分类文件夹不会影响遍历
    for entry in sorted(downloads_dir.iterdir()):
        if not entry.is_file():
            continue

        category_dir = downloads_dir / get_category(entry)
        destination = build_unique_destination(category_dir, entry.name)

        try:
            category_dir.mkdir(exist_ok=True)
            shutil.move(str(entry), str(destination))
        except OSError as exc:
            print(f"跳过 {entry.name}：移动失败（{exc}）")
            continue

        print(f"{entry.name} -> {category_dir.name}/{destination.name}")
        moved_count += 1

    return moved_count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数：可选的下载文件夹路径，默认 ~/Downloads。"""
    parser = argparse.ArgumentParser(
        description="按文件类型整理下载文件夹（只处理顶层文件，移动而非复制）。"
    )
    parser.add_argument(
        "downloads_dir",
        nargs="?",
        default="~/Downloads",
        help="下载文件夹路径（默认：~/Downloads）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """脚本入口：校验目标路径并执行整理，返回进程退出码。"""
    args = parse_args(argv)
    downloads_dir = Path(args.downloads_dir).expanduser()

    if not downloads_dir.is_dir():
        print(f"错误：{downloads_dir} 不是有效的文件夹", file=sys.stderr)
        return 1

    moved_count = organize_downloads(downloads_dir)
    print(f"整理完成，共整理 {moved_count} 个文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
