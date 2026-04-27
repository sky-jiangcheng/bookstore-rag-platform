"""
需求解析API

功能：
1. 使用对话窗口形式进行多轮对话，理解用户需求
2. 收集用户画像信息（职业、年龄段、领域范围等）
3. 确定屏蔽词类别
4. 定义书单分类及比例
5. 设置限制条件
6. 生成书单推荐提示词模板
7. 生成模板编码（UUID）
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.core.exceptions import LLMServiceError, ValidationError
from app.core.logging_config import get_logger
from app.core.service_registry import get_service
from app.models import (DemandAnalysisSession, PromptTemplate)
from app.models.auth import User
from app.utils.database import get_db

router = APIRouter(prefix="/api/v1/demand-analysis", tags=["需求解析"])
logger = get_logger(__name__)


# ==================== 数据模型 ====================


class UserProfile(BaseModel):
    """用户画像"""

    occupation: Optional[str] = Field(None, description="职业")
    age_group: Optional[str] = Field(None, description="年龄段")
    domain_scope: Optional[str] = Field(None, description="领域范围")
    reading_preferences: List[str] = Field(default_factory=list, description="阅读偏好")


class FilterCategory(BaseModel):
    """屏蔽词类别"""

    category_name: str = Field(..., description="类别名称")
    needs_new_category: bool = Field(default=False, description="是否需要创建新类别")
    new_category_name: Optional[str] = Field(None, description="新类别名称")


class BookCategory(BaseModel):
    """书籍分类"""

    category: str = Field(..., description="分类名称")
    percentage: float = Field(..., ge=0, le=100, description="百分比")
    count: int = Field(..., ge=0, description="需要数量")


class Constraints(BaseModel):
    """限制条件"""

    proportion_error_range: float = Field(
        default=5.0, ge=0, le=20, description="比例误差范围"
    )
    total_book_count: int = Field(default=20, ge=5, le=100, description="书单中的图书总数")
    other_constraints: List[str] = Field(default_factory=list, description="其他限制条件")


class DialogueMessage(BaseModel):
    """对话消息"""

    role: str = Field(..., description="角色：user 或 assistant")
    content: str = Field(..., description="消息内容")
    timestamp: float = Field(default_factory=time.time, description="时间戳")


class DemandAnalysisRequest(BaseModel):
    """需求解析请求"""

    session_id: Optional[str] = Field(None, description="会话ID，首次对话为空")
    message: str = Field(..., description="用户消息")
    context: Optional[Dict[str, Any]] = Field(None, description="对话上下文")


class DemandAnalysisResponse(BaseModel):
    """需求解析响应"""

    session_id: str = Field(..., description="会话ID")
    messages: List[DialogueMessage] = Field(..., description="对话历史")
    current_state: Dict[str, Any] = Field(..., description="当前需求状态")
    completed: bool = Field(default=False, description="是否完成需求解析")
    prompt_template: Optional[Dict[str, Any]] = Field(None, description="生成的提示词模板")
    template_id: Optional[str] = Field(None, description="模板编码")
    message: str = Field(..., description="提示信息")


class GeneratePromptTemplateRequest(BaseModel):
    """生成提示词模板请求"""

    session_id: str = Field(..., description="会话ID")
    user_confirmation: bool = Field(..., description="用户确认")


class GeneratePromptTemplateResponse(BaseModel):
    """生成提示词模板响应"""

    template_id: str = Field(..., description="模板编码")
    prompt_template: Dict[str, Any] = Field(..., description="生成的提示词模板")
    message: str = Field(..., description="提示信息")


# ==================== 核心功能 ====================


def get_gemini_service():
    """获取Gemini服务"""
    llm_service = get_service("llm_service")
    if not llm_service:
        raise LLMServiceError("LLM服务未初始化")
    return llm_service


def generate_dialogue_prompt(
    user_message: str, context: Dict[str, Any], dialogue_history: List[Dict[str, str]]
) -> str:
    """生成对话提示"""
    history_text = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in dialogue_history[-10:]]
    )  # 只保留最近10条消息

    current_state_text = ""
    if context:
        current_state_text = (
            f"\n\n当前需求状态：\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )

    prompt = f"""你是一个图书推荐需求分析助手，负责通过多轮对话了解用户的阅读需求。

