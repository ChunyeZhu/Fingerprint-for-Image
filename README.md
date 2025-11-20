# 图像导入处理器 (ImageImportProcessor)

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个支持数字指纹识别和持久化存储的智能图像处理工具。能够自动识别相似图片，并维护完整的图片历史记录。

## ✨ 主要特性

- 🔍 **数字指纹识别** - 使用多种哈希算法生成图片指纹，准确识别相似图片
- 💾 **持久化存储** - 自动保存图片指纹数据库，程序重启后仍可识别历史图片
- 🖼️ **多格式支持** - 支持 JPG, PNG, BMP, TIFF, WEBP 等主流图像格式
- 📊 **相似度分析** - 自动计算并显示图片相似度（0-100%）
- 🎯 **元数据嵌入** - 保存图片时可嵌入数字指纹到文件元数据
- 🖱️ **图形化界面** - 提供文件选择对话框，操作简单直观

## 📋 系统要求

### 必需依赖

```bash
pip install opencv-python
pip install pillow
pip install numpy
pip install imagehash
```

### Python 版本

- Python 3.7 或更高版本

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆或下载项目后，安装所需库
pip install opencv-python pillow numpy imagehash
```

### 2. 运行程序

```bash
python image_input.py
```

### 3. 使用交互式菜单

程序启动后会显示主菜单：

```
============================================================
主菜单
============================================================
1. 图形化选择文件并加载图像
2. 手动输入路径加载图像
3. 查看当前会话已加载的图像
4. 查看指定图像的详细信息
5. 保存图像到文件(嵌入数字指纹)
6. 查看指纹数据库(所有历史记录)
7. 显示使用示例代码
8. 清空指纹数据库
9. 显示数据库文件位置
q. 退出程序
```

## 📖 使用流程

### 基础流程

```
启动程序 → 选择菜单选项 → 加载图像 → 自动识别相似图片 → 保存/查看信息
```

### 详细步骤

#### 步骤 1: 加载图像

**方式 A: 图形化选择（推荐）**
```
主菜单 → 选择 1 → 在弹出窗口中选择图片文件 → 自动加载
```

**方式 B: 手动输入路径**
```
主菜单 → 选择 2 → 输入完整文件路径 → 自动加载
```

#### 步骤 2: 查看相似图片

加载图片后，系统会自动检测并显示：
```
✓ 图像加载成功: example.jpg
  尺寸: 1920x1080
  格式: JPEG
  数字指纹: a1b2c3d4e5f6...

🔍 发现相似图片:
  1. 相似度: 98.5%
     原始文件: example_old.jpg
     首次加载: 2024-01-15
     ⚠️  这很可能是同一张图片!
```

#### 步骤 3: 保存图像

```
主菜单 → 选择 5 → 输入图像哈希前几位 → 输入保存路径 → 自动嵌入指纹
```

#### 步骤 4: 查看历史记录

```
主菜单 → 选择 6 → 显示所有图片的指纹记录
```

## 💻 代码使用示例

### 基础用法

```python
from image_input import ImageImportProcessor

# 创建处理器（自动加载历史数据库）
processor = ImageImportProcessor()

# 使用图形化对话框加载图片
image_hash, image_info = processor.select_image_with_dialog()

if image_hash:
    # 获取图像数组和指纹
    img_array = image_info['array']
    fingerprint = image_info['fingerprint']
    print(f"数字指纹: {fingerprint}")
```

### 保存图像（嵌入指纹）

```python
# 保存图片时自动嵌入数字指纹
processor.save_image(img_array, 'output.png')

# 再次加载保存的图片
processor.load_image_from_path('output.png')
# 系统会自动识别出这是同一张图片
```

### 查找相似图片

```python
# 查找相似度大于90%的图片
similar_images = processor.find_similar_images(fingerprint, threshold=90)

for similar in similar_images:
    print(f"相似度: {similar['similarity']:.1f}%")
    print(f"文件名: {similar['data']['original_filename']}")
