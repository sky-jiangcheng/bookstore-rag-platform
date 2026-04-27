"""
记忆系统
管理用户偏好、历史书单和对话记忆
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import BookListHistory, BookListResult, UserPreference

logger = logging.getLogger(__name__)


class BookListMemory:
    """
    书单推荐记忆系统
    管理短期对话记忆和长期用户画像
    """

    def __init__(self, redis_client=None, db_session=None):
        """
        初始化记忆系统

        Args:
            redis_client: Redis 客户端（短期记忆）
            db_session: 数据库会话（长期记忆）
        """
        self.short_term = redis_client  # 短期对话记忆
        self.long_term = db_session  # 长期用户画像
        self.max_recent_dialogues = 5
        self.max_history_booklists = 10

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户上下文（整合短期和长期记忆）

        Args:
            user_id: 用户ID

        Returns:
            Dict: 包含用户画像、历史对话和书单的上下文
        """
        context = {
            "user_id": user_id,
            "recent_dialogues": [],
            "preferences": {},
            "history_booklists": [],
            "statistics": {},
        }

        try:
            # 1. 获取短期记忆（最近对话）
            if self.short_term:
                recent = await self._get_recent_dialogues(user_id)
                context["recent_dialogues"] = recent

            # 2. 获取长期记忆（用户画像）
            preferences = await self._get_user_preferences(user_id)
            if preferences:
                context["preferences"] = asdict(preferences)

            # 3. 获取历史书单
            history = await self._get_history_booklists(user_id)
            context["history_booklists"] = history

            # 4. 生成统计信息
            context["statistics"] = self._calculate_statistics(history)

        except Exception as e:
            logger.error(f"Error getting user context: {e}")

        return context

    async def save_dialogue(
        self, user_id: str, session_id: str, user_input: str, response: Dict[str, Any]
    ):
        """
        保存对话记录

        Args:
            user_id: 用户ID
            session_id: 会话ID
            user_input: 用户输入
            response: 系统响应
        """
        if not self.short_term:
            return

        try:
            dialogue = {
                "user_input": user_input,
                "response_type": response.get("type"),
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
            }

            # 保存到 Redis 列表
            key = f"dialogue:{user_id}"
            await self.short_term.lpush(key, json.dumps(dialogue))

            # 只保留最近的 N 条
            await self.short_term.ltrim(key, 0, self.max_recent_dialogues - 1)

            # 设置过期时间（7天）
            await self.short_term.expire(key, 7 * 24 * 3600)

        except Exception as e:
            logger.error(f"Error saving dialogue: {e}")

    async def save_booklist(
        self,
        user_id: str,
        session_id: str,
        requirement: Dict[str, Any],
        booklist: BookListResult,
        feedback: Optional[Dict[str, Any]] = None,
    ):
        """
        保存书单历史

        Args:
            user_id: 用户ID
            session_id: 会话ID
            requirement: 需求分析
            booklist: 生成的书单
            feedback: 用户反馈（可选）
        """
        try:
            # 构建书单历史记录
            history = BookListHistory(
                user_id=user_id,
                session_id=session_id,
                requirement=requirement,
                booklist=booklist,
                feedback=feedback,
                created_at=datetime.now().isoformat(),
            )

            # 保存到 Redis
            if self.short_term:
                key = f"booklist_history:{user_id}"
                await self.short_term.lpush(
                    key,
                    json.dumps(
                        {
                            "session_id": session_id,
                            "requirement": requirement,
                            "book_count": len(booklist.books),
                            "categories": list(booklist.category_distribution.keys()),
                            "total_price": booklist.total_price,
                            "quality_score": booklist.quality_score,
                            "feedback": feedback,
                            "created_at": history.created_at,
                        }
                    ),
                )

                # 只保留最近的 N 条
                await self.short_term.ltrim(key, 0, self.max_history_booklists - 1)
                await self.short_term.expire(key, 30 * 24 * 3600)  # 30天过期

            # 保存到数据库（长期存储）
            if self.long_term:
                await self._save_to_database(history)

            # 更新用户画像
            await self._update_preferences_from_booklist(user_id, booklist, feedback)

        except Exception as e:
            logger.error(f"Error saving booklist: {e}")

    async def learn_from_feedback(
        self, user_id: str, booklist: BookListResult, feedback: Dict[str, Any]
    ):
        """
        从用户反馈中学习并更新用户画像

        Args:
            user_id: 用户ID
            booklist: 书单
            feedback: 反馈信息，包含 liked/disliked 等
        """
        try:
            preferences = await self._get_user_preferences(user_id)
            if not preferences:
                preferences = UserPreference(
                    user_id=user_id,
                    preferred_categories=[],
                    avoided_categories=[],
                    preferred_authors=[],
                    avoided_authors=[],
                )

            # 更新偏好
            if feedback.get("liked"):
                # 增加喜欢的分类权重
                for category in booklist.category_distribution.keys():
                    if category not in preferences.preferred_categories:
                        preferences.preferred_categories.append(category)

                # 增加喜欢的作者
                for book in booklist.books:
                    if book.author not in preferences.preferred_authors:
                        preferences.preferred_authors.append(book.author)

                # 更新平均预算
                if preferences.average_budget:
                    preferences.average_budget = (
                        preferences.average_budget * 0.7 + booklist.total_price * 0.3
                    )
                else:
                    preferences.average_budget = booklist.total_price

            if feedback.get("disliked"):
                # 记录不喜欢的分类
                for category in booklist.category_distribution.keys():
                    if category not in preferences.avoided_categories:
                        preferences.avoided_categories.append(category)

                # 记录不喜欢的作者
                for book in booklist.books:
                    if book.author not in preferences.avoided_authors:
                        preferences.avoided_authors.append(book.author)

            # 更新时间戳
            preferences.updated_at = datetime.now().isoformat()

            # 保存更新后的偏好
            await self._save_user_preferences(user_id, preferences)

            logger.info(f"Updated preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Error learning from feedback: {e}")

    async def enhance_requirement(
        self, user_id: str, requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用用户画像增强需求

        Args:
            user_id: 用户ID
            requirement: 当前需求

        Returns:
            Dict: 增强后的需求
        """
        context = await self.get_user_context(user_id)
        preferences = context.get("preferences", {})

        if not preferences:
            return requirement

        enhanced = requirement.copy()

        # 1. 补充缺失的分类偏好
        if not enhanced.get("categories") and preferences.get("preferred_categories"):
            enhanced["categories"] = [
                {
                    "name": cat,
                    "percentage": 100 // len(preferences["preferred_categories"]),
                }
                for cat in preferences["preferred_categories"][:3]
            ]

        # 2. 避免不喜欢的分类
        if preferences.get("avoided_categories"):
            if "excluded_categories" not in enhanced.get("constraints", {}):
                enhanced.setdefault("constraints", {})["excluded_categories"] = []
            enhanced["constraints"]["excluded_categories"].extend(
                preferences["avoided_categories"]
            )

        # 3. 推荐偏好的作者
        if preferences.get("preferred_authors"):
            enhanced.setdefault("preferred_authors", [])
            enhanced["preferred_authors"].extend(preferences["preferred_authors"][:5])

        # 4. 估算预算（如果用户没有指定）
        if not enhanced.get("constraints", {}).get("budget"):
            avg_budget = preferences.get("average_budget")
            if avg_budget:
                enhanced.setdefault("constraints", {})["budget"] = avg_budget * 1.2

        return enhanced

    async def _get_recent_dialogues(self, user_id: str) -> List[Dict[str, Any]]:
        """获取最近对话"""
        key = f"dialogue:{user_id}"
        dialogues = await self.short_term.lrange(key, 0, self.max_recent_dialogues - 1)
        return [json.loads(d) for d in dialogues]

    async def _get_user_preferences(self, user_id: str) -> Optional[UserPreference]:
        """获取用户偏好"""
        if not self.short_term:
            return None

        try:
            key = f"preferences:{user_id}"
            data = await self.short_term.get(key)
            if data:
                return UserPreference(**json.loads(data))
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")

        return None

    async def _save_user_preferences(self, user_id: str, preferences: UserPreference):
        """保存用户偏好"""
        if not self.short_term:
            return

        try:
            key = f"preferences:{user_id}"
            await self.short_term.setex(
                key, 30 * 24 * 3600, json.dumps(asdict(preferences))  # 30天过期
            )
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")

    async def _get_history_booklists(self, user_id: str) -> List[Dict[str, Any]]:
        """获取历史书单"""
        if not self.short_term:
            return []

        try:
            key = f"booklist_history:{user_id}"
            history = await self.short_term.lrange(
                key, 0, self.max_history_booklists - 1
            )
            return [json.loads(h) for h in history]
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    async def _save_to_database(self, history: BookListHistory):
        """保存到数据库（长期存储）"""
        # 这里可以实现数据库持久化逻辑
        # 例如保存到 PostgreSQL 的用户历史表

    async def _update_preferences_from_booklist(
        self, user_id: str, booklist: BookListResult, feedback: Optional[Dict[str, Any]]
    ):
        """根据书单更新用户偏好"""
        if not feedback:
            return

        await self.learn_from_feedback(user_id, booklist, feedback)

    def _calculate_statistics(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算用户书单统计信息"""
        if not history:
            return {}

        total_booklists = len(history)
        total_books = sum(h.get("book_count", 0) for h in history)
        avg_price = (
            sum(h.get("total_price", 0) for h in history) / total_booklists
            if total_booklists > 0
            else 0
        )

        # 统计分类偏好
        category_counts = {}
        for h in history:
            for cat in h.get("categories", []):
                category_counts[cat] = category_counts.get(cat, 0) + 1

        top_categories = sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_booklists": total_booklists,
            "total_books": total_books,
            "average_books_per_list": total_books / total_booklists
            if total_booklists > 0
            else 0,
            "average_price": round(avg_price, 2),
            "top_categories": top_categories,
        }

    async def clear_user_memory(self, user_id: str):
        """
        清除用户记忆

        Args:
            user_id: 用户ID
        """
        if not self.short_term:
            return

        try:
            # 清除所有相关键
            keys = [
                f"dialogue:{user_id}",
                f"preferences:{user_id}",
                f"booklist_history:{user_id}",
            ]

            for key in keys:
                await self.short_term.delete(key)

            logger.info(f"Cleared memory for user {user_id}")

        except Exception as e:
            logger.error(f"Error clearing memory: {e}")


# 便捷函数
async def get_memory_context(user_id: str, memory: BookListMemory) -> Dict[str, Any]:
    """
    便捷函数：获取用户记忆上下文
    """
    return await memory.get_user_context(user_id)


async def save_interaction(
    user_id: str,
    session_id: str,
    user_input: str,
    response: Dict[str, Any],
    memory: BookListMemory,
):
    """
    便捷函数：保存交互记录
    """
    await memory.save_dialogue(user_id, session_id, user_input, response)
