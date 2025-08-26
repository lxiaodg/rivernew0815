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
    TZ=Asia/Shanghai

# 安装运行时依赖和中文字体
RUN apt-get update && \ 
    apt-get install -y --no-install-recommends cron tzdata && \ 
    # 安装中文字体支持
    apt-get install -y --no-install-recommends fonts-wqy-zenhei fonts-wqy-microhei && \ 
    rm -rf /var/lib/apt/lists/* && \ 
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /var/log/app

EXPOSE 5001

# 默认启动Web服务（使用Gunicorn）
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5001", "--timeout", "300", "--log-level", "info", "app:app"]


