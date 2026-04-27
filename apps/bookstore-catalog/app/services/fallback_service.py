"""
降级策略
当 Agent 服务失败时的回退机制
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..agents.workflow import BookListWorkflow
from ..tools.registry import tool_registry

logger = logging.getLogger(__name__)


class FallbackStrategy:
    """
    降级策略管理器
    当主服务失败时提供备用方案
    """
    
    def __init__(self):
        self.failure_count = 0
        self.max_failures = 3
        self.last_failure_time = None
        self.cooldown_period = 60  # 冷却期（秒）
    
    async def execute_with_fallback(
        self, 
        user_input: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        带降级的执行
        
        先尝试 Agent 方案，失败时降级到规则引擎
        """
        try:
            # 检查是否在冷却期
            if self._is_in_cooldown():
                logger.warning("Agent service in cooldown, using fallback")
                return await self._fallback_recommendation(user_input)
            
            # 尝试 Agent 方案
            workflow = BookListWorkflow(session_id)
            result = await workflow.execute_sync(user_input)
            
            # 成功则重置失败计数
            if result.get("type") == "complete":
                self._reset_failure_count()
                return result
            
            # 如果需要澄清，直接返回
            if result.get("type") == "clarification_needed":
                return result
            
            # 其他情况（如错误）
            raise Exception(result.get("content", "Unknown error"))
            
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            self._record_failure()
            
            # 降级到规则引擎
            return await self._fallback_recommendation(user_input)
    
    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却期"""
        if self.failure_count >= self.max_failures and self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            return elapsed < self.cooldown_period
        return False
    
    def _record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        logger.warning(f"Failure recorded. Count: {self.failure_count}")
    
    def _reset_failure_count(self):
        """重置失败计数"""
        if self.failure_count > 0:
            self.failure_count = 0
            self.last_failure_time = None
            logger.info("Failure count reset")
    
    async def _fallback_recommendation(self, user_input: str) -> Dict[str, Any]:
        """
        降级推荐方案
        
        使用简单的关键词匹配进行推荐
        """
        logger.info("Using fallback recommendation strategy")
        
        try:
            # 从用户输入提取关键词
            keywords = self._extract_keywords(user_input)
            
            # 使用向量搜索
            candidates = await tool_registry.execute(
                "vector_search",
                {"query": " ".join(keywords), "top_k": 10}
            )
            
            # 检查库存
            if candidates:
                book_ids = [b["book_id"] for b in candidates]
                inventory = await tool_registry.execute(
                    "check_inventory",
                    {"book_ids": book_ids}
                )
                
                # 过滤有库存的
                available = [
                    {**b, "stock": inventory.get(b["book_id"], 0)}
                    for b in candidates
                    if inventory.get(b["book_id"], 0) > 0
                ]
                
                if available:
                    return {
                        "type": "complete",
                        "content": "书单生成完成（使用降级方案）",
                        "session_id": None,
                        "booklist": {
                            "books": available[:10],
                            "total_price": sum(b.get("price", 0) for b in available[:10]),
                            "quality_score": 0.5,  # 降级方案质量分较低
                            "confidence": 0.5,
                            "category_distribution": {}
                        },
                        "is_fallback": True,
                        "fallback_reason": "Agent service temporarily unavailable"
                    }
            
            # 如果没有找到书籍
            return {
                "type": "error",
                "content": "暂时无法生成书单，请稍后重试",
                "error_code": "FALLBACK_NO_RESULTS",
                "is_fallback": True
            }
            
        except Exception as e:
            logger.error(f"Fallback recommendation also failed: {str(e)}")
            return {
                "type": "error",
                "content": "服务暂时不可用，请稍后重试",
                "error_code": "SERVICE_UNAVAILABLE",
                "is_fallback": True
            }
    
    def _extract_keywords(self, text: str) -> list:
        """从文本中提取关键词"""
        # 停用词列表
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', 
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那'
        }
        
        # 分词（简单按空格和标点分割）
        import re
        words = re.findall(r'\b\w+\b', text)
        
        # 过滤停用词和短词
        keywords = [
            w for w in words 
            if len(w) >= 2 and w not in stopwords
        ]
        
        # 如果没有提取到关键词，返回原文本
        if not keywords:
            keywords = [text]
        
        return keywords[:5]  # 最多返回5个关键词


# 全局降级策略实例
fallback_strategy = FallbackStrategy()


async def execute_with_fallback(user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    便捷函数：带降级的执行
    """
    return await fallback_strategy.execute_with_fallback(user_input, session_id)
