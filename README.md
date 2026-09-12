# Tesla Skin Skills

用于制作 Tesla Paint Shop 自定义车身贴膜的 Codex 技能。技能以 Tesla 官方 [custom-wraps](https://github.com/teslamotors/custom-wraps) 模板为唯一几何依据，把用户照片、风格参考或生成图案安全地合成到指定车型的 UV 画布中。

## 支持车型

车型目录来自官方仓库当前的文件夹：

| slug | 车型 |
| --- | --- |
| `cybertruck` | Cybertruck |
| `model3` | Model 3 |
| `model3-2024-base` | Model 3 (2024+) Standard and Premium |
| `model3-2024-performance` | Model 3 (2024+) Performance |
| `modely` | Model Y |
| `modely-2025-base` | Model Y (2025+) Standard |
| `modely-2025-performance` | Model Y (2025+) Performance |
| `modely-2025-premium` | Model Y (2025+) Premium |
| `modely-l` | Model Y L |
| `models-2021` | Model S (2021+) |
| `models-2025-plaid` | Model S (2025+) Plaid |
| `modelx-2021` | Model X (2021+) |

## 目录结构

```text
skills/tesla-modely-wrap/
├── SKILL.md                  # Codex 技能说明
├── agents/openai.yaml        # 技能显示信息和默认提示词
├── models.json               # 官方车型、模板路径和下载地址
└── scripts/
    ├── apply_wrap.py         # 严格按模板遮罩合成 PNG
    └── fetch_templates.py    # 下载一个或全部官方模板
```

## 使用方式

在 Codex 中调用：

```text
$tesla-modely-wrap
```

说明目标车型，并提供猫咪照片、风格参考和需要的文字元素。生成时应把对应的 `template.png` 作为几何参考，把 `vehicle_image.png` 作为车机视角参考。最终交付的是一张平面 UV PNG，不是车辆渲染图。

### 下载官方模板

需要 Python 3 和 Pillow。下载全部车型的模板及车辆参考图：

```powershell
python skills/tesla-modely-wrap/scripts/fetch_templates.py `
  --dest official_custom_wraps
```

只下载一个车型，或只下载模板：

```powershell
python skills/tesla-modely-wrap/scripts/fetch_templates.py `
  --model modely-2025-premium `
  --dest official_custom_wraps `
  --no-vehicle-image
```

### 合成输出

从官方仓库目录加载 Model Y Premium 模板：

```powershell
python skills/tesla-modely-wrap/scripts/apply_wrap.py `
  --model modely-2025-premium `
  --template-root official_custom_wraps `
  --design generated_design.png `
  --output Cat_ModelY_Example.png
```

也可以直接传入模板路径：

```powershell
python skills/tesla-modely-wrap/scripts/apply_wrap.py `
  --template path/to/template.png `
  --design generated_design.png `
  --output Cybertruck_Cat.png
```

列出目录中的全部车型：

```powershell
python skills/tesla-modely-wrap/scripts/apply_wrap.py --list-models
```

## 几何和安全约束

- 选中的官方 `template.png` 是唯一几何依据，画布尺寸必须原样保留。官方模板尺寸在 512×512 到 1024×1024 之间，Cybertruck 当前为 1024×768。
- 只有模板 RGBA 恰好为 `(255, 255, 255, 255)` 的纯白不透明像素允许替换。
- 窗户、轮洞、接缝、传感器、黑色区域、透明区域和其他非白像素必须逐像素保持不变。
- 不把另一个车型的面板位置、方向或前保险杠坐标套到当前车型。需要倒置区域时使用可重复的 `--rotate-box x,y,width,height`。
- Model Y Premium 保留旧版前保险杠兼容参数。其他车型使用 `--front-bumper-box` 前必须先从对应模板核对区域。
- 名称或徽章在遮罩合成后确定性叠加。需要前保险杠倒置文字时使用 `--name-angle 180`。
- 输出必须是 PNG，文件小于等于 1,000,000 bytes，文件名只允许英文、数字和下划线，包含 `.png` 在内不超过 30 个字符。

## 校验

`apply_wrap.py` 会自动检查输出尺寸、保护区差异和 Alpha 差异。交付前应确认保护区差异和 Alpha 差异均为 `0`。文件过大时，可以使用 `--quantize 256` 压缩可编辑区域的颜色，再重新校验。

安装依赖：

```powershell
python -m pip install pillow
```

技能本身通过 Codex `quick_validate.py` 校验；脚本通过 Python 编译检查，并以 Cybertruck、Model 3 和 Model Y Premium 模板完成跨尺寸合成验证。

## 许可与来源

本仓库中的模板下载地址和车型信息来自 Tesla 官方 [custom-wraps](https://github.com/teslamotors/custom-wraps) 仓库。模板及示例图的权利归其原作者所有；本仓库主要提供技能说明、车型目录和本地合成工具。
