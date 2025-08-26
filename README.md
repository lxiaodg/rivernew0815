# 河流水文数据分析系统

## 项目介绍
这是一个用于分析和可视化河流水文数据的Web应用程序，支持时序分析和季节性分析。

## 部署方法

### 使用Docker部署（推荐）
```bash
# 克隆仓库
git clone https://github.com/lxiaodg/rivernew0815.git
cd rivernew0815

# 配置环境变量
cp .env.example .env
# 编辑.env文件，设置REQUEST_HEADERS_JSON和REQUEST_COOKIES_JSON

# 启动服务
docker-compose up -d
```

## 运行(开发)
1. python3 -m venv venv && source venv/bin/activate
2. pip install -U pip && pip install flask matplotlib python-dotenv requests
3. cp .env.example .env 并填写 cookies/headers
4. python app.py

## 一键补齐数据
source venv/bin/activate && python request_river_data.py

## 打包
见 build_mac.sh 脚本
