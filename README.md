# 河流数据分析应用

一个基于Flask的河流数据分析Web应用，支持自动数据同步、可视化分析和Docker部署。

## 🚀 特性

- **自动数据同步**: 每日自动从官方API获取最新河流数据
- **数据可视化**: 支持水位、流量图表和时序分析
- **缓存优化**: 内置TTL缓存提升响应速度
- **健康检查**: 内置健康检查端点
- **Docker支持**: 支持容器化部署
- **自动构建**: GitHub Actions自动构建并发布到Docker Hub

## 🏗️ 架构

```
├── app.py                    # Flask主应用
├── analyze_river_data.py     # 数据分析核心
├── request_river_data.py     # 数据获取模块
├── config.py                 # 配置管理
├── templates/                # 前端模板
├── Dockerfile               # Docker镜像构建
├── docker-compose.yml       # 开发环境部署
├── docker-compose.prod.yml  # 生产环境部署
└── .github/workflows/       # CI/CD配置
```

## 🚀 快速开始

### 方式1: Docker部署（推荐）

#### 从Docker Hub拉取运行

```bash
# 设置你的Docker Hub用户名
export DOCKER_HUB_USERNAME="yourusername"

# 使用部署脚本
chmod +x deploy.sh
./deploy.sh

# 或手动运行
docker run -d \
  --name riverapp \
  -p 5001:5001 \
  -v $(pwd)/river_data:/app/river_data \
  -v $(pwd)/logs:/var/log/app \
  -e DATA_DIR=/app/river_data \
  -e DB_PATH=/app/river_data.db \
  --restart unless-stopped \
  yourusername/riverdataapp:latest
```

#### 使用Docker Compose

```bash
# 开发环境
docker compose up -d

# 生产环境
docker compose -f docker-compose.prod.yml up -d
```

### 方式2: 本地开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

## ⚙️ 配置

### 环境变量

创建 `.env` 文件：

```bash
# 应用配置
PORT=5001
DATA_DIR=river_data
DB_PATH=river_data.db
CACHE_TTL_SECONDS=600

# API请求配置
REQUEST_HEADERS_JSON={"User-Agent": "Mozilla/5.0..."}
REQUEST_COOKIES_JSON={"__jsluid_s": "..."}
```

### 获取Cookies

1. 访问 https://nsbd.swj.beijing.gov.cn/cshhsq.html
2. 打开开发者工具，复制Cookie和Headers
3. 更新 `.env` 文件

## 🔄 数据同步

### 自动同步

- 应用启动时自动检查数据更新
- 每日12:00自动同步最新数据
- 支持增量更新，只下载缺失数据

### 手动同步

```bash
# 检查数据是否需要更新
python request_river_data.py --check-update

# 手动同步数据
python request_river_data.py --sync

# 初始化数据库
python request_river_data.py --init-db
```

## 📊 API接口

### 健康检查
```
GET /health
```

### 数据可视化
```
POST /plot
{
  "river_name": "永定河",
  "station_name": "三家店",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31"
}
```

### 时序数据
```
POST /timeseries
{
  "river_name": "永定河",
  "station_name": "三家店",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31"
}
```

### 手动同步
```
POST /sync_now
```

## 🚀 CI/CD部署

### GitHub Actions

1. 在GitHub仓库设置中添加Secrets：
   - `DOCKER_HUB_USERNAME`: Docker Hub用户名
   - `DOCKER_HUB_ACCESS_TOKEN`: Docker Hub访问令牌

2. 推送代码到main分支自动触发构建：
   ```bash
   git add .
   git commit -m "feat: 新功能"
   git push origin main
   ```

3. 查看构建状态：Actions → Build and Deploy

### 手动发布

```bash
# 构建镜像
docker build -t yourusername/riverdataapp:latest .

# 推送到Docker Hub
docker push yourusername/riverdataapp:latest
```

## 📁 数据持久化

应用使用Docker volumes确保数据持久化：

- `river_data`: 河流数据文件
- `river_db`: SQLite数据库
- `app_logs`: 应用日志

## 🔍 监控和日志

### 健康检查
```bash
curl http://localhost:5001/health
```

### 查看日志
```bash
# 应用日志
docker logs -f riverapp

# 数据同步日志
docker exec riverapp tail -f /var/log/app/cron.log
```

### 性能监控
- 内置TTL缓存（默认10分钟）
- 数据库复合索引优化
- 增量数据加载

## 🛠️ 开发

### 项目结构
```
rivernew0815/
├── app.py                    # Flask应用主文件
├── analyze_river_data.py     # 数据分析模块
├── request_river_data.py     # 数据获取模块
├── config.py                 # 配置管理
├── templates/                # 前端模板
├── Dockerfile               # Docker镜像
├── docker-compose.yml       # 开发环境
├── docker-compose.prod.yml  # 生产环境
├── deploy.sh                # 部署脚本
└── .github/workflows/       # CI/CD配置
```

### 添加新功能
1. 在相应模块中实现功能
2. 添加必要的API端点
3. 更新前端模板
4. 添加测试用例
5. 提交并推送代码

## 📝 更新日志

### v1.0.0
- 基础河流数据分析功能
- Flask Web界面
- 自动数据同步
- Docker支持
- GitHub Actions CI/CD

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交GitHub Issue。
