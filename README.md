# 🧹 broom-widget

macOS 菜单栏磁盘监控小挂件，配合 [broom](https://github.com/hisunfei/broom) skill 使用，实时监控磁盘空间，一键获取清理命令。

---

## ✨ 功能特性

- 📊 **菜单栏实时显示** — 饼图 / 纯文字 / 进度条三种风格，黑白 Template 自动适配深浅色模式
- 📈 **非线性饼图** — 0-90% 使用率压缩显示，90-100% 放大 2 倍，空间紧张时变化更明显
- 🧹 **一键获取清理命令** — 点击「Broom 清理」查看 broom skill 安装和使用说明
- ⚠️ **空间不足提醒** — 可设置 1GB / 3GB / 5GB / 10GB 阈值，低于阈值自动发送系统通知
- 🚀 **开机自启动** — 通过 LaunchAgent 实现，菜单一键切换
- 🐍 **Python + PyObjC** — 无需编译，开箱即用

## 📸 预览

菜单栏显示效果：
- 饼图风格：◔ 487 GB
- 纯文字风格：487 GB 可用
- 进度条风格：███░░░ 487 GB

点击「Broom 清理」弹出说明对话框，包含 broom skill 的安装命令和使用方法。

## 🚀 快速开始

### 环境要求

- macOS 10.15 (Catalina) 或更高版本
- Python 3.8+

### 安装

```bash
# 克隆项目
git clone https://github.com/hisunfei/broom-widget.git
cd broom-widget

# 安装依赖
pip3 install pyobjc-framework-Cocoa

# 启动
python3 disk_monitor.py
```

或使用启动脚本：

```bash
chmod +x start.sh
./start.sh
```

### 停止

```bash
./stop.sh
# 或
pkill -f disk_monitor.py
```

## 📋 菜单说明

```
Broom 清理              ← 查看 broom skill 安装和使用说明
──────────────
空间不足提醒
  1 GB
  ✓ 5 GB               ← 默认阈值
  10 GB
──────────────
开机启动
  ✓ 启用
    禁用
──────────────
显示风格
  ✓ 饼图
    纯文字
    进度条
──────────────
退出            ⌘Q
```

## 🧹 broom skill

broom-widget 配合 [broom](https://github.com/hisunfei/broom) AI 磁盘清理 skill 使用。

### 安装 broom

1. 打开 DeepSeek Harness
2. 输入：`使用https://github.com/hisunfei/broom，为我清理电脑；`
3. AI 会自动完成安装和首次清理

### 使用 broom

- 手动清理：对 Agent 说 `broom`
- 定时清理：对 Agent 说 `每周一上午10 点，使用broom skill自动为我清理电脑（https://github.com/hisunfei/broom）；`

## 🎨 显示风格

| 风格 | 效果 | 说明 |
|------|------|------|
| 饼图 | ◔ 487 GB | 黑白饼图，非线性映射（推荐） |
| 纯文字 | 487 GB 可用 | 极简风格 |
| 进度条 | ███░░░ 487 GB | 横向进度条 |

所有图标使用 Template 模式，系统自动适配深色/浅色模式。

## ⚙️ 配置

配置文件位置：`~/Library/Application Support/broom-widget/config.json`

```json
{
  "style": "pie",
  "alert_threshold_gb": 5,
  "launch_at_startup": false
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `style` | 显示风格（pie / text / bar） | `pie` |
| `alert_threshold_gb` | 空间不足提醒阈值（GB） | `5` |
| `launch_at_startup` | 是否开机自启动 | `false` |

## 🛠️ 开发

```bash
# 运行
python3 disk_monitor.py

# 停止
pkill -f disk_monitor.py
```

## 📄 许可证

MIT License

## 🔗 相关项目

- [broom](https://github.com/hisunfei/broom) — AI 磁盘清理 skill
- [DeepSeek Harness](https://github.com/deepseek-ai/harness) — AI agent 平台

---

# 🧹 broom-widget (English)

A macOS menu bar disk monitor widget that works with the [broom](https://github.com/hisunfei/broom) AI skill for one-click disk cleanup commands.

## Features

- 📊 **Menu bar display** — Pie chart / Text / Progress bar, auto dark/light mode
- 📈 **Non-linear pie chart** — Compressed 0-90%, amplified 90-100% for better visibility when disk is nearly full
- 🧹 **One-click cleanup commands** — View broom skill installation and usage instructions
- ⚠️ **Low space alerts** — Configurable thresholds (1/3/5/10 GB) with system notifications
- 🚀 **Launch at startup** — Via LaunchAgent, one-click toggle
- 🐍 **Python + PyObjC** — No compilation needed

## Quick Start

```bash
git clone https://github.com/hisunfei/broom-widget.git
cd broom-widget
pip3 install pyobjc-framework-Cocoa
python3 disk_monitor.py
```

## broom skill

broom-widget works with the [broom](https://github.com/hisunfei/broom) AI disk cleanup skill.

### Install broom

1. Open DeepSeek Harness
2. Type: `使用https://github.com/hisunfei/broom，为我清理电脑；`
3. AI will install and run the first cleanup automatically

### Use broom

- Manual: Say `broom` to your Agent
- Scheduled: Say `每周一上午10 点，使用broom skill自动为我清理电脑（https://github.com/hisunfei/broom）；`

## License

MIT
