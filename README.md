# River Data App

## 运行(开发)
1. python3 -m venv venv && source venv/bin/activate
2. pip install -U pip && pip install flask matplotlib python-dotenv requests
3. cp .env.example .env 并填写 cookies/headers
4. python app.py

## 一键补齐数据
source venv/bin/activate && python request_river_data.py

## 打包
见 build_mac.sh 脚本
