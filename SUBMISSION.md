# WorkBuddy Skill 提交信息

## 基本信息

| 字段 | 内容 |
|------|------|
| **Skill 名称** | broom-桌面 |
| **版本** | 1.0.0 |
| **分类** | 系统工具 / 磁盘管理 |
| **平台** | macOS |
| **许可证** | MIT |

## 一句话介绍

macOS 菜单栏磁盘监控工具，实时监控磁盘空间，一键获取 AI 清理命令。

## 详细描述

broom-桌面 是一个轻量级 macOS 菜单栏应用，实时显示磁盘使用情况，配合 broom AI skill 实现智能磁盘清理。

### 核心功能

- **菜单栏实时显示** — 饼图 / 纯文字 / 进度条三种风格，黑白 Template 自动适配深浅色模式
- **非线性饼图** — 0-90% 使用率压缩显示，90-100% 放大 2 倍，空间紧张时变化更明显
- **一键获取清理命令** — 点击「Broom 清理」查看 broom skill 安装和使用说明
- **空间不足提醒** — 可设置 1GB / 3GB / 5GB / 10GB 阈值，低于阈值自动发送系统通知
- **开机自启动** — 通过 LaunchAgent 实现，菜单一键切换
- **Python + PyObjC** — 无需编译，开箱即用

### 使用场景

1. **日常监控** — 随时查看磁盘剩余空间，无需打开系统设置
2. **空间告急** — 收到提醒后，一键获取清理命令
3. **定期清理** — 配合 broom skill 实现自动化清理

## 安装方式

```bash
# 方式 1: 直接运行 .app
下载 Broom Desktop.app，拖入 /Applications 即可

# 方式 2: 从源码运行
git clone https://github.com/hisunfei/broom-desktop.git
cd broom-desktop
pip3 install pyobjc-framework-Cocoa
python3 disk_monitor.py
```

## 依赖

- macOS 10.15 (Catalina) 或更高版本
- Python 3.8+（仅源码运行需要）
- pyobjc-framework-Cocoa（仅源码运行需要）

## 关联 Skill

- **broom** — AI 磁盘清理 skill
  - GitHub: https://github.com/hisunfei/broom
  - 说明: broom-桌面 获取清理命令，broom skill 执行实际清理

## 截图

（请提供以下截图）
1. 菜单栏饼图显示效果
2. 下拉菜单（空间不足提醒、开机启动、显示风格）
3. Broom 清理说明对话框

## 提交文件清单

```
broom-desktop/
├── Broom Desktop.app          # 编译好的应用（26MB）
├── disk_monitor.py            # 源码
├── start.sh                   # 启动脚本
├── stop.sh                    # 停止脚本
├── README.md                  # 文档（中英文）
├── skill.yaml                 # Skill 元数据
└── LICENSE                    # MIT 许可证
```

## 审核说明

- 本应用为纯本地运行，不收集任何用户数据
- 所有磁盘信息通过 macOS 系统 API 获取
- 不联网，不上传数据
- 开源代码，可审查
