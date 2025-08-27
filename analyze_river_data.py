import json
import os
import hashlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import glob
import matplotlib.font_manager as fm
import warnings
import sqlite3

# 彻底禁用所有matplotlib字体警告
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.font_manager")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="matplotlib.font_manager")

# 设置中文显示方案
plt.rcParams['font.sans-serif'] = [
    'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei',
    'Heiti SC', 'STHeiti', 'Arial Unicode MS', 'sans-serif'
]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# 可选: 中文字体提示（仅在作为主程序运行时提示）
FONT_HINT = (
    "提示: 如果图表中文显示为方框，请安装中文字体:\n"
    "   macOS: brew install --cask font-sarasa-gothic\n"
    "   Windows: 下载并安装 'Microsoft YaHei' 或 'SimHei' 字体\n"
    "   Linux: sudo apt install fonts-wqy-microhei"
)

# 在文件顶部导入logging模块
import logging

class RiverDataAnalyzer:
    def __init__(self, data_dir='river_data', db_path=None):
        self.data_dir = data_dir
        self.db_path = db_path or 'river_data.db'  # 数据库路径
        self.rivers = set()
        self.init_database()

    def init_database(self):
        """初始化数据库连接和表结构"""
        conn = sqlite3.connect(self.db_path)
        self._init_database(conn)
        conn.close()

    def _get_connection(self):
        """获取新的数据库连接"""
        return sqlite3.connect(self.db_path)

    def _init_database(self, conn):
        cursor = conn.cursor()
        # 创建数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS river_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            river_name TEXT,
            station_name TEXT,
            date TEXT,
            date_int INTEGER,
            z_value REAL,
            q_value REAL,
            UNIQUE(river_name, station_name, date)
        );
        ''')
        # 创建索引以加速查询
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_river ON river_data(river_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_station ON river_data(station_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON river_data(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_int ON river_data(date_int)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_river_station_date ON river_data(river_name, station_name, date)')
        conn.commit()

        # 迁移: 确保旧数据具有 date_int
        try:
            cursor.execute('PRAGMA table_info(river_data)')
            cols = [row[1] for row in cursor.fetchall()]
            if 'date_int' not in cols:
                cursor.execute('ALTER TABLE river_data ADD COLUMN date_int INTEGER')
                conn.commit()
            cursor.execute('UPDATE river_data SET date_int = CAST(strftime("%Y%m%d", date) AS INTEGER) WHERE date IS NOT NULL AND (date_int IS NULL OR date_int = 0)')
            conn.commit()
        except Exception:
            pass

    # 修改 load_data 方法使用数据库
    def load_data(self):
        # 增量导入：仅导入库中最大日期之后的文件
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(date) FROM river_data')
        row = cursor.fetchone()
        max_date_in_db = row[0] if row and row[0] else None

        # 获取所有JSON文件
        files = glob.glob(os.path.join(self.data_dir, '*.json'))
        
        # 加载数据到数据库
        for file_path in sorted(files):
            try:
                file_name = os.path.basename(file_path)
                # 从文件名提取日期 (格式: river_data_YYYY-MM-DD.json)
                date_str = file_name.replace('river_data_', '').replace('.json', '')
                if max_date_in_db and date_str <= max_date_in_db:
                    continue
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 检查数据结构是否正确
                    if 'data' not in data or 'river_data' not in data['data']:
                        logger.error(f"文件 {file_name} 结构无效")
                        continue
                    
                    river_systems = data['data']['river_data']
                    
                    # 存储数据到数据库
                    for system in river_systems:
                        river_system = system['river_system']
                        for detail in system['river_detail']:
                            river_name = detail['river']
                            station_name = detail['river_name']
                            
                            # 检查Z和Q是否为有效数值（非'--'）
                            z_str = detail.get('Z', '')
                            q_str = detail.get('Q', '')
                            
                            if z_str == '--' or q_str == '--':
                                logger.warning(f"文件 {file_name} 跳过无效数据: {river_name}-{station_name} Z={z_str} Q={q_str}")
                                continue
                            
                            try:
                                z_value = float(z_str)
                                q_value = float(q_str)
                                # 插入数据库（含 date_int）
                                try:
                                    date_int = int(datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y%m%d'))
                                except Exception:
                                    date_int = None
                                cursor.execute(
                                    'INSERT OR IGNORE INTO river_data (river_name, station_name, date, date_int, z_value, q_value) VALUES (?, ?, ?, ?, ?, ?)',
                                    (river_name, station_name, date_str, date_int, z_value, q_value)
                                )
                            except (ValueError, KeyError) as e:
                                logger.error(f"文件 {file_name} 数据解析错误: {e}")
                    conn.commit()
            except Exception as e:
                # 异常处理代码
                logger.error(f"加载数据时出错: {e}")
        
        # 刷新河流集合
        cursor.execute('SELECT DISTINCT river_name FROM river_data')
        self.rivers = set(row[0] for row in cursor.fetchall())
        conn.close()

    # 修改数据获取方法
    def get_data_by_river_and_station(self, river_name, station_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT date, z_value, q_value FROM river_data WHERE river_name=? AND station_name=? ORDER BY date',
            (river_name, station_name)
        )
        result = [(datetime.strptime(row[0], '%Y-%m-%d'), row[1], row[2]) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_river_names(self):
        """获取所有河流名称"""
        return sorted(list(self.rivers))

    def get_stations_by_river(self, river_name):
        """根据河流名称获取所有站点"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT station_name FROM river_data WHERE river_name=?", (river_name,))
        stations = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sorted(stations)


    def plot_water_level(self, river_name, station_name=None):
        """绘制指定河流(和站点)的水位变化曲线"""
        # 获取数据
        if station_name:
            data = self.get_data_by_river_and_station(river_name, station_name)
            if not data:
                print(f"错误: 未找到 {river_name} - {station_name} 的数据!")
                return
            title = f'{river_name} - {station_name} 水位变化曲线'
        else:
            # 如果未指定站点，获取该河流的第一个站点
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT station_name FROM river_data WHERE river_name=? LIMIT 1", (river_name,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                print(f"错误: 未找到 {river_name} 的数据!")
                return
            station_name = row[0]
            data = self.get_data_by_river_and_station(river_name, station_name)
            title = f'{river_name} - {station_name} 水位变化曲线'

        # 准备绘图数据
        dates = [item[0] for item in data]
        levels = [item[1] for item in data]

        # 创建图表
        plt.figure(figsize=(12, 6))
        plt.plot(dates, levels, '-b', linewidth=1)
        plt.scatter(dates, levels, s=10, c='r')

        # 设置图表属性
        plt.title(title, fontsize=16)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('水位 (m)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)

        # 格式化x轴日期，增加间隔减少密度
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # 每2个月一个刻度
        plt.xticks(rotation=30)  # 减少旋转角度

        # 增加图表宽度提供更多空间
        plt.gcf().set_figwidth(14)
        plt.tight_layout()

        # 显示图表
        plt.show()

    def plot_water_flow(self, river_name, station_name=None):
        """绘制指定河流(和站点)的流量变化曲线"""
        # 获取数据
        if station_name:
            data = self.get_data_by_river_and_station(river_name, station_name)
            if not data:
                print(f"错误: 未找到 {river_name} - {station_name} 的数据!")
                return
            title = f'{river_name} - {station_name} 流量变化曲线'
        else:
            # 如果未指定站点，获取该河流的第一个站点
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT station_name FROM river_data WHERE river_name=? LIMIT 1", (river_name,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                print(f"错误: 未找到 {river_name} 的数据!")
                return
            station_name = row[0]
            data = self.get_data_by_river_and_station(river_name, station_name)
            title = f'{river_name} - {station_name} 流量变化曲线'

        # 准备绘图数据
        dates = [item[0] for item in data]
        flows = [item[2] for item in data]

        # 创建图表
        plt.figure(figsize=(12, 6))
        plt.plot(dates, flows, '-g', linewidth=1)
        plt.scatter(dates, flows, s=10, c='purple')

        # 设置图表属性
        plt.title(title, fontsize=16)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('流量 (m³/s)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)

        # 格式化x轴日期，增加间隔减少密度
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # 每2个月一个刻度
        plt.xticks(rotation=30)  # 减少旋转角度

        # 增加图表宽度提供更多空间
        plt.gcf().set_figwidth(14)
        plt.tight_layout()

        # 显示图表
        plt.show()

    def plot_level_and_flow(self, river_name, station_name=None):
        """同时绘制指定河流(和站点)的水位和流量变化曲线"""
        # 获取数据
        if station_name:
            data = self.get_data_by_river_and_station(river_name, station_name)
            if not data:
                print(f"错误: 未找到 {river_name} - {station_name} 的数据!")
                return
            title = f'{river_name} - {station_name} 水位与流量变化曲线'
        else:
            # 如果未指定站点，获取该河流的第一个站点
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT station_name FROM river_data WHERE river_name=? LIMIT 1", (river_name,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                print(f"错误: 未找到 {river_name} 的数据!")
                return
            station_name = row[0]
            data = self.get_data_by_river_and_station(river_name, station_name)
            title = f'{river_name} - {station_name} 水位与流量变化曲线'

        # 准备绘图数据
        dates = [item[0] for item in data]
        levels = [item[1] for item in data]
        flows = [item[2] for item in data]

        # 创建图表和轴
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # 绘制水位曲线
        color = 'tab:blue'
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('水位 (m)', color=color, fontsize=12)
        ax1.plot(dates, levels, '-b', linewidth=1, label='水位')
        ax1.scatter(dates, levels, s=10, c='r')
        ax1.tick_params(axis='y', labelcolor=color)

        # 创建第二个y轴用于流量
        ax2 = ax1.twinx()
        color = 'tab:green'
        ax2.set_ylabel('流量 (m³/s)', color=color, fontsize=12)
        ax2.plot(dates, flows, '-g', linewidth=1, label='流量')
        ax2.scatter(dates, flows, s=10, c='purple')
        ax2.tick_params(axis='y', labelcolor=color)

        # 设置图表标题
        plt.title(title, fontsize=16)

        # 格式化x轴日期，增加间隔减少密度
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # 每2个月一个刻度
        plt.xticks(rotation=30)  # 减少旋转角度

        # 添加网格
        ax1.grid(True, linestyle='--', alpha=0.7)

        # 增加图表宽度提供更多空间
        plt.gcf().set_figwidth(14)
        plt.tight_layout()

        # 显示图表
        plt.show()
        
    def analyze_seasonal_trends(self, river_name, station_name, years=3):
        """
        分析指定河流站点的季节性趋势
        :param river_name: 河流名称
        :param station_name: 站点名称
        :param years: 分析的年数
        :return: 包含分析结果的字典
        """
        from datetime import timedelta  # 确保导入timedelta
        
        # 获取数据
        data = self.get_data_by_river_and_station(river_name, station_name)
        if not data:
            return {'error': f'未找到 {river_name} - {station_name} 的数据'}
            
        # 过滤掉无效数据
        valid_data = [
            (date, z, q) for date, z, q in data
            if z > 0 and q > 0  # 确保水位和流量为正数
        ]
        
        if not valid_data:
            return {'error': '没有有效数据'}
            
        # 计算日期范围
        end_date = max(date for date, _, _ in valid_data)
        start_date = end_date - timedelta(days=365*years)
        
        # 季节定义
        seasons = {
            "春季": (3, 5),
            "夏季": (6, 8),
            "秋季": (9, 11),
            "冬季": (12, 2)
        }
        
        # 按年份和季节分组
        seasonal_data = {season: [] for season in seasons}
        
        for date, z, q in valid_data:
            if date < start_date:
                continue
                
            month = date.month
            for season, (start_month, end_month) in seasons.items():
                # 冬季跨年处理
                if season == "冬季":
                    if month == 12 or month <= 2:
                        seasonal_data[season].append((date, z, q))
                elif start_month <= month <= end_month:
                    seasonal_data[season].append((date, z, q))
        
        # 计算每个季节的平均值
        results = {}
        for season, data_points in seasonal_data.items():
            if not data_points:
                continue
                
            avg_z = sum(z for _, z, _ in data_points) / len(data_points)
            avg_q = sum(q for _, _, q in data_points) / len(data_points)
            results[season] = {
                'avg_level': round(avg_z, 2),
                'avg_flow': round(avg_q, 2)
            }
        
        # 构建返回结果
        analysis_result = {
            'river_name': river_name,
            'station_name': station_name,
            'years': years,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'valid_data_count': len(valid_data),
            'seasonal_data': results,
            'yearly_trends': []
        }
        
        # 分析年际变化
        if years >= 2:
            yearly_data = {}
            for date, z, q in valid_data:
                year = date.year
                if year not in yearly_data:
                    yearly_data[year] = []
                yearly_data[year].append((z, q))
                
            prev_avg_z = None
            prev_avg_q = None
            for year in sorted(yearly_data.keys()):
                data_points = yearly_data[year]
                avg_z = sum(z for z, _ in data_points) / len(data_points)
                avg_q = sum(q for _, q in data_points) / len(data_points)
                
                trend = {
                    'year': year,
                    'avg_level': round(avg_z, 2),
                    'avg_flow': round(avg_q, 2)
                }
                
                if prev_avg_z is not None:
                    z_diff = avg_z - prev_avg_z
                    z_pct = (z_diff / prev_avg_z) * 100 if prev_avg_z != 0 else 0
                    trend['level_change'] = f"{z_diff:+.2f}({z_pct:+.1f}%)"
                    
                    q_diff = avg_q - prev_avg_q
                    q_pct = (q_diff / prev_avg_q) * 100 if prev_avg_q != 0 else 0
                    trend['flow_change'] = f"{q_diff:+.2f}({q_pct:+.1f}%)"
                
                analysis_result['yearly_trends'].append(trend)
                prev_avg_z = avg_z
                prev_avg_q = avg_q
        
        return analysis_result

    def interactive_analysis(self):
        """交互式数据分析"""
        if not self.rivers:
            print("没有可用的河流数据!")
            return

        while True:
            print("\n===== 河流水文分析工具 =====")
            print("1. 查看所有河流")
            print("2. 绘制水位曲线")
            print("3. 绘制流量曲线")
            print("4. 同时绘制水位和流量曲线")
            print("5. 退出")

            choice = input("请选择操作 (1-5): ")

            if choice == '1':
                print("\n可用河流列表:")
                for i, river in enumerate(self.get_river_names(), 1):
                    print(f"{i}. {river}")
                    # 显示该河流的站点
                    stations = self.get_stations_by_river(river)
                    for station in stations:
                        print(f"   - {station}")

            elif choice == '2':
                river_list = self.get_river_names()
                print("\n可用河流:")
                for i, river in enumerate(river_list, 1):
                    print(f"{i}. {river}")

                try:
                    river_idx = int(input("请选择河流编号: ")) - 1
                    if 0 <= river_idx < len(river_list):
                        river_name = river_list[river_idx]
                        stations = self.get_stations_by_river(river_name)

                        if len(stations) > 1:
                            print(f"\n{river_name} 的站点:")
                            for i, station in enumerate(stations, 1):
                                print(f"{i}. {station}")
                            station_idx = int(input("请选择站点编号: ")) - 1
                            if 0 <= station_idx < len(stations):
                                station_name = stations[station_idx]
                                self.plot_water_level(river_name, station_name)
                            else:
                                print("无效的站点编号!")
                        else:
                            self.plot_water_level(river_name)
                    else:
                        print("无效的河流编号!")
                except ValueError:
                    print("请输入有效的数字!")

            elif choice == '3':
                river_list = self.get_river_names()
                print("\n可用河流:")
                for i, river in enumerate(river_list, 1):
                    print(f"{i}. {river}")

                try:
                    river_idx = int(input("请选择河流编号: ")) - 1
                    if 0 <= river_idx < len(river_list):
                        river_name = river_list[river_idx]
                        stations = self.get_stations_by_river(river_name)

                        if len(stations) > 1:
                            print(f"\n{river_name} 的站点:")
                            for i, station in enumerate(stations, 1):
                                print(f"{i}. {station}")
                            station_idx = int(input("请选择站点编号: ")) - 1
                            if 0 <= station_idx < len(stations):
                                station_name = stations[station_idx]
                                self.plot_water_flow(river_name, station_name)
                            else:
                                print("无效的站点编号!")
                        else:
                            self.plot_water_flow(river_name)
                    else:
                        print("无效的河流编号!")
                except ValueError:
                    print("请输入有效的数字!")

            elif choice == '4':
                river_list = self.get_river_names()
                print("\n可用河流:")
                for i, river in enumerate(river_list, 1):
                    print(f"{i}. {river}")

                try:
                    river_idx = int(input("请选择河流编号: ")) - 1
                    if 0 <= river_idx < len(river_list):
                        river_name = river_list[river_idx]
                        stations = self.get_stations_by_river(river_name)

                        if len(stations) > 1:
                            print(f"\n{river_name} 的站点:")
                            for i, station in enumerate(stations, 1):
                                print(f"{i}. {station}")
                            station_idx = int(input("请选择站点编号: ")) - 1
                            if 0 <= station_idx < len(stations):
                                station_name = stations[station_idx]
                                self.plot_level_and_flow(river_name, station_name)
                            else:
                                print("无效的站点编号!")
                        else:
                            self.plot_level_and_flow(river_name)
                    else:
                        print("无效的河流编号!")
                except ValueError:
                    print("请输入有效的数字!")

            elif choice == '5':
                print("感谢使用，再见!")
                break

            else:
                print("无效的选择，请重试!")

# 模块级日志器（不在导入时修改全局日志配置）
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='河流数据分析工具')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    
    args = parser.parse_args()
    
    if args.init_db:
        # 初始化数据库
        analyzer = RiverDataAnalyzer()
        analyzer.init_database()
        print("数据库初始化完成")
    else:
        # 默认行为：交互式分析
        logging.basicConfig(level=logging.INFO)
        print(FONT_HINT)
        analyzer = RiverDataAnalyzer()
        analyzer.load_data()
        analyzer.interactive_analysis()