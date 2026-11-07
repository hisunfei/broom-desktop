#!/bin/bash
# 停止磁盘监控

echo "🛑 正在停止磁盘监控..."

# 查找并杀死所有 disk_monitor.py 进程
pkill -f "disk_monitor.py"

if [ $? -eq 0 ]; then
    echo "✅ 磁盘监控已停止"
else
    echo "⚠️  未找到运行中的磁盘监控进程"
fi
