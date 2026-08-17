#!/usr/bin/env python3
"""整理下载文件夹脚本。

按文件类型将下载文件夹根目录下的文件移动到对应的分类子文件夹中：
    - 图片 (jpg/png/gif)    -> Images
    - 文档 (pdf/doc/txt)    -> Documents
    - 音频 (mp3/wav)        -> Audio
    - 视频 (mp4/mov)        -> Videos
    - 压缩包 (zip/rar)      -> Archives
    - 其余类型              -> Others

行为说明：
    - 仅处理下载目录根层的文件，不递归进入已有子目录；
    - 使用移动（move）而非复制，整理后原位置不再保留文件；
    - 保留原文件名，目标位置存在同名文件时自动追加 _1、_2 等后缀，绝不覆盖；
    - 结束后在控制台输出每个类别移动文件数量的汇总。

用法：
    python organize_downloads.py [下载目录路径]
    不传参数时默认使用 ~/Downloads。
"""

import argparse
import shutil
import sys
from pathlib import Path

# 分类规则：子文件夹名 -> 该类别包含的扩展名集合（统一小写比较）
CATEGORY_MAP = {
    "Images": {".jpg", ".png", ".gif"},
    "Documents": {".pdf", ".doc", ".txt"},
    "Audio": {".mp3", ".wav"},
    "Videos": {".mp4", ".mov"},
    "Archives": {".zip", ".rar"},
}

# 未匹配到任何类别的文件归入该文件夹
DEFAULT_CATEGORY = "Others"


def parse_args(argv=None):
    """解析命令行参数。

    Args:
        argv: 命令行参数列表，None 时使用 sys.argv[1:]。

    Returns:
        argparse.Namespace: 包含 downloads_dir（Path 类型）的解析结果。
    """
    parser = argparse.ArgumentParser(
        description="按文件类型整理下载文件夹：将文件移动到对应的分类子文件夹。"
    )
    parser.add_argument(
        "downloads_dir",
        nargs="?",
        default="~/Downloads",
        help="下载文件夹路径，默认为 ~/Downloads",
    )
    args = parser.parse_args(argv)
    args.downloads_dir = Path(args.downloads_dir).expanduser().resolve()
    return args


def get_category(file_path):
    """根据文件扩展名判断其所属类别。

    Args:
        file_path: Path 对象，待分类的文件路径。

    Returns:
        str: 类别对应的子文件夹名；未匹配时返回 DEFAULT_CATEGORY。
    """
    suffix = file_path.suffix.lower()
    for category, extensions in CATEGORY_MAP.items():
        if suffix in extensions:
            return category
    return DEFAULT_CATEGORY


def get_unique_destination(dest_dir, filename):
    """在目标目录中为文件生成不冲突的目标路径。

    若目标目录中已存在同名文件，则在文件名后追加 _1、_2 等序号，
    直到找到未被占用的名称为止，保证不覆盖已有文件。

    Args:
        dest_dir: Path 对象，目标目录。
        filename: str，原始文件名。

    Returns:
        Path: 不冲突的目标文件完整路径。
    """
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def organize(downloads_dir):
    """整理下载目录：将根层文件按类型移动到分类子文件夹。

    Args:
        downloads_dir: Path 对象，待整理的下载目录（必须已存在且为目录）。

    Returns:
        dict: 各类别成功移动的文件数量，键为类别名，值为整数。

    Raises:
        NotADirectoryError: 当给定路径不存在或不是目录时抛出。
    """
    if not downloads_dir.is_dir():
        raise NotADirectoryError(f"路径不存在或不是目录：{downloads_dir}")

    # 初始化计数器，包含所有已知类别与 Others
    counts = {category: 0 for category in CATEGORY_MAP}
    counts[DEFAULT_CATEGORY] = 0

    for entry in sorted(downloads_dir.iterdir()):
        # 只处理根目录这一层的文件，忽略所有子文件夹
        if not entry.is_file():
            continue

        category = get_category(entry)
        dest_dir = downloads_dir / category
        dest_dir.mkdir(exist_ok=True)

        destination = get_unique_destination(dest_dir, entry.name)
        try:
            shutil.move(str(entry), str(destination))
        except OSError as exc:
            # 单个文件移动失败（如权限不足、被占用）不中断整体整理
            print(f"  [警告] 移动失败，已跳过：{entry.name}（{exc}）")
            continue

        counts[category] += 1
        print(f"  {entry.name} -> {category}/{destination.name}")

    return counts


def print_summary(counts):
    """在控制台输出整理结果的汇总信息。

    Args:
        counts: dict，各类别移动的文件数量。
    """
    print("\n===== 整理完成，汇总如下 =====")
    total = 0
    for category, count in counts.items():
        print(f"  {category:<10} 移动 {count} 个文件")
        total += count
    print(f"  {'合计':<10} 移动 {total} 个文件")


def main(argv=None):
    """脚本入口：解析参数、执行整理并输出汇总。

    Args:
        argv: 命令行参数列表，None 时使用 sys.argv[1:]。

    Returns:
        int: 进程退出码，0 表示成功，1 表示目录无效。
    """
    args = parse_args(argv)

    print(f"开始整理目录：{args.downloads_dir}")
    try:
        counts = organize(args.downloads_dir)
    except NotADirectoryError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print_summary(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
