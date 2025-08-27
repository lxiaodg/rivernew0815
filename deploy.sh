#!/bin/bash

# 河流数据分析应用部署脚本

set -e

# 配置
DOCKER_HUB_USERNAME=${DOCKER_HUB_USERNAME:-"yourusername"}
IMAGE_NAME="riverdataapp"
CONTAINER_NAME="riverapp"
PORT=5001

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 河流数据分析应用部署脚本${NC}"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行，请先启动Docker${NC}"
    exit 1
fi

# 停止并删除现有容器
if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}🔄 停止现有容器...${NC}"
    docker stop ${CONTAINER_NAME} || true
    docker rm ${CONTAINER_NAME} || true
fi

# 拉取最新镜像
echo -e "${YELLOW}📥 拉取最新镜像...${NC}"
docker pull ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest

# 创建数据目录
mkdir -p ./river_data
mkdir -p ./logs

# 运行容器
echo -e "${YELLOW}🚀 启动应用...${NC}"
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:5001 \
    -v "$(pwd)/river_data:/app/river_data" \
    -v "$(pwd)/logs:/var/log/app" \
    -e DATA_DIR=/app/river_data \
    -e DB_PATH=/app/river_data.db \
    -e TZ=Asia/Shanghai \
    --restart unless-stopped \
    ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest

# 等待应用启动
echo -e "${YELLOW}⏳ 等待应用启动...${NC}"
sleep 10

# 检查健康状态
if curl -f http://localhost:${PORT}/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 应用启动成功！${NC}"
    echo -e "${GREEN}🌐 访问地址: http://localhost:${PORT}${NC}"
    echo -e "${GREEN}📊 健康检查: http://localhost:${PORT}/health${NC}"
else
    echo -e "${RED}❌ 应用启动失败，查看日志:${NC}"
    docker logs ${CONTAINER_NAME}
    exit 1
fi

# 显示容器状态
echo -e "${YELLOW}📋 容器状态:${NC}"
docker ps --filter "name=${CONTAINER_NAME}"

# 显示日志
echo -e "${YELLOW}📝 最近日志:${NC}"
docker logs --tail 20 ${CONTAINER_NAME}

echo -e "${GREEN}🎉 部署完成！${NC}"
echo ""
echo "常用命令:"
echo "  查看日志: docker logs -f ${CONTAINER_NAME}"
echo "  停止应用: docker stop ${CONTAINER_NAME}"
echo "  重启应用: docker restart ${CONTAINER_NAME}"
echo "  删除应用: docker rm -f ${CONTAINER_NAME}"
