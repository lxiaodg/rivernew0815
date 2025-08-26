# 在app.py文件顶部添加
import os
import json
from datetime import datetime
import matplotlib
matplotlib.use('Agg')

# 添加这两行
from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

# 验证宋体可用性
from matplotlib import font_manager
try:
    songti_path = font_manager.findfont('Songti SC')
    print(f"成功找到宋体路径: {songti_path}")
except Exception as e:
    print(f"宋体加载失败: {str(e)}")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import io
import base64
import hashlib
import time

from config import get_config
from request_river_data import sync_to_latest

# 导入现有的RiverDataAnalyzer类
from analyze_river_data import RiverDataAnalyzer

# 创建Flask应用
app = Flask(__name__)

# 确保使用系统宋体（直接指定字体族）
plt.rcParams['font.sans-serif'] = ['Songti SC', 'STSong', 'SimSun', 'Microsoft YaHei', 'SimHei']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
print("✅ 已配置中文字体: Songti SC, STSong, SimSun")

config = get_config()

# 启动时确保数据已同步至当天
try:
    sync_to_latest(refresh_cookie_on_fail=True)
except Exception:
    pass

# 初始化数据分析器并加载数据
analyzer = RiverDataAnalyzer(data_dir=config.data_dir, db_path=config.db_path)
analyzer.load_data()

# 简单TTL缓存
_CACHE = {}

def _cache_get(key):
    item = _CACHE.get(key)
    if not item:
        return None
    expire_ts, value = item
    if expire_ts < time.time():
        _CACHE.pop(key, None)
        return None
    return value

def _cache_set(key, value, ttl_sec=None):
    ttl = ttl_sec if ttl_sec is not None else config.cache_ttl_seconds
    _CACHE[key] = (time.time() + ttl, value)

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
    os.path.join(log_dir, 'app.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=3
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# 配置根日志器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# 创建应用日志器
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    # 获取所有河流名称
    rivers = analyzer.get_river_names()  # 修复方法名称
    return render_template('index.html', rivers=rivers)

@app.route('/get_stations', methods=['POST'])
def get_stations():
    river_name = request.json.get('river_name')
    stations = analyzer.get_stations_by_river(river_name)
    return jsonify(stations)

@app.route('/plot', methods=['POST'])
def plot():
    river_name = request.json.get('river_name')
    station_name = request.json.get('station_name')
    plot_type = request.json.get('plot_type', 'level')  # 'level', 'flow', or 'both'
    start_date_str = request.json.get('start_date')
    end_date_str = request.json.get('end_date')

    # 缓存键
    key_src = json.dumps({
        'r': river_name, 's': station_name, 't': plot_type,
        'start': start_date_str, 'end': end_date_str
    }, sort_keys=True)
    key = 'plot:' + hashlib.md5(key_src.encode('utf-8')).hexdigest()
    cached = _cache_get(key)
    if cached:
        return jsonify({'image': cached})

    # 获取数据
    data = analyzer.get_data_by_river_and_station(river_name, station_name)
    if not data:
        return jsonify({'error': '未找到数据'}), 400

    # 解析日期和过滤数据
    dates = []
    levels = []
    flows = []

    # 校验日期输入
    start_date = None
    end_date = None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        if start_date and end_date and start_date > end_date:
            return jsonify({'error': '开始日期不能晚于结束日期'}), 400
    except ValueError:
        return jsonify({'error': '日期格式无效，应为 YYYY-MM-DD'}), 400

    for item in data:
        date = item[0]
        if start_date and date < start_date:
            continue
        if end_date and date > end_date:
            continue
        dates.append(date)
        levels.append(item[1])
        flows.append(item[2])

    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))

    if plot_type == 'level' or plot_type == 'both':
        ax.plot(dates, levels, 'b-', label='水位 (m)')
        ax.set_ylabel('水位 (m)', color='b')
        ax.tick_params('y', colors='b')

    if plot_type == 'flow' or plot_type == 'both':
        if plot_type == 'both':
            ax2 = ax.twinx()
            ax2.plot(dates, flows, 'r-', label='流量 (m³/s)')
            ax2.set_ylabel('流量 (m³/s)', color='r')
            ax2.tick_params('y', colors='r')
            lines = ax.get_lines() + ax2.get_lines()
            labels = [line.get_label() for line in lines]
            ax.legend(lines, labels, loc='upper right')
        else:
            ax.plot(dates, flows, 'r-', label='流量 (m³/s)')
            ax.set_ylabel('流量 (m³/s)', color='r')
            ax.tick_params('y', colors='r')
            ax.legend()

    ax.set_xlabel('日期')
    ax.set_title(f'{river_name} - {station_name} 水文数据')
    ax.grid(True)

    # 设置日期格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    # 将图表转换为base64编码
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)

    _cache_set(key, image_base64)
    return jsonify({'image': image_base64})

@app.route('/timeseries', methods=['POST'])
def timeseries():
    river_name = request.json.get('river_name')
    station_name = request.json.get('station_name')
    start_date_str = request.json.get('start_date')
    end_date_str = request.json.get('end_date')

    # 缓存键
    key_src = json.dumps({
        'r': river_name, 's': station_name,
        'start': start_date_str, 'end': end_date_str
    }, sort_keys=True)
    key = 'ts:' + hashlib.md5(key_src.encode('utf-8')).hexdigest()
    cached = _cache_get(key)
    if cached:
        return jsonify(cached)

    data = analyzer.get_data_by_river_and_station(river_name, station_name)
    if not data:
        return jsonify({'error': '未找到数据'}), 400

    # 日期校验
    start_date = None
    end_date = None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        if start_date and end_date and start_date > end_date:
            return jsonify({'error': '开始日期不能晚于结束日期'}), 400
    except ValueError:
        return jsonify({'error': '日期格式无效，应为 YYYY-MM-DD'}), 400

    dates = []
    levels = []
    flows = []
    for dt, z, q in data:
        if start_date and dt < start_date:
            continue
        if end_date and dt > end_date:
            continue
        dates.append(dt.strftime('%Y-%m-%d'))
        levels.append(z)
        flows.append(q)

    resp = {
        'river_name': river_name,
        'station_name': station_name,
        'dates': dates,
        'levels': levels,
        'flows': flows
    }
    _cache_set(key, resp)
    return jsonify(resp)

@app.route('/seasonal_analysis', methods=['POST'])
def seasonal_analysis():
    river_name = request.json.get('river_name')
    station_name = request.json.get('station_name')
    years = int(request.json.get('years', 3))
    
    # 调用分析方法
    result = analyzer.analyze_seasonal_trends(river_name, station_name, years)
    
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    
    return jsonify(result)

@app.route('/sync_now', methods=['POST'])
def sync_now():
    try:
        result = sync_to_latest(refresh_cookie_on_fail=True)
        # 同步后刷新内存中的河流列表
        analyzer.load_data()
        return jsonify({"ok": True, **result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# 添加健康检查路由
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)