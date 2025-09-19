"""
Redis 基礎的分散式速率限制器
用於多實例部署時的速率限制協調
"""

from typing import Optional
import time


class RedisRateLimiter:
    """Redis 速率限制器"""

    def __init__(
        self,
        redis_client,
        max_requests: int = 60,
        window_seconds: int = 60
    ):
        """
        初始化 Redis 速率限制器

        Args:
            redis_client: Redis 客戶端
            max_requests: 時間窗口內最大請求數
            window_seconds: 時間窗口（秒）
        """
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def check_rate_limit(self, client_id: str) -> bool:
        """
        檢查速率限制

        Args:
            client_id: 客戶端識別碼

        Returns:
            是否允許請求
        """
        key = f"rate_limit:{client_id}"
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        try:
            # 使用 Redis 管線優化
            pipe = self.redis.pipeline()

            # 移除過期記錄
            pipe.zremrangebyscore(key, 0, window_start)

            # 計算當前窗口內的請求數
            pipe.zcount(key, window_start, current_time)

            # 添加當前請求
            pipe.zadd(key, {str(current_time): current_time})

            # 設定過期時間
            pipe.expire(key, self.window_seconds * 2)

            results = pipe.execute()

            # 檢查是否超過限制
            request_count = results[1]

            if request_count >= self.max_requests:
                # 移除剛添加的記錄
                self.redis.zrem(key, str(current_time))
                return False

            return True

        except Exception:
            # Redis 錯誤時降級為允許
            return True

    def get_retry_after(self, client_id: str) -> int:
        """
        獲取重試時間

        Args:
            client_id: 客戶端識別碼

        Returns:
            重試秒數
        """
        key = f"rate_limit:{client_id}"
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        try:
            # 獲取最舊的請求時間
            oldest = self.redis.zrange(key, 0, 0, withscores=True)

            if oldest:
                oldest_time = int(oldest[0][1])
                retry_after = self.window_seconds - (current_time - oldest_time)
                return max(0, retry_after)

        except Exception:
            pass

        return self.window_seconds