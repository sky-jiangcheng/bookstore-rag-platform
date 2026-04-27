"""
Service Orchestrator - 统一的服务编排器

这是一个关键的新增模块，负责：
1. 统一编排所有服务调用
2. 提供统一的错误处理和降级
3. 实现事务性操作
4. 性能监控和日志记录

将所有复杂的服务协调逻辑集中在这里，便于维护和测试。
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.api.v1.book_list.schemas import (GenerateBookListResponse,
                                          ParsedRequirements,
                                          ParseRequirementsResponse,
                                          RefineRequirementsResponse)
from app.api.v1.book_list.services import (BookListGenerator,
                                           RequirementParser)
from app.core.exceptions import (BookRecommendationError, LLMServiceError,
                                 ValidationError, VectorServiceError)
from app.models import BookListSession, CustomBookList

logger = logging.getLogger(__name__)


class ServiceOrchestrator:
    """
    统一的服务编排器

    负责协调所有业务服务的调用，提供：
    - 统一的错误处理
    - 事务性保证
    - 性能监控
    - 自动降级和重试
    """

    def __init__(
        self, llm_service, vector_service, vector_db, cache_service, db: Session
    ):
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.vector_db = vector_db
        self.cache_service = cache_service
        self.db = db

        # 初始化内部的解析器和生成器
        self.requirement_parser = RequirementParser(llm_service)
        self.book_generator = BookListGenerator(
            vector_service=vector_service, vector_db=vector_db, db=db
        )

    async def parse_requirements(
        self, user_input: str, user_id: int, use_history: bool = True
    ) -> Tuple[ParseRequirementsResponse, int]:
        """
        解析用户需求（第一步）

        Args:
            user_input: 用户原始输入
            user_id: 用户 ID
            use_history: 是否使用历史反馈

        Returns:
            (response, session_id)
        """
        start_time = time.time()

        try:
            logger.info(
                "开始解析用户需求: user_id=%s, user_input=%s",
                user_id,
                user_input[:50],
            )

            # 获取用户历史反馈
            user_history = []
            if use_history:
                user_history = self._get_user_history(user_id)

            # 使用解析器解析需求
            (
                parsed_reqs,
                confidence_score,
                suggestions,
            ) = self.requirement_parser.parse_user_input(
                user_input=user_input,
                user_history=user_history if user_history else None,
            )

            # 创建会话记录
            import uuid

            request_id = str(uuid.uuid4())
            session = self._create_session(
                request_id=request_id,
                user_id=user_id,
                original_input=user_input,
                parsed_requirements=parsed_reqs,
                parsing_time_ms=int((time.time() - start_time) * 1000),
            )

            logger.info(
                "需求解析完成: request_id=%s, session_id=%s, confidence_score=%s",
                request_id,
                session.id,
                confidence_score,
            )

            # 构建响应
            response = ParseRequirementsResponse(
                request_id=request_id,
                session_id=session.id,
                original_input=user_input,
                parsed_requirements=parsed_reqs,
                confidence_score=confidence_score,
                suggestions=suggestions,
                needs_confirmation=confidence_score < 0.9,
                message="需求解析完成，请确认是否符合您的要求"
                if confidence_score < 0.9
                else "需求解析完成，置信度较高",
            )

            return response, session.id

        except LLMServiceError as e:
            logger.error(f"LLM 服务错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"需求解析系统错误: {str(e)}", exc_info=True)
            raise

    async def refine_requirements(
        self,
        request_id: str,
        user_id: int,
        refinement_input: str,
        manual_adjustments: Optional[Dict[str, Any]] = None,
    ) -> Tuple[RefineRequirementsResponse, int]:
        """
        细化用户需求（第二步）

        Args:
            request_id: 原始请求 ID
            user_id: 用户 ID
            refinement_input: 细化输入文本
            manual_adjustments: 手动调整（优先级更高）

        Returns:
            (response, session_id)
        """
        time.time()

        try:
            logger.info(
                "开始细化需求: user_id=%s, request_id=%s",
                user_id,
                request_id,
            )

            # 查找会话
            session = self._get_session(request_id, user_id)

            # 获取当前需求
            before_reqs = ParsedRequirements(**session.parsed_requirements)

            # 处理细化
            if manual_adjustments:
                after_reqs, changes_summary = self._process_manual_refinement(
                    before_reqs, manual_adjustments
                )
            else:
                (
                    after_reqs,
                    changes_summary,
                ) = self.requirement_parser.refine_requirements(
                    before_reqs=before_reqs, refinement_input=refinement_input
                )

            # 更新会话
            self._update_session_refinement(
                session=session,
                after_reqs=after_reqs,
                refinement_input=refinement_input,
                before_reqs=before_reqs,
                manual_adjustments=manual_adjustments,
            )

            logger.info(
                "需求细化完成: request_id=%s, refinement_count=%s",
                request_id,
                session.refinement_count,
            )

            # 构建响应
            response = RefineRequirementsResponse(
                request_id=request_id,
                session_id=session.id,
                before_requirements=before_reqs,
                after_requirements=after_reqs,
                changes_summary=changes_summary,
                needs_confirmation=True,
                message=f"需求已更新（第{session.refinement_count}次细化），请确认",
            )

            return response, session.id

        except ValidationError as e:
            logger.error(f"需求细化验证错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"需求细化系统错误: {str(e)}", exc_info=True)
            raise

    async def generate_book_list(
        self,
        request_id: Optional[str],
        user_id: int,
        requirements: Optional[ParsedRequirements],
        limit: int = 20,
        save_to_history: bool = True,
    ) -> GenerateBookListResponse:
        """
        生成书单（第三步）

        支持两种方式：
        1. 基于 request_id（交互式流程）
        2. 直接传递 requirements（前端页面）

        Args:
            request_id: 原始请求 ID（可选）
            user_id: 用户 ID
            requirements: 直接提供的需求（可选）
            limit: 推荐数量
            save_to_history: 是否保存到历史

        Returns:
            GenerateBookListResponse
        """
        start_time = time.time()

        try:
            logger.info(
                "开始生成书单: user_id=%s, request_id=%s, has_requirements=%s",
                user_id,
                request_id,
                requirements is not None,
            )

            session = None

            # 确定需求来源
            if request_id:
                session = self._get_session(request_id, user_id)
                parsed_reqs = ParsedRequirements(**session.parsed_requirements)
                self._update_session_status(session, "generating")
            elif requirements:
                parsed_reqs = requirements
            else:
                raise ValidationError("必须提供 request_id 或 requirements")

            # 生成书单
            recommendations, category_distribution = self.book_generator.generate(
                parsed_reqs=parsed_reqs, limit=limit
            )

            generation_time = int((time.time() - start_time) * 1000)

            # 保存书单
            book_list_id = None
            if save_to_history:
                book_list_id = self._save_book_list(
                    user_id=user_id,
                    request_text=session.original_input if session else "直接生成",
                    parsed_requirements=parsed_reqs,
                    recommendations=recommendations,
                    generation_time=generation_time,
                )

                # 更新会话
                if session:
                    self._finalize_session(
                        session=session,
                        book_list_id=book_list_id,
                        generation_time=generation_time,
                    )

            logger.info(
                "书单生成完成: request_id=%s, total_count=%s, generation_time_ms=%s",
                request_id,
                len(recommendations),
                generation_time,
            )

            # 构建响应
            response = GenerateBookListResponse(
                request_id=request_id,
                session_id=session.id if session else None,
                book_list_id=book_list_id,
                requirements=parsed_reqs,
                recommendations=recommendations,
                total_count=len(recommendations),
                category_distribution=category_distribution,
                generation_time_ms=generation_time,
                success=True,
                message=f"成功生成 {len(recommendations)} 本书的推荐书单",
            )

            # 缓存结果
            if book_list_id:
                self._cache_result(book_list_id, response)

            return response

        except (ValidationError, VectorServiceError, BookRecommendationError) as e:
            logger.error(f"书单生成失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"书单生成系统错误: {str(e)}", exc_info=True)
            raise

    # ==================== 内部辅助方法 ====================

    def _get_user_history(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户历史反馈"""
        try:
            from app.models import BookListSession

            recent_sessions = (
                self.db.query(BookListSession)
                .filter(
                    BookListSession.user_id == user_id,
                    BookListSession.status.in_(["completed", "confirmed"]),
                )
                .order_by(BookListSession.created_at.desc())
                .limit(5)
                .all()
            )

            user_history = []
            for session in recent_sessions:
                if session.user_feedbacks:
                    user_history.extend(session.user_feedbacks)

            return user_history
        except Exception as e:
            logger.warning(f"获取用户历史反馈失败: {str(e)}")
            return []

    def _create_session(
        self,
        request_id: str,
        user_id: int,
        original_input: str,
        parsed_requirements: ParsedRequirements,
        parsing_time_ms: int,
    ) -> BookListSession:
        """创建会话记录"""
        from app.models import BookListSession

        session = BookListSession(
            request_id=request_id,
            user_id=user_id,
            original_input=original_input,
            refined_inputs=[],
            parsed_requirements=parsed_requirements.model_dump(),
            parsing_history=[parsed_requirements.model_dump()],
            status="waiting_confirmation",
            user_feedbacks=[],
            confirmation_count=0,
            refinement_count=0,
            parsing_time_ms=parsing_time_ms,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def _get_session(self, request_id: str, user_id: int) -> BookListSession:
        """获取会话"""
        from app.models import BookListSession

        session = (
            self.db.query(BookListSession)
            .filter(
                BookListSession.request_id == request_id,
                BookListSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            raise ValidationError(f"未找到请求 ID: {request_id}")

        if session.status == "completed":
            raise ValidationError("该会话已完成，无法再次细化")

        return session

    def _process_manual_refinement(
        self, before_reqs: ParsedRequirements, manual_adjustments: Dict[str, Any]
    ) -> Tuple[ParsedRequirements, List[str]]:
        """处理手动调整"""
        from app.api.v1.book_list.schemas import CategoryRequirement

        after_reqs_dict = before_reqs.model_dump()
        after_reqs_dict.update(manual_adjustments)

        # 重新计算分类数量
        if "categories" in manual_adjustments:
            limit = 20
            category_requirements = []
            total_percentage = sum(
                cat["percentage"] for cat in manual_adjustments["categories"]
            )

            for cat in manual_adjustments["categories"]:
                adjusted_percentage = (
                    cat["percentage"] * 100 / total_percentage
                    if total_percentage > 100
                    else cat["percentage"]
                )
                count = max(1, int(limit * adjusted_percentage / 100))
                category_requirements.append(
                    CategoryRequirement(
                        category=cat["category"],
                        percentage=adjusted_percentage,
                        count=count,
                    )
                )

            after_reqs_dict["categories"] = [
                c.model_dump() for c in category_requirements
            ]

        after_reqs = ParsedRequirements(**after_reqs_dict)
        changes_summary = ["用户手动调整了需求参数"]

        return after_reqs, changes_summary

    def _update_session_refinement(
        self,
        session: BookListSession,
        after_reqs: ParsedRequirements,
        refinement_input: str,
        before_reqs: ParsedRequirements,
        manual_adjustments: Optional[Dict[str, Any]],
    ) -> None:
        """更新会话的细化信息"""
        from app.models import SessionFeedback

        session.status = "refining"
        session.refinement_count += 1
        session.refined_inputs = session.refined_inputs or []
        session.refined_inputs.append(refinement_input)
        session.parsed_requirements = after_reqs.model_dump()
        session.parsing_history = session.parsing_history or []
        session.parsing_history.append(after_reqs.model_dump())

        # 记录反馈
        feedback = SessionFeedback(
            session_id=session.id,
            user_id=session.user_id,
            feedback_type="refinement",
            feedback_content=refinement_input,
            feedback_data=manual_adjustments,
            before_requirements=before_reqs.model_dump(),
            after_requirements=after_reqs.model_dump(),
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(session)

    def _update_session_status(self, session: BookListSession, status: str) -> None:
        """更新会话状态"""
        session.status = status
        session.confirmed_at = datetime.now()
        session.confirmation_count += 1
        self.db.commit()

    def _save_book_list(
        self,
        user_id: int,
        request_text: str,
        parsed_requirements: ParsedRequirements,
        recommendations: List[Any],
        generation_time: int,
    ) -> int:
        """保存书单"""
        book_list = CustomBookList(
            user_id=user_id,
            request_text=request_text,
            parsed_requirements=parsed_requirements.model_dump(),
            book_list=[
                r.model_dump() if hasattr(r, "model_dump") else r
                for r in recommendations
            ],
            status="completed",
            processing_time=generation_time,
            completed_at=datetime.now(),
        )

        self.db.add(book_list)
        self.db.commit()
        self.db.refresh(book_list)

        return book_list.id

    def _finalize_session(
        self, session: BookListSession, book_list_id: int, generation_time: int
    ) -> None:
        """完成会话"""
        session.book_list_id = book_list_id
        session.status = "completed"
        session.generation_time_ms = generation_time
        session.completed_at = datetime.now()
        self.db.commit()

    def _cache_result(
        self, book_list_id: int, response: GenerateBookListResponse
    ) -> None:
        """缓存结果"""
        try:
            if self.cache_service:
                cache_key = f"book_list:{book_list_id}"
                self.cache_service.set(cache_key, response.model_dump(), ttl=3600)
                logger.info(f"书单结果已缓存: {cache_key}")
        except Exception as e:
            logger.warning(f"缓存结果失败: {str(e)}")


class TransactionContext:
    """
    事务上下文管理器

    确保多个数据库操作的原子性
    """

    def __init__(self, db: Session):
        self.db = db
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常，回滚
            self.db.rollback()
            logger.error(f"事务回滚，异常: {exc_type.__name__}: {exc_val}")
            return False

        if not self.committed:
            # 没有异常，提交
            try:
                self.db.commit()
                self.committed = True
            except Exception as e:
                self.db.rollback()
                logger.error(f"事务提交失败: {str(e)}")
                raise

        return True

    def commit(self):
        """手动提交"""
        if not self.committed:
            self.db.commit()
            self.committed = True

    def rollback(self):
        """手动回滚"""
        self.db.rollback()
