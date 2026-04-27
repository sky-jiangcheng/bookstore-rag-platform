"""
工作流编排器
整合三个 Agent，提供端到端的书单生成服务
"""

from typing import Dict, Any, Optional, AsyncIterator
import asyncio
import logging
from datetime import datetime
import uuid

from .requirement_agent import RequirementAgent
from .retrieval_agent import RetrievalAgent
from .recommendation_agent import RecommendationAgent
from .models import BookListResult, RequirementAnalysis

logger = logging.getLogger(__name__)


class BookListWorkflow:
    """
    书单生成工作流
    编排 RequirementAgent → RetrievalAgent → RecommendationAgent
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.req_agent = RequirementAgent()
        self.retrieval_agent = RetrievalAgent()
        self.rec_agent = RecommendationAgent()
        self.history = []
        
    async def execute(
        self, 
        user_input: str,
        stream: bool = True,
        target_count: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        执行完整工作流
        
        Args:
            user_input: 用户输入
            stream: 是否流式输出
            
        Yields:
            Dict: 包含步骤类型和数据的字典
        """
        try:
            # 记录开始
            logger.info(f"[{self.session_id}] 开始处理请求: {user_input[:50]}...")
            yield {
                "type": "start",
                "content": "开始生成书单...",
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # ========== Step 1: 需求分析 ==========
            yield {
                "type": "step_start",
                "step": 1,
                "step_name": "需求分析",
                "content": "正在分析您的阅读需求..."
            }
            
            async for msg in self.req_agent.analyze_streaming(user_input):
                if stream:
                    yield {**msg, "step": 1}
            
            # 获取最终结果（使用 await 等待协程执行）
            requirement = await self.req_agent.analyze(user_input)
            
            yield {
                "type": "step_complete",
                "step": 1,
                "step_name": "需求分析",
                "content": "需求分析完成",
                "data": {
                    "target_audience": requirement.target_audience,
                    "categories": requirement.categories,
                    "keywords": requirement.keywords,
                    "confidence": requirement.confidence,
                    "needs_clarification": requirement.needs_clarification
                }
            }
            
            # 检查是否需要澄清
            if requirement.needs_clarification:
                yield {
                    "type": "clarification_needed",
                    "content": "需要更多信息",
                    "questions": requirement.clarification_questions,
                    "session_id": self.session_id
                }
                return
            
            # ========== Step 2: 智能检索 ==========
            yield {
                "type": "step_start",
                "step": 2,
                "step_name": "智能检索",
                "content": "正在从书库中检索相关书籍..."
            }
            
            # 执行检索
            candidates = await self.retrieval_agent.retrieve(requirement.__dict__)
            
            yield {
                "type": "step_complete",
                "step": 2,
                "step_name": "智能检索",
                "content": f"检索完成，找到 {len(candidates)} 本候选书籍",
                "data": {
                    "candidate_count": len(candidates),
                    "strategy": "hybrid"  # 可以记录实际使用的策略
                }
            }
            
            # 如果没有找到候选书籍
            if not candidates:
                yield {
                    "type": "error",
                    "content": "未找到符合条件的书籍",
                    "error_code": "NO_CANDIDATES",
                    "session_id": self.session_id
                }
                return
            
            # ========== Step 3: 生成书单 ==========
            yield {
                "type": "step_start",
                "step": 3,
                "step_name": "生成书单",
                "content": "正在为您精选书籍..."
            }
            
            # 生成书单
            booklist = self.rec_agent.generate_booklist(
                requirement=requirement.__dict__,
                candidates=candidates,
                target_count=target_count
            )
            
            yield {
                "type": "step_complete",
                "step": 3,
                "step_name": "生成书单",
                "content": "书单生成完成",
                "data": {
                    "book_count": len(booklist.books),
                    "quality_score": booklist.quality_score,
                    "total_price": booklist.total_price,
                    "confidence": booklist.confidence
                }
            }
            
            # ========== 最终结果 ==========
            yield {
                "type": "complete",
                "content": "书单生成完成！",
                "session_id": self.session_id,
                "requirement": {
                    "target_audience": requirement.target_audience,
                    "categories": requirement.categories,
                    "keywords": requirement.keywords,
                    "constraints": requirement.constraints
                },
                "booklist": {
                    "books": [
                        {
                            "book_id": b.book_id,
                            "title": b.title,
                            "author": b.author,
                            "publisher": b.publisher,
                            "price": b.price,
                            "stock": b.stock,
                            "category": b.category,
                            "relevance_score": b.relevance_score
                        }
                        for b in booklist.books
                    ],
                    "total_price": booklist.total_price,
                    "quality_score": booklist.quality_score,
                    "confidence": booklist.confidence,
                    "category_distribution": booklist.category_distribution
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 记录历史
            self.history.append({
                "input": user_input,
                "requirement": requirement.__dict__,
                "booklist": booklist,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"[{self.session_id}] 书单生成完成: {len(booklist.books)} 本书")
            
        except Exception as e:
            logger.error(f"[{self.session_id}] 工作流执行失败: {str(e)}")
            yield {
                "type": "error",
                "content": f"生成书单时发生错误: {str(e)}",
                "error_code": "WORKFLOW_ERROR",
                "session_id": self.session_id
            }
    
    async def execute_sync(
        self, 
        user_input: str,
        target_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同步执行工作流（返回最终结果）
        
        Args:
            user_input: 用户输入
            
        Returns:
            Dict: 完整结果
        """
        result = None
        async for msg in self.execute(user_input, stream=False, target_count=target_count):
            if msg["type"] in ["complete", "error", "clarification_needed"]:
                result = msg
        return result or {"type": "error", "content": "执行失败"}


class WorkflowManager:
    """
    工作流管理器
    管理多个会话的工作流实例
    """
    
    def __init__(self):
        self.workflows: Dict[str, BookListWorkflow] = {}
        self.max_history = 100
    
    def create_workflow(self, session_id: Optional[str] = None) -> BookListWorkflow:
        """
        创建新工作流
        
        Args:
            session_id: 可选的会话ID
            
        Returns:
            BookListWorkflow: 工作流实例
        """
        workflow = BookListWorkflow(session_id)
        self.workflows[workflow.session_id] = workflow
        
        # 清理旧会话
        if len(self.workflows) > self.max_history:
            oldest = min(self.workflows.keys(), 
                        key=lambda k: self.workflows[k].history[0]["timestamp"] 
                        if self.workflows[k].history else "")
            del self.workflows[oldest]
        
        return workflow
    
    def get_workflow(self, session_id: str) -> Optional[BookListWorkflow]:
        """
        获取已存在的工作流
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[BookListWorkflow]: 工作流实例或None
        """
        return self.workflows.get(session_id)
    
    def remove_workflow(self, session_id: str):
        """
        移除工作流
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.workflows:
            del self.workflows[session_id]


# 全局工作流管理器实例
workflow_manager = WorkflowManager()
