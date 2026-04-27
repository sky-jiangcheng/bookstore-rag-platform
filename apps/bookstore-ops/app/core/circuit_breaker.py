"""
Circuit Breaker 熔断机制

用于防止级联故障，当某个服务出现问题时：
1. CLOSED（正常）- 正常调用
2. OPEN（断路）- 快速失败
3. HALF_OPEN（半开）- 尝试恢复

这个实现支持：
- 失败次数阈值
- 时间窗口重置
- 自动恢复
- 事件回调
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 正常状态
    OPEN = "open"          # 断路状态
    HALF_OPEN = "half_open"  # 半开状态（尝试恢复）


class CircuitBreakerListener:
    """熔断器监听器基类"""
    
    async def on_state_change(
        self,
        old_state: CircuitState,
        new_state: CircuitState,
        name: str
    ) -> None:
        """状态改变时调用"""
        pass
    
    async def on_success(self, name: str, duration_ms: int) -> None:
        """调用成功时"""
        pass
    
    async def on_failure(self, name: str, exception: Exception) -> None:
        """调用失败时"""
        pass
    
    async def on_circuit_open(self, name: str) -> None:
        """熔断器打开时"""
        pass


class AlertListener(CircuitBreakerListener):
    """告警监听器"""
    
    def __init__(self, alert_message: str):
        self.alert_message = alert_message
    
    async def on_circuit_open(self, name: str) -> None:
        """熔断器打开时发送告警"""
        logger.error(
            f"⚠️  {self.alert_message} - 服务 {name} 熔断器已打开"
        )


class CircuitBreaker:
    """
    熔断器实现
    
    用于防止级联故障，当服务出现问题时快速失败
    """
    
    def __init__(
        self,
        name: str = "CircuitBreaker",
        fail_max: int = 5,
        reset_timeout: int = 60,
        listeners: Optional[List[CircuitBreakerListener]] = None
    ):
        """
        初始化熔断器
        
        Args:
            name: 熔断器名称
            fail_max: 最大失败次数
            reset_timeout: 重置超时时间（秒）
            listeners: 监听器列表
        """
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.listeners = listeners or []
        
        self._state = CircuitState.CLOSED
        self._fail_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_state_change_time = time.time()
    
    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        return self._state
    
    @property
    def is_closed(self) -> bool:
        """是否关闭（正常）"""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """是否打开（断路）"""
        return self._state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """是否半开（尝试恢复）"""
        return self._state == CircuitState.HALF_OPEN
    
    async def call(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        通过熔断器调用函数
        
        Args:
            func: 要调用的函数
            fallback: 降级函数（可选）
            *args, **kwargs: 函数参数
            
        Returns:
            函数返回值
        """
        # 检查是否需要更新状态
        await self._check_state_transition()
        
        # 如果熔断器打开，使用降级或快速失败
        if self.is_open:
            logger.warning(
                f"熔断器 {self.name} 处于开启状态，使用降级策略"
            )
            if fallback:
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            else:
                raise Exception(f"熔断器 {self.name} 已打开，服务暂时不可用")
        
        # 执行函数
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            
            duration_ms = int((time.time() - start_time) * 1000)
            await self._record_success(duration_ms)
            
            return result
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await self._record_failure(e, duration_ms)
            
            # 如果有降级函数，使用降级
            if fallback:
                logger.warning(
                    f"熔断器 {self.name} 中的函数执行失败，使用降级策略: {str(e)}"
                )
                return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
            else:
                raise
    
    async def _check_state_transition(self) -> None:
        """检查状态转换"""
        if self.is_open:
            # 检查是否应该从 OPEN 转换到 HALF_OPEN
            if time.time() - self._last_state_change_time > self.reset_timeout:
                await self._set_state(CircuitState.HALF_OPEN)
                self._success_count = 0
    
    async def _record_success(self, duration_ms: int) -> None:
        """记录成功"""
        self._fail_count = 0
        
        # 如果处于 HALF_OPEN 状态，尝试关闭
        if self.is_half_open:
            self._success_count += 1
            if self._success_count >= 2:  # 连续 2 次成功则关闭
                await self._set_state(CircuitState.CLOSED)
        
        # 通知监听器
        for listener in self.listeners:
            await listener.on_success(self.name, duration_ms)
    
    async def _record_failure(
        self,
        exception: Exception,
        duration_ms: int
    ) -> None:
        """记录失败"""
        self._fail_count += 1
        self._last_failure_time = time.time()
        
        logger.error(
            f"熔断器 {self.name} 记录失败 "
            f"(失败次数: {self._fail_count}/{self.fail_max}): {str(exception)}"
        )
        
        # 如果失败次数达到阈值，打开熔断器
        if self._fail_count >= self.fail_max:
            await self._set_state(CircuitState.OPEN)
        
        # 通知监听器
        for listener in self.listeners:
            await listener.on_failure(self.name, exception)
    
    async def _set_state(self, new_state: CircuitState) -> None:
        """设置状态"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._last_state_change_time = time.time()
            
            logger.info(
                f"熔断器 {self.name} 状态转换: "
                f"{old_state.value} → {new_state.value}"
            )
            
            # 通知监听器
            for listener in self.listeners:
                await listener.on_state_change(old_state, new_state, self.name)
            
            # 如果转换到 OPEN 状态，发送特殊通知
            if new_state == CircuitState.OPEN:
                for listener in self.listeners:
                    await listener.on_circuit_open(self.name)
    
    def reset(self) -> None:
        """手动重置熔断器"""
        self._fail_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
        logger.info(f"熔断器 {self.name} 已重置")
    
    def get_status(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "name": self.name,
            "state": self._state.value,
            "fail_count": self._fail_count,
            "fail_max": self.fail_max,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "reset_timeout": self.reset_timeout,
        }


class CircuitBreakerRegistry:
    """
    熔断器注册表
    
    集中管理所有熔断器
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def register(
        self,
        name: str,
        fail_max: int = 5,
        reset_timeout: int = 60,
        listeners: Optional[List[CircuitBreakerListener]] = None
    ) -> CircuitBreaker:
        """注册熔断器"""
        breaker = CircuitBreaker(
            name=name,
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            listeners=listeners
        )
        self._breakers[name] = breaker
        return breaker
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """获取熔断器"""
        return self._breakers.get(name)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有熔断器的状态"""
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self) -> None:
        """重置所有熔断器"""
        for breaker in self._breakers.values():
            breaker.reset()


# 全局熔断器注册表
breaker_registry = CircuitBreakerRegistry()


# 便捷函数
def create_circuit_breaker(
    name: str,
    fail_max: int = 5,
    reset_timeout: int = 60,
    alert_message: Optional[str] = None
) -> CircuitBreaker:
    """创建并注册熔断器"""
    listeners = []
    if alert_message:
        listeners.append(AlertListener(alert_message))
    
    return breaker_registry.register(
        name=name,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        listeners=listeners
    )


from typing import Dict
