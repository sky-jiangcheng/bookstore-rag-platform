"""
智能书单推荐API - AgenticRAG版本
使用新的Agent架构重构，保持与原有API兼容
"""

import time
import uuid
from datetime import datetime
from types import SimpleNamespace
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.book_list_adapter import BookListAgentAdapter
from app.agents.multi_agent import MultiAgentOrchestrator
from app.api.auth_management import get_current_active_user
from app.api.v1.book_list.schemas import (CategoryRequirement,
                                          GenerateBookListRequest,
                                          GenerateBookListResponse,
                                          ParsedRequirements,
                                          ParseRequirementsRequest,
                                          ParseRequirementsResponse,
                                          RefineRequirementsRequest,
                                          RefineRequirementsResponse)
from app.core.logging_config import get_logger
from app.models import BookListSession, CustomBookList
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter()
logger = get_logger(__name__)
EPHEMERAL_BOOKLIST_SESSIONS: dict[str, dict] = {}


class AgenticBookListService:
    """
    基于AgenticRAG的书单服务
    封装所有Agent调用逻辑
    """

    def __init__(self):
        self.orchestrator = MultiAgentOrchestrator()
        self.adapter = BookListAgentAdapter()

    async def parse_requirements(
        self, user_input: str, use_history: bool = False, user_id: Optional[str] = None
    ) -> dict:
        """
        使用Agent解析需求

        使用 RequirementAgent 替代原有的LLM直接调用
        """
        from app.agents.requirement_agent import RequirementAgent

        req_agent = RequirementAgent()
        result = await req_agent.analyze(user_input)

        # 转换为ParsedRequirements格式
        categories = []
        if result.categories:
            total = sum(c.get("percentage", 0) for c in result.categories)
            for cat in result.categories:
                percentage = cat.get("percentage", 0)
                if total > 100:
                    percentage = percentage * 100 / total
                count = max(1, int(20 * percentage / 100))
                categories.append(
                    CategoryRequirement(
                        category=cat.get("name", "通用"),
                        percentage=percentage,
                        count=count,
                    )
                )

        parsed_reqs = ParsedRequirements(
            target_audience=result.target_audience.get("occupation"),
            cognitive_level=result.target_audience.get("reading_level"),
            categories=categories,
            keywords=result.keywords,
            constraints=result.constraints.get("other", []),
            exclude_textbooks=result.constraints.get("exclude_textbooks", True),
            min_cognitive_level=result.target_audience.get("reading_level"),
        )

        return {
            "parsed_requirements": parsed_reqs,
            "confidence": result.confidence,
            "needs_clarification": result.needs_clarification,
            "clarification_questions": result.clarification_questions,
            "suggestions": [],
        }

    async def generate_booklist(
        self,
        parsed_reqs: ParsedRequirements,
        user_context: Optional[dict] = None,
        target_count: Optional[int] = None,
    ) -> dict:
        """
        使用Agent生成书单

        使用 MultiAgentOrchestrator 替代原有逻辑
        """
        # 转换需求格式
        user_input = self.adapter.create_user_input_from_requirements(parsed_reqs)

        # 使用Agent生成
        agent_result = None
        async for msg in self.orchestrator.collaborative_generate(
            user_input=user_input, stream=False, target_count=target_count
        ):
            if msg.get("type") == "complete":
                agent_result = msg
                break

        if not agent_result:
            raise Exception("Agent未能生成书单")

        # 转换结果
        return self.adapter.convert_agent_result_to_response(
            agent_result=agent_result, parsed_reqs=parsed_reqs
        )


