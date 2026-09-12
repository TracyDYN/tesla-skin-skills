# Tesla Skin Skills

用于制作 Tesla Paint Shop 自定义车身贴膜的 Codex 技能。技能以 Tesla 官方 [custom-wraps](https://github.com/teslamotors/custom-wraps) 模板为唯一几何依据，把用户照片、风格参考或生成图案安全地合成到指定车型的 UV 画布中。最终 PNG 的背景必须透明，不添加纯色背景、场景背景或车辆渲染背景。

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
skills/tesla-wrap/
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
$tesla-wrap
```

说明目标车型，并提供猫咪照片、风格参考和需要的文字元素。生成时应把对应的 `template.png` 作为几何参考，把 `vehicle_image.png` 作为车机视角参考。最终交付的是一张平面 UV PNG，不是车辆渲染图。

### 下载官方模板

需要 Python 3 和 Pillow。下载全部车型的模板及车辆参考图：

```powershell
python skills/tesla-wrap/scripts/fetch_templates.py `
  --dest official_custom_wraps
```

只下载一个车型，或只下载模板：

```powershell
python skills/tesla-wrap/scripts/fetch_templates.py `
  --model model3 `
  --dest official_custom_wraps `
  --no-vehicle-image
```

### 合成输出

从官方仓库目录加载指定车型模板：

```powershell
python skills/tesla-wrap/scripts/apply_wrap.py `
  --model model3 `
  --template-root official_custom_wraps `
  --design generated_design.png `
  --output Cat_Model3_Example.png
```

也可以直接传入模板路径：

```powershell
python skills/tesla-wrap/scripts/apply_wrap.py `
  --template path/to/template.png `
  --design generated_design.png `
  --output Cybertruck_Cat.png
```

列出目录中的全部车型：

```powershell
python skills/tesla-wrap/scripts/apply_wrap.py --list-models
```

## 面板内容分配参考

提供的卡通猫皮肤体现了一种适合车机视角的布局。它把大尺寸、需要辨识度的内容集中在大面板，把装饰纹样放在小面板：

- 机舱盖放一张主图或主角肖像，作为整张皮肤的视觉中心。
- 四个主要车门各放一张清晰主图，人物或猫咪面部要完整落在对应门板内，并按车机视角调整朝向。
- 前后翼子板、侧后围、尾门等较宽的辅助面放云朵、爱心、星星、色块或主背景的裁切纹样。
- 前后保险杠、后视镜、侧裙和窄条只放重复小图案或颜色点缀，不放脸部、长文字和复杂场景。
- 天窗、玻璃、车窗、轮洞、传感器、接缝、黑色区域、透明区域以及模板中其他不可编辑区域不放任何图案，保持官方模板原像素。
- 模板中 Alpha 为 0 的区域在最终 PNG 中必须继续保持透明。生成提示词要明确要求透明背景，不能用白色或黑色填充透明区域。

不同车型的 UV 面板形状和数量不同。每次都要以所选车型自己的 `template.png` 和 `vehicle_image.png` 重新判断面板职责，不能照搬其他车型的坐标或旋转角度。

## 主体物理朝向要求

每个面上的主体物必须符合车辆在现实世界中的朝向。UV 图做完面板变换后，要回到车机视角复核：

- 以重力方向为准，头顶、直立物体、天空和竖排文字朝上，脚、车轮、地面和阴影朝下。
- 主体可以面向车辆左侧或右侧，但不能因为门板或保险杠的 UV 旋转而倒置、横躺或头朝下。
- 左右两侧车门都必须让主体的头或顶部朝向天窗和车顶线，脚或底部朝向侧裙。车头方向在车门上是水平的前后方向，不能当作竖直向上。
- 左右侧门板分别检查。需要旋转或镜像时，只调整当前面板的图案，不对整张画布做全局旋转；两侧不默认使用相同的 UV 变换。
- 机舱盖、尾门、保险杠、后视镜和窄条要结合面板法线与 `vehicle_image.png` 判断变换。只有在车机视角中仍然符合现实朝向时，才允许使用 180 度变换。
- 抽象装饰纹样可以按面板需要旋转，但不能以此为理由让猫咪、人物或其他主体物倒置。

## 几何和安全约束

- 选中的官方 `template.png` 是唯一几何依据，画布尺寸必须原样保留。官方模板尺寸在 512×512 到 1024×1024 之间，Cybertruck 当前为 1024×768。
- 只有模板 RGBA 恰好为 `(255, 255, 255, 255)` 的纯白不透明像素允许替换。
- 窗户、轮洞、接缝、传感器、黑色区域、透明区域和其他非白像素必须逐像素保持不变。
- 图像生成提示词必须明确禁止在天窗、玻璃和所有非白保护区域绘图；最终仍由遮罩脚本逐像素恢复保护区。
- 输出背景必须透明，不能出现纯色、照片、车辆渲染或其他场景背景；脚本会校验模板的透明像素没有被改变。
- 不把另一个车型的面板位置、方向或前保险杠坐标套到当前车型。需要倒置区域时使用可重复的 `--rotate-box x,y,width,height`。
- 每个面板都要做世界朝向检查，确认主体、地平线、车轮、阴影和文字基线符合重力及车辆前后方向，尤其检查左右车门是否头朝天窗、脚朝侧裙。
- 目录保留上游官方 slug 以便准确定位模板；项目目录、技能名和通用文案使用 Tesla Custom Wrap。旧版 Premium 前保险杠兼容参数仅对对应模板有效，其他车型使用 `--front-bumper-box` 前必须先核对区域。
- 名称或徽章在遮罩合成后确定性叠加。使用 `--name` 时必须同时按当前模板显式提供 `--name-box`，需要前保险杠倒置文字时再使用 `--name-angle 180`。
- 输出必须是 PNG，文件小于等于 1,000,000 bytes，文件名只允许英文、数字和下划线，包含 `.png` 在内不超过 30 个字符。

## 校验

`apply_wrap.py` 会自动检查输出尺寸、保护区差异、透明背景差异和 Alpha 差异。交付前应确认保护区差异、透明背景差异和 Alpha 差异均为 `0`。文件过大时，可以使用 `--quantize 256` 压缩可编辑区域的颜色，再重新校验。

安装依赖：

```powershell
python -m pip install pillow
```

技能本身通过 Codex `quick_validate.py` 校验；脚本通过 Python 编译检查，并以 Cybertruck、Model 3 和 Premium 模板完成跨尺寸合成验证。物理朝向需要在车机视角中人工复核，脚本只负责模板遮罩、透明度和文件约束。

## 许可与来源

本仓库中的模板下载地址和车型信息来自 Tesla 官方 [custom-wraps](https://github.com/teslamotors/custom-wraps) 仓库。模板及示例图的权利归其原作者所有；本仓库主要提供技能说明、车型目录和本地合成工具。
