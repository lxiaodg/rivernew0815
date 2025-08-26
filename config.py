import os
import json

try:
    from dotenv import load_dotenv  # 可选依赖
    load_dotenv()
except Exception:
    pass


def _get_json_env(name, default_obj):
    raw = os.getenv(name)
    if not raw:
        return default_obj
    try:
        return json.loads(raw)
    except Exception:
        return default_obj


class AppConfig:
    def __init__(self):
        self.port = int(os.getenv('PORT', '5001'))
        self.data_dir = os.getenv('DATA_DIR', 'river_data')
        self.db_path = os.getenv('DB_PATH', 'river_data.db')
        self.cache_ttl_seconds = int(os.getenv('CACHE_TTL_SECONDS', '600'))

        # 下载相关
        self.headers = _get_json_env('REQUEST_HEADERS_JSON', {})
        self.cookies = _get_json_env('REQUEST_COOKIES_JSON', {})


def get_config() -> AppConfig:
    return AppConfig()