对话历史：
{history_text}

用户最新消息：{user_message}{current_state_text}

请分析用户的需求，并：
1. 提取用户画像信息（职业、年龄段、领域范围等）
2. 确定需要使用的屏蔽词类别
3. 了解用户对书单分类及比例的要求
4. 明确限制条件（如比例误差范围、书单总数等）

如果信息不完整，请以友好的方式向用户提问，引导用户提供更多信息。
如果信息已完整，请生成一个结构化的需求分析结果。

请以JSON格式返回以下信息：
{{
    "type": "question" 或 "analysis",
    "content": "你的回复内容",
    "updated_context": {{
        "user_profile": {{
            "occupation": "职业",
            "age_group": "年龄段",
            "domain_scope": "领域范围",
            "reading_preferences": ["偏好1", "偏好2"]
        }},
        "filter_category": {{
            "category_name": "屏蔽词类别",
            "needs_new_category": false,
            "new_category_name": "新类别名称"
        }},
        "book_categories": [
            {{"category": "分类名称", "percentage": 百分比, "count": 数量}}
        ],
        "constraints": {{
            "proportion_error_range": 5.0,
            "total_book_count": 20,
            "other_constraints": ["其他限制条件"]
        }},
        "completed": false
    }}
}}
"""
    return prompt


def generate_prompt_template(context: Dict[str, Any]) -> Dict[str, Any]:
    """生成提示词模板"""
    user_profile = context.get("user_profile", {})
    filter_category = context.get("filter_category", {})
    book_categories = context.get("book_categories", [])
    constraints = context.get("constraints", {})

    # 构建提示词模板
    prompt_template = {
        "template_id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "user_profile": user_profile,
        "filter_category": filter_category,
        "book_categories": book_categories,
        "constraints": constraints,
        "prompt": f"""请根据以下需求生成一份书单：

用户画像：
- 职业：{user_profile.get('occupation', '未知')}
- 年龄段：{user_profile.get('age_group', '未知')}
- 领域范围：{user_profile.get('domain_scope', '未知')}
- 阅读偏好：{', '.join(user_profile.get('reading_preferences', []))}

屏蔽词类别：{filter_category.get('category_name', '默认')}

书单分类及比例：
{chr(10).join([f'- {cat["category"]}: {cat["percentage"]}% ({cat["count"]}本)' for cat in book_categories])}

限制条件：
- 比例误差范围：{constraints.get('proportion_error_range', 5.0)}%
- 书单总数：{constraints.get('total_book_count', 20)}本
- 其他限制：{', '.join(constraints.get('other_constraints', []))}

