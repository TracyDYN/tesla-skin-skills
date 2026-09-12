#!/usr/bin/env python3
"""将生成的图案安全地套入 Tesla 官方车型 UV 模板。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "models.json"
# 仅保留旧版 Premium 命令的兼容默认值；其他车型必须显式传入区域。
LEGACY_PREMIUM_BUMPER = (245, 9, 532, 106)
MAX_NAME_LENGTH = 30
DEFAULT_MAX_BYTES = 1_000_000


def allowed(pixel: tuple[int, int, int, int]) -> bool:
    """官方模板中只有纯白不透明像素可贴图。"""

    return pixel == (255, 255, 255, 255)


def parse_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(item.strip()) for item in value.split(",")]
    if len(parts) != 4 or parts[2] <= 0 or parts[3] <= 0:
        raise argparse.ArgumentTypeError("区域必须是 x,y,width,height 且宽高为正数")
    return tuple(parts)  # type: ignore[return-value]


def parse_color(value: str) -> tuple[int, int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) not in (6, 8) or not re.fullmatch(r"[0-9a-fA-F]+", value):
        raise argparse.ArgumentTypeError("颜色必须是 RRGGBB 或 RRGGBBAA")
    if len(value) == 6:
        value += "FF"
    return tuple(int(value[index : index + 2], 16) for index in range(0, 8, 2))  # type: ignore[return-value]


def load_catalog(path: Path) -> dict[str, dict[str, object]]:
    """读取官方车型目录，并检查每个模板路径和下载地址字段。"""

    catalog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or not catalog:
        raise ValueError("车型目录必须是非空 JSON 对象")
    for slug, entry in catalog.items():
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]+", slug):
            raise ValueError(f"车型 slug 无效：{slug}")
        if not isinstance(entry, dict) or not entry.get("template_path"):
            raise ValueError(f"车型缺少 template_path：{slug}")
    return catalog


def print_models(catalog: dict[str, dict[str, object]]) -> None:
    """以稳定顺序列出官方仓库当前支持的全部车型 slug。"""

    for slug in sorted(catalog):
        entry = catalog[slug]
        print(f"{slug}\t{entry.get('display_name', slug)}\t{entry['template_path']}")


def resolve_template(
    template: Path | None,
    model: str | None,
    template_root: Path | None,
    catalog: dict[str, dict[str, object]],
) -> Path:
    """根据显式路径或官方车型 slug 定位 template.png。"""

    if template is not None:
        return template
    if not model:
        raise ValueError("请提供 --template，或使用 --model 选择官方车型")
    if model not in catalog:
        raise ValueError(f"未知车型 {model}，可用 --list-models 查看目录")
    root = template_root or Path.cwd()
    return root / str(catalog[model]["template_path"])


def model_bumper_box(model: str | None, catalog: dict[str, dict[str, object]]) -> tuple[int, int, int, int] | None:
    """返回目录中明确记录的前保险杠区域，避免把 Premium 坐标误套到其他车型。"""

    if not model or model not in catalog:
        return None
    raw = catalog[model].get("front_bumper_box")
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    return tuple(int(value) for value in raw)  # type: ignore[return-value]


def load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont:
    candidates = []
    if font_path:
        candidates.append(font_path)
    candidates.extend(
        [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise FileNotFoundError("找不到中文字体，请通过 --font 指定字体文件")


def mask_design(template: Image.Image, design: Image.Image) -> Image.Image:
    template = template.convert("RGBA")
    design = design.convert("RGBA")
    if template.size != design.size:
        # imagegen 的中间图有时不是 1024 方图，先缩放到模板尺寸再进入严格 mask。
        design = design.resize(template.size, Image.Resampling.LANCZOS)
    output = template.copy()
    tp = template.load()
    dp = design.load()
    op = output.load()
    for y in range(template.height):
        for x in range(template.width):
            if allowed(tp[x, y]):
                r, g, b, _ = dp[x, y]
                op[x, y] = (r, g, b, 255)
    return output


def rotate_clipped(
    output: Image.Image,
    template: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    """在官方白区内旋转一块图案，避免旋转内容越过模板轮廓。"""

    x0, y0, width, height = box
    if x0 < 0 or y0 < 0 or x0 + width > output.width or y0 + height > output.height:
        raise ValueError("旋转区域超出画布")
    region = output.crop((x0, y0, x0 + width, y0 + height)).transpose(
        Image.Transpose.ROTATE_180
    )
    tp = template.load()
    op = output.load()
    for j in range(height):
        for i in range(width):
            x, y = x0 + i, y0 + j
            if not allowed(tp[x, y]):
                continue
            source_x = x0 + width - 1 - i
            source_y = y0 + height - 1 - j
            if allowed(tp[source_x, source_y]):
                op[x, y] = region.getpixel((i, j))


def draw_name(
    output: Image.Image,
    template: Image.Image,
    name: str,
    box: tuple[int, int, int, int],
    angle: int,
    font_path: str | None,
    font_size: int,
    fill: tuple[int, int, int, int],
    background: tuple[int, int, int, int] | None,
) -> None:
    x, y, width, height = box
    if x < 0 or y < 0 or x + width > output.width or y + height > output.height:
        raise ValueError("名字区域超出画布")
    if background is not None:
        draw = ImageDraw.Draw(output)
        draw.rounded_rectangle((x, y, x + width - 1, y + height - 1), radius=12, fill=background)
    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    font = load_font(font_path, font_size)
    bounds = draw.textbbox((0, 0), name, font=font)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    draw.text(
        ((width - text_width) / 2 - bounds[0], (height - text_height) / 2 - bounds[1]),
        name,
        font=font,
        fill=fill,
    )
    if angle == 180:
        text_layer = text_layer.transpose(Image.Transpose.ROTATE_180)
    output.alpha_composite(text_layer, (x, y))
    # 文字和背景若越界，按官方 mask 截断。
    op = output.load()
    tp = template.load()
    for yy in range(output.height):
        for xx in range(output.width):
            if not allowed(tp[xx, yy]):
                op[xx, yy] = tp[xx, yy]


def quantize_editable(output: Image.Image, template: Image.Image, colors: int) -> Image.Image:
    if colors < 2 or colors > 256:
        raise ValueError("--quantize 颜色数必须在 2 到 256 之间")
    quantized = output.convert("RGB").quantize(colors=colors, dither=Image.Dither.NONE).convert("RGBA")
    op = quantized.load()
    tp = template.load()
    for y in range(template.height):
        for x in range(template.width):
            if not allowed(tp[x, y]):
                op[x, y] = tp[x, y]
    return quantized


def validate(template: Image.Image, output: Image.Image) -> tuple[int, int, int, int]:
    protected_diff = 0
    alpha_diff = 0
    protected_count = 0
    editable_count = 0
    tp = template.load()
    op = output.load()
    for y in range(template.height):
        for x in range(template.width):
            source = tp[x, y]
            result = op[x, y]
            if source[3] != result[3]:
                alpha_diff += 1
            if allowed(source):
                editable_count += 1
            else:
                protected_count += 1
                if source != result:
                    protected_diff += 1
    return editable_count, protected_count, protected_diff, alpha_diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="安全地生成 Tesla 官方车型自定义贴膜 PNG")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help="车型目录 JSON")
    parser.add_argument("--list-models", action="store_true", help="列出官方仓库支持的全部车型并退出")
    parser.add_argument("--model", help="官方车型 slug，例如 model3-2024-base")
    parser.add_argument("--template", type=Path, help="官方 template.png；不传时由 --model 和 --template-root 定位")
    parser.add_argument("--template-root", type=Path, help="官方 custom-wraps 仓库根目录")
    parser.add_argument("--design", type=Path, help="已生成的平面图案 PNG")
    parser.add_argument("--output", type=Path, help="输出 PNG，文件名须符合 Tesla 限制")
    parser.add_argument("--rotate-box", type=parse_box, action="append", help="将指定区域旋转 180°，可重复传入")
    parser.add_argument("--rotate-front-bumper", action="store_true", help="将前保险杠区域旋转 180°")
    parser.add_argument("--front-bumper-box", type=parse_box, help="前保险杠区域 x,y,width,height；其他车型需显式提供")
    parser.add_argument("--name", help="需要叠加的精确文字，例如 八月")
    parser.add_argument("--name-box", type=parse_box, default=(414, 31, 212, 58), help="名字区域 x,y,width,height")
    parser.add_argument("--name-angle", type=int, choices=(0, 180), default=0, help="名字旋转角度")
    parser.add_argument("--font", help="中文字体路径")
    parser.add_argument("--font-size", type=int, default=48)
    parser.add_argument("--name-fill", type=parse_color, default=(24, 52, 76, 255))
    parser.add_argument("--name-bg", type=parse_color, help="可选名字背景色")
    parser.add_argument("--quantize", type=int, metavar="COLORS", help="将颜色量化到 2-256 色以压缩文件")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    catalog = load_catalog(args.catalog)
    if args.list_models:
        print_models(catalog)
        return 0
    if args.model and args.model not in catalog:
        raise ValueError(f"未知车型 {args.model}，可用 --list-models 查看目录")
    if not args.design or not args.output:
        raise ValueError("生成文件时必须同时提供 --design 和 --output")
    template_path = resolve_template(args.template, args.model, args.template_root, catalog)
    if args.output.suffix.lower() != ".png":
        raise ValueError("输出文件必须是 .png")
    if len(args.output.name) > MAX_NAME_LENGTH or not re.fullmatch(r"[A-Za-z0-9_]+\.png", args.output.name):
        raise ValueError("输出文件名必须只含英文、数字、下划线，且不超过 30 个字符")
    template = Image.open(template_path).convert("RGBA")
    design = Image.open(args.design).convert("RGBA")
    output = mask_design(template, design)
    rotate_boxes = list(args.rotate_box or [])
    if args.rotate_front_bumper:
        bumper_box = args.front_bumper_box or model_bumper_box(args.model, catalog)
        if bumper_box is None:
            # 保留旧版直接传入 Premium template 的行为，同时避免误套到新车型。
            if args.model is None and args.template is not None:
                bumper_box = LEGACY_PREMIUM_BUMPER
            else:
                raise ValueError("该车型没有预置前保险杠区域，请使用 --front-bumper-box 指定")
        rotate_boxes.append(bumper_box)
    for rotate_box in rotate_boxes:
        rotate_clipped(output, template, rotate_box)
    if args.name:
        draw_name(
            output,
            template,
            args.name,
            args.name_box,
            args.name_angle,
            args.font,
            args.font_size,
            args.name_fill,
            args.name_bg,
        )
    if args.quantize:
        output = quantize_editable(output, template, args.quantize)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.save(args.output, format="PNG", optimize=True)
    saved = Image.open(args.output).convert("RGBA")
    editable, protected, protected_diff, alpha_diff = validate(template, saved)
    size = args.output.stat().st_size
    print(
        f"尺寸={saved.width}x{saved.height}; 可贴像素={editable}; "
        f"保护像素={protected}; 保护区差异={protected_diff}; "
        f"Alpha差异={alpha_diff}; 字节={size}"
    )
    if (saved.size != template.size) or protected_diff or alpha_diff:
        raise ValueError("输出未通过模板像素/透明度校验")
    if size > args.max_bytes:
        raise ValueError(f"文件超过大小限制：{size} > {args.max_bytes} bytes，请使用 --quantize")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, OSError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        raise SystemExit(2)
