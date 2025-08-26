# 河流水文数据分析工具

## ⚠️ 重要提示
- **风险提示**：本工具所提供的数据仅供参考，不能作为任何决策的唯一依据。实际钓鱼活动前，请务必结合当地气象、水文部门发布的官方信息，确保人身安全。
- **使用限制**：本项目**不得用于商业目的**，仅供北京地区钓鱼爱好者个人参考使用。
- **数据来源**：本工具通过公开渠道获取的河流水文数据，可能存在延迟或不准确的情况，请自行判断使用。

## 项目介绍
这是一个用于分析和可视化河流水文数据的Web应用程序，支持时序分析和季节性分析，帮助钓鱼爱好者了解北京地区河流的水文变化规律。

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

## 使用说明
1. 部署完成后，通过浏览器访问应用（默认端口为5000）
2. 应用将展示河流水文数据的可视化图表和分析结果
3. 所有数据仅供北京地区钓鱼爱好者参考，请勿用于其他用途

## 免责声明
使用本工具即表示您同意：对于因使用本工具或依赖本工具提供的数据而产生的任何后果，开发者不承担任何责任。钓鱼活动存在风险，请始终将安全放在首位。
