"""
书单推荐 - 核心路由

包含三个主要步骤：
1. 需求解析 - parse_requirements
2. 需求细化 - refine_requirements  
3. 生成书单 - generate_book_list
"""

import logging
import time
import uuid

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.api.v1.book_list.schemas import (GenerateBookListRequest,
                                          GenerateBookListResponse,
                                          ParsedRequirements,
                                          ParseRequirementsRequest,
                                          ParseRequirementsResponse,
                                          RefineRequirementsRequest,
                                          RefineRequirementsResponse)
from app.api.v1.book_list.services import BookListGenerator, RequirementParser
from app.api.v1.shared.dependencies import (get_llm_service,
                                            get_vector_db_service,
                                            get_vector_service,
                                            handle_service_error)
from app.core.exceptions import (BookRecommendationError, LLMServiceError,
                                 ValidationError, VectorServiceError)
from app.models import BookListSession, CustomBookList, SessionFeedback
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter(prefix="/api/v1/book-list", tags=["book-list"])
logger = logging.getLogger(__name__)


# ==================== 步骤1：需求解析 ====================


@router.post(
    "/parse",
    response_model=ParseRequirementsResponse,
    summary="解析用户需求",
    description="使用 LLM 解析用户模糊输入，提取目标受众、认知水平、分类比例等",
)
async def parse_requirements(
    request: ParseRequirementsRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    llm_service=Depends(get_llm_service),
):
    """
    步骤1：解析用户需求

    功能：
    - 使用 LLM 解析用户模糊输入
    - 提取目标受众、认知水平、分类比例
    - 生成 requestId 用于后续交互
    - 可选使用用户历史反馈优化解析

    示例请求：
    ```json
    {
      "user_input": "大学生书单，战争20%历史10%经济15%"
    }
    ```
    """
    start_time = time.time()

    try:
        logger.info(
            "开始解析用户需求",
            user_id=current_user.id,
            user_input=request.user_input[:50],
        )

        # 查找用户历史反馈（可选）
        user_history = []
        if request.use_history:
            recent_sessions = (
                db.query(BookListSession)
                .filter(
                    BookListSession.user_id == current_user.id,
                    BookListSession.status.in_(["completed", "confirmed"]),
                )
                .order_by(BookListSession.created_at.desc())
                .limit(5)
                .all()
            )

            user_history = [
                feedback.to_dict() if hasattr(feedback, "to_dict") else feedback
                for session in recent_sessions
                for feedback in (session.user_feedbacks or [])
            ]

        # 使用 RequirementParser 解析
        parser = RequirementParser(llm_service)
        parsed_reqs, confidence_score, suggestions = parser.parse_user_input(
            user_input=request.user_input,
            user_history=user_history if user_history else None,
        )

        # 生成 requestId
        request_id = str(uuid.uuid4())

        # 创建会话记录
        session = BookListSession(
            request_id=request_id,
            user_id=current_user.id,
            original_input=request.user_input,
            refined_inputs=[],
            parsed_requirements=parsed_reqs.model_dump(),
            parsing_history=[parsed_reqs.model_dump()],
            status="waiting_confirmation",
            user_feedbacks=[],
            confirmation_count=0,
            refinement_count=0,
            parsing_time_ms=int((time.time() - start_time) * 1000),
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(
            "需求解析完成",
            request_id=request_id,
            session_id=session.id,
            confidence_score=confidence_score,
            parse_time_ms=int((time.time() - start_time) * 1000),
        )

        return ParseRequirementsResponse(
            request_id=request_id,
            session_id=session.id,
            original_input=request.user_input,
            parsed_requirements=parsed_reqs,
            confidence_score=confidence_score,
            suggestions=suggestions,
            needs_confirmation=confidence_score < 0.9,
            message="需求解析完成，请确认是否符合您的要求" if confidence_score < 0.9 else "需求解析完成，置信度较高",
        )

    except LLMServiceError as e:
        logger.error(f"LLM 服务错误: {str(e)}")
        handle_service_error(e, "需求解析")
    except Exception as e:
        logger.error(f"需求解析系统错误: {str(e)}", exc_info=True)
        handle_service_error(e, "需求解析")


# ==================== 步骤2：需求细化 ====================


@router.post(
    "/refine",
    response_model=RefineRequirementsResponse,
    summary="细化用户需求",
    description="基于原始请求，通过文本或手动调整来优化需求",
)
async def refine_requirements(
    request: RefineRequirementsRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    llm_service=Depends(get_llm_service),
):
    """
    步骤2：细化需求

    功能：
    - 基于同一 requestId 优化需求
    - 支持文本描述和手动调整两种方式
    - 记录细化历史

    示例请求1（文本细化）：
    ```json
    {
      "request_id": "uuid-here",
      "refinement_input": "增加科幻10%，减少历史到5%"
    }
    ```

    示例请求2（手动调整）：
    ```json
    {
      "request_id": "uuid-here",
      "refinement_input": "手动调整分类比例",
      "manual_adjustments": {
        "categories": [
          {"category": "战争", "percentage": 25},
          {"category": "历史", "percentage": 5},
          {"category": "科幻", "percentage": 10}
        ]
      }
    }
    ```
    """
    start_time = time.time()

    try:
        logger.info(
            "开始细化需求",
            user_id=current_user.id,
            request_id=request.request_id,
        )

        # 查找会话
        session = (
            db.query(BookListSession)
            .filter(
                BookListSession.request_id == request.request_id,
                BookListSession.user_id == current_user.id,
            )
            .first()
        )

        if not session:
            raise ValidationError(f"未找到请求 ID: {request.request_id}")

        if session.status == "completed":
            raise ValidationError("该会话已完成，无法再次细化")

        # 获取当前需求
        before_reqs = ParsedRequirements(**session.parsed_requirements)

        # 处理细化（优先使用手动调整）
        if request.manual_adjustments:
            # 手动调整模式
            after_reqs_dict = before_reqs.model_dump()
            after_reqs_dict.update(request.manual_adjustments)
            after_reqs = ParsedRequirements(**after_reqs_dict)
            changes_summary = ["用户手动调整了需求参数"]

        else:
            # LLM 文本细化模式
            parser = RequirementParser(llm_service)
            after_reqs, changes_summary = parser.refine_requirements(
                before_reqs=before_reqs, refinement_input=request.refinement_input
            )

        # 更新会话
        session.status = "refining"
        session.refinement_count += 1
        session.refined_inputs = session.refined_inputs or []
        session.refined_inputs.append(request.refinement_input)
        session.parsed_requirements = after_reqs.model_dump()
        session.parsing_history = session.parsing_history or []
        session.parsing_history.append(after_reqs.model_dump())

        # 记录反馈
        feedback = SessionFeedback(
            session_id=session.id,
            user_id=current_user.id,
            feedback_type="refinement",
            feedback_content=request.refinement_input,
            feedback_data=request.manual_adjustments,
            before_requirements=before_reqs.model_dump(),
            after_requirements=after_reqs.model_dump(),
        )

        db.add(feedback)
        db.commit()
        db.refresh(session)

        logger.info(
            "需求细化完成",
            request_id=request.request_id,
            refinement_count=session.refinement_count,
            refine_time_ms=int((time.time() - start_time) * 1000),
        )

        return RefineRequirementsResponse(
            request_id=request.request_id,
            session_id=session.id,
            before_requirements=before_reqs,
            after_requirements=after_reqs,
            changes_summary=changes_summary,
            needs_confirmation=True,
            message=f"需求已更新（第{session.refinement_count}次细化），请确认",
        )

    except (ValidationError, LLMServiceError) as e:
        logger.error(f"需求细化失败: {str(e)}")
        handle_service_error(e, "需求细化")
    except Exception as e:
        logger.error(f"需求细化系统错误: {str(e)}", exc_info=True)
        handle_service_error(e, "需求细化")


# ==================== 步骤3：生成书单 ====================


@router.post(
    "/generate",
    response_model=GenerateBookListResponse,
    summary="生成书单",
    description="根据需求生成推荐书单（支持交互式 API 和前端页面直接调用）",
)
async def generate_book_list(
    request: GenerateBookListRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    vector_service=Depends(get_vector_service),
    vector_db=Depends(get_vector_db_service),
):
    """
    步骤3：生成书单（统一接口）

    支持两种使用方式：
    1. 基于 requestId（交互式 API 流程）
    2. 直接传递 requirements（前端页面直接使用）

    这确保了前端页面和 API 的推荐逻辑完全一致！

    示例请求1（基于 requestId）：
    ```json
    {
      "request_id": "uuid-here",
      "limit": 20
    }
    ```

    示例请求2（直接使用，前端页面）：
    ```json
    {
      "requirements": {
        "cognitive_level": "大学生",
        "categories": [
          {"category": "战争", "percentage": 20, "count": 4}
        ],
        "exclude_textbooks": true
      },
      "limit": 20,
      "save_to_history": false
    }
    ```
    """
    start_time = time.time()

    try:
        logger.info(
            "开始生成书单",
            user_id=current_user.id,
            request_id=request.request_id,
            has_direct_requirements=request.requirements is not None,
        )

        session = None

        # 确定需求来源
        if request.request_id:
            # 方式1：基于 requestId
            session = (
                db.query(BookListSession)
                .filter(
                    BookListSession.request_id == request.request_id,
                    BookListSession.user_id == current_user.id,
                )
                .first()
            )

            if not session:
                raise ValidationError(f"未找到请求 ID: {request.request_id}")

            parsed_reqs = ParsedRequirements(**session.parsed_requirements)
            session.status = "generating"
            session.confirmed_at = time.time()
            session.confirmation_count += 1

        elif request.requirements:
            # 方式2：直接使用 requirements
            parsed_reqs = request.requirements

        else:
            raise ValidationError("必须提供 request_id 或 requirements")

        # 调用书单生成器
        generator = BookListGenerator(
            vector_service=vector_service, vector_db=vector_db, db=db
        )

        recommendations, category_distribution = generator.generate(
            parsed_reqs=parsed_reqs, limit=request.limit
        )

        generation_time = int((time.time() - start_time) * 1000)

        # 保存书单（可选）
        book_list_id = None
        if request.save_to_history:
            book_list = CustomBookList(
                user_id=current_user.id,
                request_text=session.original_input if session else "直接生成",
                parsed_requirements=parsed_reqs.model_dump(),
                book_list=[r.model_dump() for r in recommendations],
                status="completed",
                processing_time=generation_time,
                completed_at=time.time(),
            )

            db.add(book_list)
            db.commit()
            db.refresh(book_list)
            book_list_id = book_list.id

            # 更新会话（如果有）
            if session:
                session.book_list_id = book_list_id
                session.status = "completed"
                session.generation_time_ms = generation_time
                session.total_time_ms = int(
                    (time.time() - session.created_at.timestamp()) * 1000
                )
                session.completed_at = time.time()

        if session:
            db.commit()

        logger.info(
            "书单生成完成",
            request_id=request.request_id,
            total_count=len(recommendations),
            generation_time_ms=generation_time,
        )

        return GenerateBookListResponse(
            request_id=request.request_id,
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

    except (ValidationError, VectorServiceError, BookRecommendationError) as e:
        logger.error(f"书单生成失败: {str(e)}")
        handle_service_error(e, "书单生成")
    except Exception as e:
        logger.error(f"书单生成系统错误: {str(e)}", exc_info=True)
        handle_service_error(e, "书单生成")
