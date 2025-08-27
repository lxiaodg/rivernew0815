# 第一阶段：构建环境
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# 安装构建依赖
RUN apt-get update && \ 
    apt-get install -y --no-install-recommends gcc libc-dev

# 复制和安装Python依赖
COPY requirements.txt ./
RUN pip install --user --upgrade pip && \ 
    pip install --user -r requirements.txt

# 第二阶段：运行环境
FROM python:3.11-slim AS runtime

WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH" \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

# 安装运行时依赖和中文字体
RUN apt-get update && \ 
    apt-get install -y --no-install-recommends \
        cron \
        tzdata \
        curl \
        fonts-wqy-zenhei \
        fonts-wqy-microhei \
        fonts-noto-cjk \
        && \ 
    # 配置字体缓存
    fc-cache -fv && \
    # 清理缓存
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # 设置时区
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /var/log/app /app/river_data /app/logs

# 设置权限
RUN chmod +x /app/start.sh

EXPOSE 5001

# 使用启动脚本
CMD ["/app/start.sh"]