def _store_ephemeral_session(
    request_id: str,
    current_user_id: int,
    original_input: str,
    parsed_requirements: dict,
) -> SimpleNamespace:
    """在数据库不可用时保存临时会话。"""
    ephemeral_session = {
        "id": 0,
        "request_id": request_id,
        "user_id": current_user_id,
        "original_input": original_input,
        "parsed_requirements": parsed_requirements,
        "status": "waiting_confirmation",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    EPHEMERAL_BOOKLIST_SESSIONS[request_id] = ephemeral_session
    return SimpleNamespace(**ephemeral_session)


def _load_booklist_session(
    db: Session,
    request_id: str,
    current_user_id: int,
) -> Optional[object]:
    """优先从数据库读取会话，失败时回退到临时会话。"""
    try:
        session = (
            db.query(BookListSession)
            .filter(
                BookListSession.request_id == request_id,
                BookListSession.user_id == current_user_id,
            )
            .first()
        )
        if session:
            return session
    except Exception as exc:
        logger.warning(
            "Database session lookup failed, using ephemeral session: %s", exc
        )

    ephemeral = EPHEMERAL_BOOKLIST_SESSIONS.get(request_id)
    if not ephemeral or ephemeral.get("user_id") != current_user_id:
        return None
    return SimpleNamespace(**ephemeral)


# 创建服务实例
agentic_service = AgenticBookListService()


@router.post("/api/v1/book-list/parse", response_model=ParseRequirementsResponse)
async def parse_requirements_agentic(
    request: ParseRequirementsRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    步骤1：使用Agent解析用户需求

    升级：使用 RequirementAgent 替代直接LLM调用
    """
    start_time = time.time()

    try:
        logger.info(
            "使用Agent解析需求",
            user_id=current_user.id,
            user_input=request.user_input,
        )

        # 使用Agent解析
        result = await agentic_service.parse_requirements(
            user_input=request.user_input,
            use_history=request.use_history,
            user_id=str(current_user.id),
        )

        # 生成requestId
        request_id = str(uuid.uuid4())

        # 创建会话，数据库不可用时自动降级为临时会话
        session = None
        try:
            session = BookListSession(
                request_id=request_id,
                user_id=current_user.id,
                original_input=request.user_input,
                parsed_requirements=result["parsed_requirements"].model_dump(),
                status="waiting_confirmation",
                confirmation_count=0,
                refinement_count=0,
                parsing_time_ms=int((time.time() - start_time) * 1000),
            )

            db.add(session)
            db.commit()
            db.refresh(session)
        except Exception as db_error:
            try:
                db.rollback()
            except Exception:
                pass
            logger.warning(
                "Database unavailable, storing ephemeral session: %s", db_error
            )
            session = _store_ephemeral_session(
                request_id=request_id,
                current_user_id=current_user.id,
                original_input=request.user_input,
                parsed_requirements=result["parsed_requirements"].model_dump(),
            )

        logger.info(
            "Agent需求解析完成",
            request_id=request_id,
            confidence=result["confidence"],
        )

        return ParseRequirementsResponse(
            request_id=request_id,
            session_id=session.id if session else 0,
            original_input=request.user_input,
            parsed_requirements=result["parsed_requirements"],
            confidence_score=result["confidence"],
            suggestions=result["suggestions"],
            needs_confirmation=result["needs_clarification"]
            or result["confidence"] < 0.9,
            message="需求解析完成，请确认是否符合您的要求"
            if result["confidence"] < 0.9
            else "需求解析完成，置信度较高",
        )

    except Exception as e:
        logger.error(f"Agent需求解析失败: {e}", user_input=request.user_input)
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/api/v1/book-list/generate", response_model=GenerateBookListResponse)
async def generate_book_list_agentic(
    request: GenerateBookListRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    步骤3：使用Agent生成书单

    升级：使用 MultiAgentOrchestrator 替代原有逻辑
    - 多路召回（语义+精确+热门）
    - RRF融合排序
    - 迭代质量优化
    """
    start_time = time.time()

    try:
        logger.info(
            "使用Agent生成书单",
            user_id=current_user.id,
            request_id=request.request_id,
        )

        # 确定需求来源
        session = None
        if request.request_id:
            session = _load_booklist_session(db, request.request_id, current_user.id)
            if not session:
                raise HTTPException(
                    status_code=404, detail=f"未找到请求ID: {request.request_id}"
                )

            parsed_reqs = ParsedRequirements(**session.parsed_requirements)
            if hasattr(session, "status"):
                session.status = "generating"
            if hasattr(session, "confirmed_at"):
                session.confirmed_at = datetime.now()
            if hasattr(session, "confirmation_count"):
                session.confirmation_count += 1
        elif request.requirements:
            parsed_reqs = request.requirements
        else:
            raise HTTPException(status_code=400, detail="必须提供request_id或requirements")

        # 获取用户上下文（用于个性化）
        user_context = None
        # TODO: 集成记忆系统
        # memory = BookListMemory()
        # user_context = await memory.get_user_context(str(current_user.id))

        # 使用Agent生成书单
        result = await agentic_service.generate_booklist(
            parsed_reqs=parsed_reqs,
            user_context=user_context,
            target_count=request.limit,
        )

        generation_time = int((time.time() - start_time) * 1000)

        # 保存书单（可选）
        book_list_id = None
        if request.save_to_history:
            try:
                book_list = CustomBookList(
                    user_id=current_user.id,
                    request_text=session.original_input if session else "直接生成",
                    parsed_requirements=parsed_reqs.model_dump(),
                    book_list=[r.model_dump() for r in result["recommendations"]],
                    status="completed",
                    processing_time=generation_time,
                    completed_at=datetime.now(),
                )
                db.add(book_list)
                db.commit()
                db.refresh(book_list)
                book_list_id = book_list.id
            except Exception as db_error:
                try:
                    db.rollback()
                except Exception:
                    pass
                logger.warning(
                    "Failed to persist book list, returning transient result: %s",
                    db_error,
                )
                book_list_id = 0

            # 更新会话
            if session:
                try:
                    if hasattr(session, "book_list_id"):
                        session.book_list_id = book_list_id
                    if hasattr(session, "status"):
                        session.status = "completed"
                    if hasattr(session, "generation_time_ms"):
                        session.generation_time_ms = generation_time
                    if hasattr(session, "completed_at"):
                        session.completed_at = datetime.now()
                    db.commit()
                except Exception as db_error:
                    try:
                        db.rollback()
                    except Exception:
                        pass
                    logger.warning("Failed to update session state: %s", db_error)

        logger.info(
            "Agent书单生成完成",
            request_id=request.request_id,
            total_count=result["total_count"],
            generation_time_ms=generation_time,
            quality_score=result.get("quality_score", 0),
        )

        return GenerateBookListResponse(
            request_id=request.request_id,
            session_id=session.id if session else None,
            book_list_id=book_list_id,
            requirements=parsed_reqs,
            recommendations=result["recommendations"],
            total_count=result["total_count"],
            category_distribution=result["category_distribution"],
            generation_time_ms=generation_time,
            success=True,
            message=f"成功生成{result['total_count']}本书的推荐书单（Agent模式）",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent书单生成失败: {e}", request_id=request.request_id)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


# 保留原有路由（细化需求等）
@router.post("/api/v1/book-list/refine", response_model=RefineRequirementsResponse)
async def refine_requirements_agentic(
    request: RefineRequirementsRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    步骤2：细化需求（保持原有逻辑）
    """
    # TODO: 可以在这里也使用Agent进行需求细化
    # 暂时保持原有实现
    from app.api.v1.book_list.routes import refine_requirements

    return await refine_requirements(request, db, current_user)


# 导出router
__all__ = ["router"]
