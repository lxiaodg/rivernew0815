import requests
import json
import urllib3
from datetime import datetime, timedelta
import os
import time
from config import get_config

# 忽略SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = get_config()

# 请求URL
url = 'https://nsbd.swj.beijing.gov.cn/service/cityRiverList/list'

# Cookie 从 .env 读取（JSON 字符串）
cookies = config.cookies or {}

# 请求头从 .env 读取（JSON 字符串），若未配置则使用最小集合
headers = config.headers or {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=UTF-8',
}

# 创建数据保存目录
os.makedirs(config.data_dir, exist_ok=True)

# 获取当前日期
end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# 查找最后下载的日期
def find_last_downloaded_date(directory='river_data'):
    directory = directory or config.data_dir
    files = os.listdir(directory)
    date_pattern = r'river_data_(\d{4}-\d{2}-\d{2})\.json'
    dates = []
    for file in files:
        match = re.match(date_pattern, file)
        if match:
            try:
                date = datetime.strptime(match.group(1), '%Y-%m-%d')
                dates.append(date)
            except ValueError:
                continue
    if dates:
        return max(dates)
    else:
        # 如果没有找到任何数据文件，返回三年前的日期
        return end_date - timedelta(days=3*365)

import re

# 在文件顶部添加
import logging
from logging.handlers import RotatingFileHandler
import os

# 配置日志
log_dir = '/var/log/app'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# 设置日志格式
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 文件日志
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'request_data.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=3
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# 配置日志器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def download_one_day(session: requests.Session, date_str: str, data_dir: str, use_headers: dict, use_cookies: dict) -> bool:
    """下载某一天的数据，成功返回 True，失败返回 False。"""
    filename = f'{data_dir}/river_data_{date_str}.json'
    if os.path.exists(filename):
        return True
    payload = {"queryDate": date_str}
    try:
        response = session.post(url, headers=use_headers, cookies=use_cookies, json=payload, verify=False, timeout=30)
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('code') == 0:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f'  数据已保存到 {filename}')
                    return True
                else:
                    print(f'  请求成功但返回错误码: {data.get("code")}, 消息: {data.get("message")}')
            except json.JSONDecodeError:
                raw_filename = f'{data_dir}/raw_response_{date_str}.txt'
                with open(raw_filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print('  响应不是有效的JSON，已保存原始文本')
        else:
            print(f'  请求失败，状态码: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f'  请求发生错误: {e}')
    return False

def sync_to_latest(refresh_cookie_on_fail: bool = True) -> dict:
    """同步数据到当天；仅使用 .env 中的 Cookie/Headers。返回 {success:int, fail:int}."""
    session = requests.Session()
    use_cookies = config.cookies or {}
    use_headers = headers

    data_dir = config.data_dir
    last_date = find_last_downloaded_date(data_dir)
    start_date = last_date + timedelta(days=1)
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    total_days = (end_date - start_date).days + 1
    if total_days <= 0:
        return {"success": 0, "fail": 0}

    success_count = 0
    fail_count = 0
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f'同步 {date_str} ...')
        ok = download_one_day(session, date_str, data_dir, use_headers, use_cookies)
        if ok:
            success_count += 1
        else:
            fail_count += 1
        current_date += timedelta(days=1)
    return {"success": success_count, "fail": fail_count}

def main():
    try:
        result = sync_to_latest(refresh_cookie_on_fail=True)
        print(f"数据下载完成！成功: {result['success']}, 失败: {result['fail']}")
    except KeyboardInterrupt:
        print('程序被用户中断')
    except Exception as e:
        print(f'发生未知错误: {e}')


if __name__ == '__main__':
    main()