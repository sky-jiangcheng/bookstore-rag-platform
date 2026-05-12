"""
轻量级内存速率限制器（无第三方依赖）

使用滑动窗口算法，基于 collections.defaultdict + time 实现。
用于 FastAPI 中间件，在共享库中提供统一的速率限制功能。
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple


class RateLimiter:
    """
    内存速率限制器，使用滑动窗口计数器。

    用法:
        limiter = RateLimiter()
        ok, remaining, reset = limiter.check("client_ip", max_requests=60, window_seconds=60)
        if not ok:
            raise HTTPException(status_code=429, detail="请求过于频繁")
    """

    def __init__(self):
        # {key: [(timestamp, count), ...]}
        self._windows: Dict[str, List[Tuple[float, int]]] = defaultdict(list)

    def check(
        self,
        key: str,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, float]:
        """
        检查是否超过速率限制。

        Args:
            key: 限流键（如客户端 IP）
            max_requests: 窗口内最大请求数
            window_seconds: 窗口大小（秒）

        Returns:
            (是否允许, 剩余请求数, 重置时间戳)
        """
        now = time.time()
        cutoff = now - window_seconds

        # 清理过期记录
        windows = self._windows[key]
        self._windows[key] = [(ts, c) for ts, c in windows if ts > cutoff]

        # 计算当前窗口内的总请求数
        total = sum(c for _, c in self._windows[key])

        if total >= max_requests:
            # 获取最早的记录时间作为重置时间
            reset_time = self._windows[key][0][0] + window_seconds if self._windows[key] else now + window_seconds
            return False, 0, reset_time

        # 记录本次请求
        self._windows[key].append((now, 1))
        remaining = max_requests - total - 1
        reset_time = now + window_seconds
        return True, remaining, reset_time

    def get_client_ip(self, request) -> str:
        """从 FastAPI Request 中提取客户端 IP。"""
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if hasattr(request, "client") and request.client:
            return request.client.host or "unknown"
        return "unknown"


# 全局单例
rate_limiter = RateLimiter()
