#!/bin/zsh
set -euo pipefail

# 1) 准备虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask matplotlib python-dotenv requests pyinstaller

# 2) 生成版本信息
APP_VERSION=$(date +%Y%m%d_%H%M%S)
echo "Building RiverDataApp ${APP_VERSION}"

# 3) 打包 Flask 服务为独立可执行
#  - 使用 console 模式，启动后通过浏览器访问 127.0.0.1:PORT
#  - 将模板与静态资源打入
pyinstaller \
  --name RiverDataApp \
  --clean \
  --noconfirm \
  --add-data "templates:templates" \
  --add-data "river_data:river_data" \
  --hidden-import matplotlib \
  --hidden-import matplotlib.backends.backend_agg \
  app.py

# 4) 拷贝示例环境配置
cp -f ./.env.example ./dist/RiverDataApp/.env

echo "打包完成: dist/RiverDataApp"
echo "运行: ./dist/RiverDataApp/RiverDataApp"
echo "如需端口/目录配置，编辑 dist/RiverDataApp/.env"