请生成一份符合以上要求的书单，确保分类比例符合要求，并包含具体的书籍信息。
""",
    }

    return prompt_template


# ==================== API端点 ====================


@router.post("/dialogue", response_model=DemandAnalysisResponse)
async def dialogue_with_user(
    request: DemandAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    对话式需求解析

    通过多轮对话了解用户需求，收集必要信息
    """
    start_time = time.time()

    try:
        logger.info(
            "开始需求解析对话",
            user_id=current_user.id,
            session_id=request.session_id,
            user_message=request.message,
        )

        # 获取LLM服务
        llm_service = get_gemini_service()

        # 查找或创建会话
        if request.session_id:
            session = (
                db.query(DemandAnalysisSession)
                .filter(
                    DemandAnalysisSession.session_id == request.session_id,
                    DemandAnalysisSession.user_id == current_user.id,
                )
                .first()
            )

            if not session:
                raise ValidationError(f"会话不存在: {request.session_id}")
        else:
            # 创建新会话
            session_id = str(uuid.uuid4())
            session = DemandAnalysisSession(
                session_id=session_id,
                user_id=current_user.id,
                dialogue_history=[],
                current_context={},
                status="in_progress",
                created_at=datetime.now(),
            )
            db.add(session)
            db.commit()
            db.refresh(session)

        # 更新对话历史
        session.dialogue_history.append(
            {"role": "user", "content": request.message, "timestamp": time.time()}
        )

        # 生成对话提示
        prompt = generate_dialogue_prompt(
            request.message, session.current_context or {}, session.dialogue_history
        )

        # 调用LLM
        response = llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )

        # 解析LLM响应
        try:
            llm_result = json.loads(response)
        except json.JSONDecodeError:
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                llm_result = json.loads(json_match.group())
            else:
                raise LLMServiceError("LLM返回格式错误")

        # 更新会话
        session.dialogue_history.append(
            {
                "role": "assistant",
                "content": llm_result.get("content", ""),
                "timestamp": time.time(),
            }
        )

        session.current_context = llm_result.get("updated_context", {})
        session.updated_at = datetime.now()

        # 检查是否完成
        completed = session.current_context.get("completed", False)
        if completed:
            session.status = "completed"

        db.commit()
        db.refresh(session)

        # 构建响应
        response_data = {
            "session_id": session.session_id,
            "messages": [DialogueMessage(**msg) for msg in session.dialogue_history],
            "current_state": session.current_context,
            "completed": completed,
            "message": "对话处理成功",
        }

        logger.info(
            "需求解析对话完成",
            session_id=session.session_id,
            completed=completed,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )

        return response_data

    except (LLMServiceError, ValidationError) as e:
        logger.error(f"对话处理失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"对话处理系统错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系统错误: {str(e)}")


@router.post("/generate-template", response_model=GeneratePromptTemplateResponse)
async def generate_prompt_template_api(
    request: GeneratePromptTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    生成提示词模板

    根据用户确认的需求，生成提示词模板并分配唯一标识
    """
    try:
        logger.info(
            "开始生成提示词模板",
            user_id=current_user.id,
            session_id=request.session_id,
            user_confirmation=request.user_confirmation,
        )

        # 查找会话
        session = (
            db.query(DemandAnalysisSession)
            .filter(
                DemandAnalysisSession.session_id == request.session_id,
                DemandAnalysisSession.user_id == current_user.id,
            )
            .first()
        )

        if not session:
            raise ValidationError(f"会话不存在: {request.session_id}")

        if not request.user_confirmation:
            raise ValidationError("用户未确认需求")

        # 生成提示词模板
        prompt_template = generate_prompt_template(session.current_context)

        # 保存模板到数据库
        template = PromptTemplate(
            template_id=prompt_template["template_id"],
            user_id=current_user.id,
            template_content=prompt_template,
            created_at=datetime.now(),
            status="active",
        )
        db.add(template)
        db.commit()

        # 更新会话状态
        session.status = "completed"
        session.updated_at = datetime.now()
        db.commit()

        logger.info(
            "提示词模板生成成功",
            template_id=prompt_template["template_id"],
            user_id=current_user.id,
        )

        return GeneratePromptTemplateResponse(
            template_id=prompt_template["template_id"],
            prompt_template=prompt_template,
            message="提示词模板生成成功",
        )

    except ValidationError as e:
        logger.error(f"生成提示词模板失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"生成提示词模板系统错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"系统错误: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取会话信息
    """
    session = (
        db.query(DemandAnalysisSession)
        .filter(
            DemandAnalysisSession.session_id == session_id,
            DemandAnalysisSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session.session_id,
        "status": session.status,
        "dialogue_history": session.dialogue_history,
        "current_context": session.current_context,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("/templates")
async def get_user_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取用户的提示词模板列表
    """
    query = db.query(PromptTemplate).filter(
        PromptTemplate.user_id == current_user.id, PromptTemplate.status == "active"
    )

    total = query.count()
    templates = (
        query.order_by(PromptTemplate.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": [
            {
                "template_id": t.template_id,
                "template_content": t.template_content,
                "created_at": t.created_at.isoformat(),
                "status": t.status,
            }
            for t in templates
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }
