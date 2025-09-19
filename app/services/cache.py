"""
快取服務
用於存儲和檢索降級時使用的快取資料
"""

import time
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import json
import hashlib


class ResponseCache:
    """回應快取"""

    def __init__(self, ttl: int = 300):
        """
        初始化快取

        Args:
            ttl: 存活時間（秒）
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_key(self, **kwargs) -> str:
        """生成快取鍵"""
        # 將參數序列化並計算雜湊
        key_data = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        獲取快取

        Returns:
            快取資料或 None
        """
        key = self._get_key(**kwargs)

        if key not in self._cache:
            return None

        cache_entry = self._cache[key]
        cache_time = cache_entry["timestamp"]
        cache_age = time.time() - cache_time

        if cache_age > self.ttl:
            # 快取過期
            del self._cache[key]
            return None

        return {
            **cache_entry["data"],
            "cache_age": int(cache_age)
        }

    def set(self, data: Dict[str, Any], **kwargs):
        """存儲快取"""
        key = self._get_key(**kwargs)
        self._cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    def clear_expired(self):
        """清理過期快取"""
        current_time = time.time()
        keys_to_delete = []

        for key, entry in self._cache.items():
            if current_time - entry["timestamp"] > self.ttl:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._cache[key]