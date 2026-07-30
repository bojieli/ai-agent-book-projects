#!/usr/bin/env python3
"""整理下载文件夹脚本。

按文件类型将下载文件夹顶层的文件（不递归子目录）移动到对应的分类子文件夹：

    图片 (jpg/png/gif)  -> Images
    文档 (pdf/doc/txt)  -> Documents
    音频 (mp3/wav)      -> Audio
    视频 (mp4/mov)      -> Videos
    压缩包 (zip/rar)    -> Archives
    其余文件            -> Others（含隐藏文件与无扩展名文件）

用法：
    python organize_downloads.py [下载文件夹路径]

不传路径时默认使用 ~/Downloads。整理采用移动（move）方式，原位置不再保留；
目标位置存在同名文件时自动在文件名后追加 _1、_2 等序号，不会覆盖已有文件。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# 类别文件夹名 -> 该类别包含的扩展名（小写、带点）
CATEGORY_EXTENSIONS: dict[str, set[str]] = {
    "Images": {".jpg", ".png", ".gif"},
    "Documents": {".pdf", ".doc", ".txt"},
    "Audio": {".mp3", ".wav"},
    "Videos": {".mp4", ".mov"},
    "Archives": {".zip", ".rar"},
}

# 未匹配到任何类别时使用的默认文件夹名
DEFAULT_CATEGORY = "Others"


def classify(file_path: Path) -> str:
    """根据文件扩展名返回类别文件夹名。

    扩展名匹配不区分大小写；无扩展名（含以 . 开头的隐藏文件）
    或未识别的扩展名一律归入 Others。

    Args:
        file_path: 待分类的文件路径。

    Returns:
        类别文件夹名，如 "Images"、"Documents"、"Others"。
    """
    suffix = file_path.suffix.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if suffix in extensions:
            return category
    return DEFAULT_CATEGORY


def resolve_conflict(dest: Path) -> Path:
    """返回一个不冲突的目标路径。

    若 dest 不存在则原样返回；否则在扩展名之前依次追加
    _1、_2 ... 直到得到不存在的路径，保证不覆盖已有文件。

    Args:
        dest: 期望的目标文件路径。

    Returns:
        实际可用的目标文件路径。
    """
    if not dest.exists():
        return dest
    counter = 1
    while True:
        candidate = dest.with_name(f"{dest.stem}_{counter}{dest.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def organize(folder: Path) -> tuple[dict[str, int], list[str]]:
    """整理 folder 顶层的文件（不递归子目录）。

    遍历 folder 第一层的所有文件，按类别移动到对应的分类子文件夹；
    忽略所有子目录，也跳过脚本自身（防止脚本恰好放在该目录时被移走）。

    Args:
        folder: 待整理的文件夹路径（须已存在且为目录）。

    Returns:
        一个二元组 (moved, errors)：
        - moved: 类别文件夹名 -> 成功移动的文件数；
        - errors: 移动失败的文件错误描述列表。
    """
    moved: dict[str, int] = {}
    errors: list[str] = []
    script_path = Path(__file__).resolve()

    for entry in sorted(folder.iterdir()):
        if not entry.is_file():
            continue  # 忽略子目录，不做递归
        if entry.resolve() == script_path:
            continue  # 不移动脚本自身

        category = classify(entry)
        dest_dir = folder / category
        dest = resolve_conflict(dest_dir / entry.name)

        try:
            dest_dir.mkdir(exist_ok=True)
            shutil.move(str(entry), str(dest))
        except OSError as exc:
            errors.append(f"{entry.name}: {exc}")
            print(f"  [失败] {entry.name}: {exc}", file=sys.stderr)
            continue

        moved[category] = moved.get(category, 0) + 1
        if dest.name != entry.name:
            print(f"  {entry.name} -> {category}/{dest.name}（重命名以避免覆盖）")
        else:
            print(f"  {entry.name} -> {category}/")

    return moved, errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。

    Args:
        argv: 参数列表；为 None 时使用 sys.argv。

    Returns:
        解析结果，folder 字段为下载文件夹路径（默认 ~/Downloads）。
    """
    parser = argparse.ArgumentParser(
        description="按文件类型整理下载文件夹：将顶层文件移动到对应的分类子文件夹。"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=str(Path.home() / "Downloads"),
        help="下载文件夹路径（默认：~/Downloads）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """脚本入口：解析参数、执行整理并打印分类汇总。

    Args:
        argv: 参数列表；为 None 时使用 sys.argv。

    Returns:
        进程退出码：0 表示全部成功；1 表示路径无效；
        2 表示整理完成但存在移动失败的文件。
    """
    args = parse_args(argv)
    folder = Path(args.folder).expanduser()

    if not folder.exists():
        print(f"错误：路径不存在：{folder}", file=sys.stderr)
        return 1
    if not folder.is_dir():
        print(f"错误：不是一个文件夹：{folder}", file=sys.stderr)
        return 1

    print(f"开始整理：{folder}\n")
    moved, errors = organize(folder)

    print("\n整理完成，分类汇总：")
    if moved:
        for category, count in moved.items():
            print(f"  {category}: {count} 个文件")
        print(f"  合计移动 {sum(moved.values())} 个文件")
    else:
        print("  没有需要整理的文件。")

    if errors:
        print(f"\n{len(errors)} 个文件移动失败：", file=sys.stderr)
        for message in errors:
            print(f"  {message}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
