"""
缓存服务
支持内存缓存和Redis缓存
"""
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CacheService:
    """缓存服务基类"""

    def __init__(self, ttl: int = 3600):
        """
        初始化缓存服务

        Args:
            ttl: 缓存过期时间（秒），默认1小时
        """
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, prefix: str, *args) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            *args: 键组成部分

        Returns:
            缓存键
        """
        key_parts = [prefix]
        for arg in args:
            if isinstance(arg, (dict, list)):
                # 对于复杂对象，先序列化为JSON再计算哈希
                key_str = json.dumps(arg, sort_keys=True)
                key_parts.append(hashlib.md5(key_str.encode()).hexdigest()[:16])
            else:
                key_parts.append(str(arg))
        return ":".join(key_parts)

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if key not in self.cache:
            return None

        item = self.cache[key]

        # 检查是否过期
        if item["expires_at"] < time.time():
            del self.cache[key]
            return None

        logger.debug(f"缓存命中: {key}")
        return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认使用初始化时的ttl
        """
        ttl = ttl or self.ttl
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }
        logger.debug(f"缓存设置: {key}, TTL={ttl}s")

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"缓存删除: {key}")
            return True
        return False

    def clear(self) -> None:
        """清空所有缓存"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"清空缓存: 共{count}项")

    def clear_prefix(self, prefix: str) -> int:
        """
        清空指定前缀的所有缓存

        Args:
            prefix: 键前缀

        Returns:
            清空的缓存数量
        """
        count = 0
        keys_to_delete = [key for key in self.cache if key.startswith(prefix)]
        for key in keys_to_delete:
            del self.cache[key]
            count += 1
        logger.info(f"清空前缀缓存: {prefix}, 共{count}项")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        now = time.time()
        valid_count = sum(1 for item in self.cache.values() if item["expires_at"] > now)
        expired_count = len(self.cache) - valid_count

        return {
            "total_items": len(self.cache),
            "valid_items": valid_count,
            "expired_items": expired_count,
            "ttl": self.ttl,
        }


class BookListCache(CacheService):
    """书单推荐缓存服务"""

    # 缓存键前缀
    PREFIX_PARSE = "booklist:parse"
    PREFIX_ANALYZE = "booklist:analyze"
    PREFIX_GENERATE = "booklist:generate"

    def cache_parse_result(
        self,
        user_input: str,
        parsed_requirements: dict,
        ttl: int = 3600,
    ) -> None:
        """
        缓存需求解析结果

        Args:
            user_input: 用户输入
            parsed_requirements: 解析结果
            ttl: 过期时间（秒）
        """
        key = self._generate_key(self.PREFIX_PARSE, user_input)
        self.set(key, parsed_requirements, ttl)

    def get_parse_result(self, user_input: str) -> Optional[dict]:
        """
        获取缓存的解析结果

        Args:
            user_input: 用户输入

        Returns:
            解析结果，如果不存在则返回None
        """
        key = self._generate_key(self.PREFIX_PARSE, user_input)
        return self.get(key)

    def cache_analyze_result(
        self,
        analysis_input: dict,
        result: dict,
        ttl: int = 1800,
    ) -> None:
        """
        缓存分析结果

        Args:
            analysis_input: 分析输入参数
            result: 分析结果
            ttl: 过期时间（秒）
        """
        key = self._generate_key(self.PREFIX_ANALYZE, analysis_input)
        self.set(key, result, ttl)

    def get_analyze_result(self, analysis_input: dict) -> Optional[dict]:
        """
        获取缓存的分析结果

        Args:
            analysis_input: 分析输入参数

        Returns:
            分析结果，如果不存在则返回None
        """
        key = self._generate_key(self.PREFIX_ANALYZE, analysis_input)
        return self.get(key)

    def cache_generate_result(
        self,
        requirements: dict,
        limit: int,
        result: dict,
        ttl: int = 900,
    ) -> None:
        """
        缓存生成结果

        Args:
            requirements: 需求
            limit: 数量限制
            result: 生成结果
            ttl: 过期时间（秒）
        """
        key = self._generate_key(self.PREFIX_GENERATE, requirements, limit)
        self.set(key, result, ttl)

    def get_generate_result(self, requirements: dict, limit: int) -> Optional[dict]:
        """
        获取缓存的生成结果

        Args:
            requirements: 需求
            limit: 数量限制

        Returns:
            生成结果，如果不存在则返回None
        """
        key = self._generate_key(self.PREFIX_GENERATE, requirements, limit)
        return self.get(key)

    def clear_user_cache(self, user_id: int) -> int:
        """
        清空指定用户的所有缓存

        Args:
            user_id: 用户ID

        Returns:
            清空的缓存数量
        """
        # 目前使用全局缓存，所以清空全部
        # 如果使用Redis，可以根据user_id删除
        return self.clear_prefix(f"booklist:{user_id}")


# 全局缓存服务实例
book_list_cache = BookListCache(ttl=3600)


def get_book_list_cache() -> BookListCache:
    """获取书单缓存服务实例"""
    return book_list_cache


class AgentCache:
    """
    Agent 结果缓存管理器（Phase 2 增强版）
    实现多级缓存策略：内存缓存 + Redis 缓存
    """

    def __init__(self, redis_client=None):
        """
        初始化缓存管理器

        Args:
            redis_client: Redis 客户端
        """
        self.redis = redis_client
        self.memory_cache = {}  # 内存缓存
        self.memory_cache_ttl = {}  # 内存缓存过期时间

        # 默认 TTL 配置（秒）
        self.default_ttl = {
            "vector_search": 300,  # 5分钟
            "db_query": 600,  # 10分钟
            "requirement_analysis": 1800,  # 30分钟
            "retrieval": 300,  # 5分钟
            "recommendation": 600,  # 10分钟
            "evaluation": 300,  # 5分钟
            "popular_books": 1800,  # 30分钟
            "user_preferences": 3600,  # 1小时
            "booklist_result": 1800,  # 30分钟
        }

        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def cache_result(
            self,
            func_name: str,
            ttl: int = None,
            use_memory: bool = True,
            use_redis: bool = True
    ):
        """
        缓存装饰器

        Args:
            func_name: 函数名，用于确定 TTL
            ttl: 自定义 TTL（秒）
            use_memory: 是否使用内存缓存
            use_redis: 是否使用 Redis 缓存

        Returns:
            装饰器函数
        """

        def decorator(func):
            import functools

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_key(func_name or func.__name__, args, kwargs)

                # 尝试从缓存获取
                cached_value = await self._get_from_cache(cache_key, use_memory, use_redis)

                if cached_value is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    self.stats["hits"] += 1
                    return cached_value

                # 执行函数
                self.stats["misses"] += 1
                result = await func(*args, **kwargs)

                # 存入缓存
                if result is not None:
                    cache_ttl = ttl or self.default_ttl.get(func_name, 300)
                    await self._set_to_cache(cache_key, result, cache_ttl, use_memory, use_redis)

                return result

            return async_wrapper

        return decorator

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_parts = ["agent", func_name]

        # 序列化参数
        try:
            args_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
            args_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]
            key_parts.append(args_hash)
        except:
            key_parts.append(str(args))
            key_parts.append(str(kwargs))

        return ":".join(key_parts)

    async def _get_from_cache(self, key: str, use_memory: bool, use_redis: bool) -> Any:
        """从缓存获取值（多级缓存）"""
        # 1. 先查内存缓存
        if use_memory:
            value = self._get_from_memory(key)
            if value is not None:
                return value

        # 2. 再查 Redis
        if use_redis and self.redis:
            value = await self._get_from_redis(key)
            if value is not None and use_memory:
                # 回填到内存缓存
                self._set_to_memory(key, value, 60)
            return value

        return None

    def _get_from_memory(self, key: str) -> Any:
        """从内存缓存获取"""
        if key not in self.memory_cache:
            return None

        # 检查是否过期
        if key in self.memory_cache_ttl:
            if time.time() > self.memory_cache_ttl[key]:
                # 过期，删除
                del self.memory_cache[key]
                del self.memory_cache_ttl[key]
                self.stats["evictions"] += 1
                return None

        return self.memory_cache[key]

    async def _get_from_redis(self, key: str) -> Any:
        """从 Redis 获取（使用安全的 JSON 序列化）"""
        if not self.redis:
            return None

        try:
            data = await self.redis.get(key)
            if data:
                # 使用 JSON 替代 pickle，避免远程代码执行风险
                return json.loads(data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Redis get decode error: {e}")
        except Exception as e:
            logger.error(f"Redis get error: {e}")

        return None

    async def _set_to_cache(self, key: str, value: Any, ttl: int, use_memory: bool, use_redis: bool):
        """存入缓存"""
        if use_memory:
            self._set_to_memory(key, value, ttl)

        if use_redis and self.redis:
            await self._set_to_redis(key, value, ttl)

    def _set_to_memory(self, key: str, value: Any, ttl: int):
        """存入内存缓存"""
        # 简单的内存管理：如果缓存太大，删除最老的项
        if len(self.memory_cache) >= 1000:
            # 删除最老的 10% 数据
            sorted_keys = sorted(self.memory_cache_ttl.items(), key=lambda x: x[1])
            for old_key, _ in sorted_keys[:100]:
                del self.memory_cache[old_key]
                del self.memory_cache_ttl[old_key]
                self.stats["evictions"] += 1

        self.memory_cache[key] = value
        self.memory_cache_ttl[key] = time.time() + ttl

    async def _set_to_redis(self, key: str, value: Any, ttl: int):
        """存入 Redis（使用安全的 JSON 序列化）"""
        if not self.redis:
            return

        try:
            # 使用 JSON 替代 pickle，避免远程代码执行风险
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized)
        except (TypeError, ValueError) as e:
            logger.error(f"Redis set serialize error: {e}")
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self.stats["evictions"],
            "memory_cache_size": len(self.memory_cache),
        }


# 全局 Agent 缓存实例
agent_cache = AgentCache()


def get_agent_cache() -> AgentCache:
    """获取 Agent 缓存服务实例"""
    return agent_cache
