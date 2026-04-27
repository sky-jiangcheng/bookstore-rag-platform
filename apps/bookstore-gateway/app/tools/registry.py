"""
工具注册和管理系统
用于 Agent 的工具发现和调用
"""

from typing import Dict, Any, Callable, List
from functools import wraps
import asyncio


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self, 
        name: str, 
        func: Callable, 
        description: str = "",
        parameters: Dict[str, Any] = None
    ):
        """注册工具"""
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {}
        }
    
    async def execute(self, name: str, params: Dict[str, Any] = None) -> Any:
        """异步执行工具"""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found. Available: {list(self._tools.keys())}")
        
        tool = self._tools[name]
        func = tool["func"]
        params = params or {}
        
        # 检查是否为异步函数
        if asyncio.iscoroutinefunction(func):
            return await func(**params)
        else:
            # 同步函数在线程池中运行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(**params))
    
    def list_tools(self) -> List[str]:
        """列出所有可用工具"""
        return list(self._tools.keys())
    
    def get_tool_info(self, name: str) -> Dict[str, Any]:
        """获取工具信息"""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        
        tool = self._tools[name]
        return {
            "name": name,
            "description": tool["description"],
            "parameters": tool["parameters"]
        }


# 全局工具注册表实例
tool_registry = ToolRegistry()


def tool(name: str = None, description: str = ""):
    """工具装饰器"""
    def decorator(func: Callable):
        tool_name = name or func.__name__
        tool_registry.register(
            name=tool_name,
            func=func,
            description=description or func.__doc__ or ""
        )
        return func
    return decorator
