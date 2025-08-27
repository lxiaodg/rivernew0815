#!/bin/bash

# 启动脚本 - 支持健康检查和自动数据同步

echo "启动河流数据分析应用..."

# 检查环境变量
if [ -z "$DATA_DIR" ]; then
    export DATA_DIR="/app/river_data"
fi

if [ -z "$DB_PATH" ]; then
    export DB_PATH="/app/river_data.db"
fi

# 创建必要的目录
mkdir -p "$DATA_DIR" /app/logs /var/log/app

# 检查数据库是否存在，如果不存在则初始化
if [ ! -f "$DB_PATH" ]; then
    echo "数据库不存在，正在初始化..."
    python /app/analyze_river_data.py --init-db
fi

# 启动时检查数据是否需要更新
echo "检查数据是否需要更新..."
python /app/request_river_data.py --check-update

# 启动cron服务（后台运行）
echo "启动定时任务服务..."
echo "0 12 * * * cd /app && python request_river_data.py --sync >> /var/log/app/cron.log 2>&1" | crontab -
cron -f &
CRON_PID=$!

# 启动Web服务
echo "启动Web服务..."
exec gunicorn \
    -w 2 \
    -b 0.0.0.0:5001 \
    --timeout 300 \
    --log-level info \
    --access-logfile /var/log/app/access.log \
    --error-logfile /var/log/app/error.log \
    --preload \
    app:app
