"""
Conversation Manager - 多轮对话管理

用于维护和管理多轮对话的上下文，包括：
1. 对话历史记录
2. 上下文融合
3. 对话状态管理
4. 自动摘要生成
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Message:
    """单条消息"""
    
    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.role = role  # "user" 或 "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            metadata=data.get("metadata", {}),
        )


class ConversationContext:
    """对话上下文"""
    
    def __init__(
        self,
        session_id: int,
        user_id: int,
        max_history_length: int = 10
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.max_history_length = max_history_length
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """添加消息"""
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # 防止历史过长
        if len(self.messages) > self.max_history_length * 2:
            # 保留最后 max_history_length 条消息
            self.messages = self.messages[-self.max_history_length:]
        
        return message
    
    def get_recent_messages(self, count: int = 5) -> List[Message]:
        """获取最近的消息"""
        return self.messages[-count:]
    
    def get_context_for_llm(self, count: int = 5) -> List[Dict[str, str]]:
        """获取用于 LLM 的对话上下文"""
        recent = self.get_recent_messages(count)
        return [{"role": msg.role, "content": msg.content} for msg in recent]
    
    def get_summary(self) -> str:
        """获取对话摘要"""
        if not self.messages:
            return ""
        
        # 简单的摘要：取出所有用户消息的关键内容
        user_messages = [m.content for m in self.messages if m.role == "user"]
        return "\n".join(user_messages[-3:])  # 最后 3 条用户消息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """从字典创建"""
        ctx = cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
        )
        ctx.messages = [Message.from_dict(m) for m in data.get("messages", [])]
        ctx.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        ctx.updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        return ctx


class ConversationManager:
    """
    多轮对话管理器
    
    负责管理对话的上下文、历史和状态
    """
    
    def __init__(self, db: Session, cache_service=None):
        self.db = db
        self.cache_service = cache_service
        self._contexts: Dict[int, ConversationContext] = {}  # 内存缓存
    
    def create_conversation(
        self,
        session_id: int,
        user_id: int
    ) -> ConversationContext:
        """创建新的对话"""
        ctx = ConversationContext(session_id=session_id, user_id=user_id)
        self._contexts[session_id] = ctx
        
        # 保存到缓存
        if self.cache_service:
            cache_key = f"conversation:{session_id}"
            self.cache_service.set(cache_key, ctx.to_dict(), ttl=3600)
        
        logger.info(f"创建对话: session_id={session_id}, user_id={user_id}")
        return ctx
    
    def get_conversation(
        self,
        session_id: int,
        create_if_missing: bool = False
    ) -> Optional[ConversationContext]:
        """获取对话"""
        # 先从内存获取
        if session_id in self._contexts:
            return self._contexts[session_id]
        
        # 从缓存获取
        if self.cache_service:
            cache_key = f"conversation:{session_id}"
            cached = self.cache_service.get(cache_key)
            if cached:
                ctx = ConversationContext.from_dict(cached)
                self._contexts[session_id] = ctx
                return ctx
        
        # 从数据库获取（如果有对话存储表）
        try:
            from app.models import BookListSession
            session = self.db.query(BookListSession).filter(
                BookListSession.id == session_id
            ).first()
            
            if session and session.user_feedbacks:
                ctx = ConversationContext(
                    session_id=session_id,
                    user_id=session.user_id
                )
                
                # 重建对话历史
                for feedback in session.user_feedbacks:
                    if isinstance(feedback, dict):
                        ctx.add_message("user", feedback.get("content", ""))
                
                self._contexts[session_id] = ctx
                return ctx
        except Exception as e:
            logger.warning(f"从数据库获取对话失败: {str(e)}")
        
        # 如果不存在且需要创建
        if create_if_missing:
            return self.create_conversation(session_id, user_id=0)
        
        return None
    
    def add_user_message(
        self,
        session_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """添加用户消息"""
        ctx = self.get_conversation(session_id, create_if_missing=True)
        if not ctx:
            return None
        
        message = ctx.add_message("user", content, metadata)
        self._save_conversation(ctx)
        
        logger.debug(f"添加用户消息: session_id={session_id}")
        return message
    
    def add_assistant_message(
        self,
        session_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """添加助手消息"""
        ctx = self.get_conversation(session_id)
        if not ctx:
            logger.warning(f"对话不存在: session_id={session_id}")
            return None
        
        message = ctx.add_message("assistant", content, metadata)
        self._save_conversation(ctx)
        
        logger.debug(f"添加助手消息: session_id={session_id}")
        return message
    
    def get_context_for_llm(
        self,
        session_id: int,
        recent_count: int = 5
    ) -> List[Dict[str, str]]:
        """获取用于 LLM 的上下文"""
        ctx = self.get_conversation(session_id)
        if not ctx:
            return []
        
        return ctx.get_context_for_llm(recent_count)
    
    def get_conversation_summary(
        self,
        session_id: int
    ) -> str:
        """获取对话摘要"""
        ctx = self.get_conversation(session_id)
        if not ctx:
            return ""
        
        return ctx.get_summary()
    
    def clear_conversation(self, session_id: int) -> None:
        """清空对话"""
        if session_id in self._contexts:
            del self._contexts[session_id]
        
        if self.cache_service:
            cache_key = f"conversation:{session_id}"
            self.cache_service.delete(cache_key)
        
        logger.info(f"清空对话: session_id={session_id}")
    
    def get_all_conversations_info(self) -> Dict[int, Dict[str, Any]]:
        """获取所有对话的信息"""
        return {
            session_id: {
                "message_count": len(ctx.messages),
                "created_at": ctx.created_at.isoformat(),
                "updated_at": ctx.updated_at.isoformat(),
                "summary": ctx.get_summary(),
            }
            for session_id, ctx in self._contexts.items()
        }
    
    def _save_conversation(self, ctx: ConversationContext) -> None:
        """保存对话"""
        try:
            if self.cache_service:
                cache_key = f"conversation:{ctx.session_id}"
                self.cache_service.set(cache_key, ctx.to_dict(), ttl=3600)
                
                # 也保存最后一条消息为快速查询
                if ctx.messages:
                    last_msg = ctx.messages[-1]
                    self.cache_service.set(
                        f"conversation:{ctx.session_id}:last",
                        last_msg.to_dict(),
                        ttl=3600
                    )
        except Exception as e:
            logger.warning(f"保存对话失败: {str(e)}")
    
    def cleanup_old_conversations(self, max_age_hours: int = 24) -> None:
        """清理旧对话"""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=max_age_hours)
        
        expired_sessions = [
            session_id for session_id, ctx in self._contexts.items()
            if ctx.updated_at < cutoff_time
        ]
        
        for session_id in expired_sessions:
            self.clear_conversation(session_id)
        
        if expired_sessions:
            logger.info(f"清理过期对话: {len(expired_sessions)} 个")


class MultiRoundConversationService:
    """
    多轮对话服务
    
    集成对话管理和 LLM 调用
    """
    
    def __init__(
        self,
        llm_service,
        conversation_manager: ConversationManager
    ):
        self.llm_service = llm_service
        self.conversation_manager = conversation_manager
    
    async def chat(
        self,
        session_id: int,
        user_message: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        多轮对话聊天
        
        Args:
            session_id: 会话 ID
            user_message: 用户消息
            system_prompt: 系统提示词（可选）
            
        Returns:
            助手的回复
        """
        # 添加用户消息
        self.conversation_manager.add_user_message(session_id, user_message)
        
        # 获取对话上下文
        context = self.conversation_manager.get_context_for_llm(session_id)
        
        # 构建完整的消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(context)
        
        # 调用 LLM
        try:
            response = self.llm_service.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            
            # 添加助手消息
            self.conversation_manager.add_assistant_message(session_id, response)
            
            logger.info(f"多轮对话完成: session_id={session_id}")
            return response
        
        except Exception as e:
            logger.error(f"多轮对话失败: {str(e)}", exc_info=True)
            raise
    
    def get_conversation_info(self, session_id: int) -> Dict[str, Any]:
        """获取对话信息"""
        ctx = self.conversation_manager.get_conversation(session_id)
        if not ctx:
            return {}
        
        return {
            "session_id": session_id,
            "message_count": len(ctx.messages),
            "created_at": ctx.created_at.isoformat(),
            "updated_at": ctx.updated_at.isoformat(),
            "summary": ctx.get_summary(),
            "recent_messages": [
                m.to_dict() for m in ctx.get_recent_messages(3)
            ],
        }
