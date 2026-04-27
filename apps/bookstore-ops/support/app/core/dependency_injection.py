"""
依赖注入系统
"""
from typing import Any, Callable, Dict, Optional, Type

import logging

logger = logging.getLogger(__name__)


class ServiceContainer:
    """服务容器，用于依赖注入"""

    def __init__(self):
        """初始化服务容器"""
        self.services: Dict[str, Dict[str, Any]] = {}
        self.instances: Dict[str, Any] = {}

    def register(self, service_id: str, service_class: Type, **kwargs):
        """
        注册服务

        Args:
            service_id: 服务ID
            service_class: 服务类
            **kwargs: 服务初始化参数
        """
        self.services[service_id] = {
            "class": service_class,
            "params": kwargs,
            "instance": None,
        }
        logger.info(f"Service registered: {service_id}")

    def register_singleton(self, service_id: str, service_class: Type, **kwargs):
        """
        注册单例服务

        Args:
            service_id: 服务ID
            service_class: 服务类
            **kwargs: 服务初始化参数
        """
        self.services[service_id] = {
            "class": service_class,
            "params": kwargs,
            "instance": None,
            "singleton": True,
        }
        logger.info(f"Singleton service registered: {service_id}")

    def register_factory(self, service_id: str, factory: Callable, **kwargs):
        """
        注册工厂服务

        Args:
            service_id: 服务ID
            factory: 服务工厂函数
            **kwargs: 工厂函数参数
        """
        self.services[service_id] = {"factory": factory, "params": kwargs}
        logger.info(f"Factory service registered: {service_id}")

    def resolve(self, service_id: str) -> Any:
        """
        解析服务

        Args:
            service_id: 服务ID

        Returns:
            服务实例
        """
        if service_id in self.instances:
            return self.instances[service_id]

        if service_id not in self.services:
            raise ValueError(f"Service not registered: {service_id}")

        service_def = self.services[service_id]

        # 处理工厂服务
        if "factory" in service_def:
            factory = service_def["factory"]
            params = self._resolve_params(service_def["params"])
            instance = factory(**params)
            logger.info(f"Factory service resolved: {service_id}")
            return instance

        # 处理普通服务
        service_class = service_def["class"]
        params = self._resolve_params(service_def["params"])

        try:
            instance = service_class(**params)
            logger.info(f"Service resolved: {service_id}")

            # 如果是单例，缓存实例
            if service_def.get("singleton", False):
                self.instances[service_id] = instance

            return instance
        except Exception as e:
            logger.error(f"Failed to resolve service {service_id}: {e}")
            raise

    def _resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析参数中的服务引用

        Args:
            params: 原始参数

        Returns:
            解析后的参数
        """
        resolved_params = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("@"):
                # 解析服务引用
                ref_service_id = value[1:]
                resolved_params[key] = self.resolve(ref_service_id)
            else:
                resolved_params[key] = value
        return resolved_params

    def has_service(self, service_id: str) -> bool:
        """
        检查服务是否已注册

        Args:
            service_id: 服务ID

        Returns:
            是否已注册
        """
        return service_id in self.services

    def clear(self):
        """
        清空服务容器
        """
        self.services.clear()
        self.instances.clear()
        logger.info("Service container cleared")


# 创建全局服务容器实例
service_container = ServiceContainer()
