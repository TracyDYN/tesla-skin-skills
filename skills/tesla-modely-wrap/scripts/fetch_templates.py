#!/usr/bin/env python3
"""从 Tesla 官方 custom-wraps 仓库下载车型模板和车辆参考图。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


CATALOG = Path(__file__).resolve().parents[1] / "models.json"


def load_catalog(path: Path) -> dict[str, dict[str, object]]:
    """读取技能随附的官方车型清单。"""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("车型目录为空")
    return data


def download(url: str, destination: Path) -> None:
    """以临时文件接收下载内容，避免留下半个 PNG。"""

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = Request(url, headers={"User-Agent": "tesla-custom-wrap-skill"})
    with urlopen(request, timeout=60) as response:
        partial.write_bytes(response.read())
    partial.replace(destination)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="下载 Tesla 官方 custom-wraps 车型模板")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--dest", type=Path, default=Path("official_custom_wraps"))
    parser.add_argument("--model", action="append", help="车型 slug，可重复；省略则下载全部车型")
    parser.add_argument("--no-vehicle-image", action="store_true", help="只下载模板，不下载车辆参考图")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    catalog = load_catalog(args.catalog)
    models = args.model or sorted(catalog)
    unknown = [model for model in models if model not in catalog]
    if unknown:
        raise ValueError(f"未知车型：{', '.join(unknown)}")
    for model in models:
        entry = catalog[model]
        template_target = args.dest / str(entry["template_path"])
        download(str(entry["template_url"]), template_target)
        print(f"已下载 {model} template.png -> {template_target}")
        if not args.no_vehicle_image:
            image_target = args.dest / str(entry["vehicle_image_path"])
            download(str(entry["vehicle_image_url"]), image_target)
            print(f"已下载 {model} vehicle_image.png -> {image_target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"错误：{error}")
        raise SystemExit(2)
