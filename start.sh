#!/bin/bash
# broom-桌面 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "broom-桌面"
echo "=========="
echo ""

# 检查 Python 和 PyObjC
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    exit 1
fi

if ! python3 -c "import objc" 2>/dev/null; then
    echo "📦 正在安装 PyObjC..."
    pip3 install pyobjc-framework-Cocoa
    if [ $? -ne 0 ]; then
        echo "❌ 安装 PyObjC 失败"
        exit 1
    fi
fi

echo "✅ 启动 broom-桌面..."
echo ""
echo "💡 提示："
echo "   - 菜单栏显示磁盘空间"
echo "   - 点击「清理磁盘」唤起 agent 清理"
echo "   - 首次使用请先安装 broom skill"
echo ""

python3 disk_monitor.py