```

### 查看数据库

```python
# 显示指纹数据库内容
processor.display_fingerprint_database()

# 查看数据库文件位置
print(f"数据库位置: {processor.storage_file}")
```

## 📁 文件结构

```
Image/
├── image_input.py              # 主程序文件
├── image_fingerprints.json     # 指纹数据库（自动生成）
└── README.md                   # 本文档
```

## 🔧 数据库说明

### 数据库位置

程序会在脚本所在目录创建 `image_fingerprints.json` 文件。

启动时会显示：
```
📂 数据库文件位置: /完整/路径/image_fingerprints.json
✓ 已加载指纹数据库: 5 条记录
```

### 数据库格式

```json
{
  "abc123def456": {
    "fingerprint": "1234abcd_5678efgh_9012ijkl",
    "original_filename": "example.jpg",
    "first_seen": "2024-01-15T10:30:00",
    "count": 3,
    "locations": [
      {
        "path": "/path/to/example.jpg",
        "filename": "example.jpg",
        "timestamp": "2024-01-15T10:30:00",
        "size": 1024000
      }
    ]
  }
}
```

### 数据库管理

```bash
# 查看数据库位置
主菜单 → 选择 9

# 清空数据库
主菜单 → 选择 8 → 输入 yes 确认

# 备份数据库（手动）
cp image_fingerprints.json image_fingerprints.json.backup
```

## 🎯 应用场景

### 1. 图片去重
```python
# 批量加载图片，自动识别重复图片
for img_path in image_list:
    processor.load_image_from_path(img_path)
# 查看数据库，重复图片会被标记
processor.display_fingerprint_database()
```

### 2. 图片追踪
```python
# 追踪图片的所有保存位置和修改历史
similar = processor.find_similar_images(fingerprint, threshold=95)
for loc in similar[0]['data']['locations']:
    print(f"位置: {loc['path']}")
    print(f"时间: {loc['timestamp']}")
```

### 3. 版权保护
```python
# 在图片中嵌入数字指纹
processor.save_image(img_array, 'protected.png', embed_fingerprint=True)
# 后续可通过指纹验证图片来源
```

## ⚠️ 注意事项

1. **数据库文件** - `image_fingerprints.json` 包含所有历史记录，请定期备份
2. **文件权限** - 确保程序对工作目录有读写权限
3. **内存占用** - 大量图片会占用较多内存，建议分批处理
4. **指纹精度** - 相似度阈值可调整（默认90%），过高可能漏检，过低可能误报

## 🐛 常见问题

### Q: 数据库无法加载历史记录？
**A:** 检查以下几点：
- 运行 `选项 9` 查看数据库文件路径
- 确认 `image_fingerprints.json` 文件存在
- 检查文件权限和 JSON 格式是否正确

### Q: 图形化对话框无法打开？
**A:** 确保已安装 tkinter：
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS (通常已内置)
# Windows (通常已内置)
```

### Q: 相似图片识别不准确？
**A:** 可以调整相似度阈值：
```python
similar = processor.find_similar_images(fingerprint, threshold=85)  # 降低阈值
```

## 📊 技术细节

### 数字指纹算法

本工具使用三种哈希算法组合：

1. **Average Hash (aHash)** - 平均哈希，速度快
2. **Perceptual Hash (pHash)** - 感知哈希，精度高
3. **Difference Hash (dHash)** - 差异哈希，抗干扰

### 相似度计算

```python
相似度 = (1 - 汉明距离 / 最大长度) × 100%
最终相似度 = 三种算法相似度的平均值
```

## 📝 更新日志

### v1.0.0 (2024-01-15)
- ✅ 初始版本发布
- ✅ 支持数字指纹识别
- ✅ 持久化存储功能
- ✅ 图形化文件选择
- ✅ 相似度分析

## 📄 许可证

MIT License - 可自由使用和修改

## 👨‍💻 作者

信息对抗系统课程 - 实验四

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**提示**: 首次使用建议运行 `选项 7` 查看使用示例代码。
