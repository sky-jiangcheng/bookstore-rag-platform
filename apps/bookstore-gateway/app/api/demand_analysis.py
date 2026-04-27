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
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.core.service_registry import get_service
from app.core.exceptions import (LLMServiceError, ValidationError)
from app.core.logging_config import get_logger
from app.models import BookListSession, DemandAnalysisSession, FilterKeyword, PromptTemplate
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
    """限制条件（硬约束）"""
    proportion_error_range: float = Field(
        default=5.0,
        ge=0,
        le=20,
        description="比例误差范围（%）- 各分类书籍数量与目标比例的最大允许偏差"
    )
    total_book_count: int = Field(
        default=20,
        ge=5,
        le=100,
        description="书单中的图书总数 - 必须严格遵守的数量限制"
    )
    budget: Optional[float] = Field(None, ge=0, description="预算上限（元）")
    exclude_textbooks: bool = Field(False, description="是否排除教材类书籍")
    language_preference: Optional[str] = Field(
        None,
        description="语言偏好：cn（中文）/ en（英文）/ mixed（混合）"
    )
    publish_year_range: Optional[str] = Field(
        None,
        description="出版年份范围，如：2020-2024"
    )
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


def validate_constraints(constraints: Constraints) -> tuple[bool, str]:
    """
    验证硬约束条件的有效性

    Args:
        constraints: 约束条件对象

    Returns:
        (是否有效, 错误信息)
    """
    # 验证书籍分类的总数是否匹配
    # 这个验证需要在生成书单时进行，这里只验证约束本身

    # 验证比例误差范围
    if constraints.proportion_error_range < 0 or constraints.proportion_error_range > 20:
        return False, "比例误差范围必须在 0-20% 之间"

    # 验证书单总数
    if constraints.total_book_count < 5 or constraints.total_book_count > 100:
        return False, "书单总数必须在 5-100 本之间"

    # 验证预算
    if constraints.budget is not None and constraints.budget < 0:
        return False, "预算不能为负数"

    # 验证语言偏好
    valid_languages = ["cn", "en", "mixed", None]
    if constraints.language_preference not in valid_languages:
        return False, f"语言偏好必须是以下之一：{valid_languages}"

    return True, ""


def get_gemini_service():
    """获取Gemini服务"""
    llm_service = get_service("llm_service")
    if not llm_service:
        raise LLMServiceError("LLM服务未初始化")
    return llm_service


def generate_dialogue_prompt(user_message: str, context: Dict[str, Any], dialogue_history: List[Dict[str, str]]) -> str:
    """
    生成优化的对话提示

    优化策略：
    1. 根据已有信息智能生成澄清问题
    2. 避免重复提问
    3. 提供具体的选择项而非开放式问题
    4. 引导用户明确约束条件
    """
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in dialogue_history[-5:]])

    current_state_text = ""
    if context:
        current_state_text = f"\n\n当前已收集信息：\n{json.dumps(context, ensure_ascii=False, indent=2)}"

    # 分析缺失信息
    missing_info = _analyze_missing_info(context)

    prompt = f"""你是一个专业的图书推荐需求分析助手。

任务目标：通过对话收集完整的书单推荐需求

对话历史（最近5条）：
{history_text}

用户最新消息：{user_message}{current_state_text}

当前缺失信息分析：
{missing_info}

工作流程：
1. 分析用户最新消息，提取新的需求信息
2. 更新需求状态，标记已收集和缺失的信息
3. 根据缺失信息生成针对性的澄清问题

澄清问题设计原则：
- 提供具体选项而非泛泛提问（例：职业选择？程序员/教师/大学生/产品经理/设计师）
- 一次聚焦1-2个关键信息，避免过多问题
- 基于已有信息推断，减少用户负担
- 当约束条件不明确时，主动确认硬约束参数

请以JSON格式返回：
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
            "budget": null,
            "exclude_textbooks": false,
            "language_preference": null,
            "other_constraints": []
        }},
        "completed": false
    }}
}}
"""
    return prompt


def _analyze_missing_info(context: Dict[str, Any]) -> str:
    """分析缺失的信息"""
    missing = []

    user_profile = context.get("user_profile", {})
    if not user_profile.get("occupation"):
        missing.append("❌ 目标受众职业")
    else:
        missing.append(f"✓ 目标受众职业：{user_profile.get('occupation')}")

    if not user_profile.get("age_group"):
        missing.append("❌ 年龄段")
    else:
        missing.append(f"✓ 年龄段：{user_profile.get('age_group')}")

    book_categories = context.get("book_categories", [])
    if not book_categories:
        missing.append("❌ 书籍分类及比例")
    else:
        missing.append(f"✓ 书籍分类：{len(book_categories)} 个分类")

    constraints = context.get("constraints", {})
    if not constraints.get("total_book_count"):
        missing.append("❌ 书单总数")
    else:
        missing.append(f"✓ 书单总数：{constraints.get('total_book_count')} 本")

    if constraints.get("budget"):
        missing.append(f"✓ 预算：{constraints.get('budget')} 元")
    else:
        missing.append("⚠ 预算（可选）")

    return "\n".join(missing) if missing else "✓ 信息完整"


def generate_prompt_template(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成优化的提示词模板

    优化策略：
    1. 根据目标受众定制推荐逻辑
    2. 明确硬约束要求
    3. 提供具体的选书标准
    4. 生成可执行的生成指令
    """
    user_profile = context.get("user_profile", {})
    filter_category = context.get("filter_category", {})
    book_categories = context.get("book_categories", [])
    constraints = context.get("constraints", {})

    # 构建目标受众描述
    occupation = user_profile.get('occupation', '未识别')
    age_group = user_profile.get('age_group', '未识别')
    domain_scope = user_profile.get('domain_scope', '')
    reading_preferences = user_profile.get('reading_preferences', [])

    # 构建目标受众引导语
    target_audience_guide = _build_target_audience_guide(occupation, age_group, reading_preferences)

    # 构建硬约束指令
    constraint_instructions = _build_constraint_instructions(constraints, book_categories)

    # 构建选书标准
    selection_criteria = _build_selection_criteria(occupation, domain_scope, reading_preferences)

    # 构建提示词模板
    prompt_template = {
        "template_id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "user_profile": user_profile,
        "filter_category": filter_category,
        "book_categories": book_categories,
        "constraints": constraints,
        "prompt": f"""# 图书推荐任务

## 目标受众
{target_audience_guide}

## 选书标准
{selection_criteria}

## 书单结构
{chr(10).join([f'- {cat["category"]}: {cat["percentage"]}% ({cat["count"]}本)' for cat in book_categories])}

## 硬约束（必须严格遵守）
{constraint_instructions}

## 输出要求
请生成一份符合以上要求的书单，确保：
1. 每个分类的书籍数量严格符合硬约束要求
2. 比例误差控制在 {constraints.get('proportion_error_range', 5.0)}% 以内
3. 总数精确为 {constraints.get('total_book_count', 20)} 本
4. 每本书包含：书名、作者、出版社、ISBN、推荐理由

开始生成书单：
"""
    }

    return prompt_template


def _build_target_audience_guide(occupation: str, age_group: str, preferences: list) -> str:
    """构建目标受众引导语"""
    guide_parts = []

    if occupation != '未识别':
        guide_parts.append(f"- 目标职业：{occupation}")

        # 根据职业添加定制化建议
        occupation_guidance = {
            "程序员": "关注技术深度、实战性和前沿技术",
            "大学生": "注重知识体系完整性、易理解性和性价比",
            "教师": "重视教学价值、知识准确性和系统性",
            "产品经理": "强调用户体验、商业思维和实战案例",
            "设计师": "注重视觉呈现、创意灵感和实战技巧",
        }
        if occupation in occupation_guidance:
            guide_parts.append(f"- 选书策略：{occupation_guidance[occupation]}")

    if age_group != '未识别':
        guide_parts.append(f"- 年龄段：{age_group}")

    if preferences:
        guide_parts.append(f"- 阅读偏好：{', '.join(preferences)}")

    return "\n".join(guide_parts) if guide_parts else "目标受众：通用读者"


def _build_constraint_instructions(constraints: dict, book_categories: list) -> str:
    """构建硬约束指令"""
    instructions = []

    # 基本约束
    instructions.append(f"1. 总数约束：必须正好 {constraints.get('total_book_count', 20)} 本书，不可多也不可少")

    # 比例约束
    error_range = constraints.get('proportion_error_range', 5.0)
    instructions.append(f"2. 比例约束：各分类数量与目标比例的偏差不超过 ±{error_range}%")

    # 其他约束
    if constraints.get('budget'):
        instructions.append(f"3. 预算约束：总定价不超过 {constraints['budget']} 元")

    if constraints.get('exclude_textbooks'):
        instructions.append("4. 排除教材：不要包含教材类书籍")

    if constraints.get('language_preference'):
        language_map = {"cn": "中文", "en": "英文", "mixed": "中英混合"}
        instructions.append(f"5. 语言偏好：{language_map.get(constraints['language_preference'], constraints['language_preference'])}")

    if constraints.get('publish_year_range'):
        instructions.append(f"6. 出版年份：{constraints['publish_year_range']}")

    if constraints.get('other_constraints'):
        for i, other in enumerate(constraints['other_constraints'], start=len(instructions) + 1):
            instructions.append(f"{i}. 其他：{other}")

    return "\n".join(instructions)


def _build_selection_criteria(occupation: str, domain_scope: str, preferences: list) -> str:
    """构建选书标准"""
    criteria = []

    # 基础标准
    criteria.extend([
        "1. 权威性：选择知名作者、经典作品或口碑良好的新书",
        "2. 时效性：优先选择近年出版或内容更新的版本",
        "3. 适用性：与目标受众的实际需求和阅读水平匹配",
    ])

    # 根据职业定制
    if occupation == "程序员":
        criteria.append("4. 技术性：重视代码质量、实战项目和最佳实践")
    elif occupation == "大学生":
        criteria.extend([
            "4. 学习性：注重知识体系的循序渐进",
            "5. 性价比：考虑学生预算，优先选择性价比高的书籍"
        ])

    # 根据偏好定制
    if preferences:
        criteria.append(f"5. 偏好匹配：重点考虑 {', '.join(preferences[:3])} 相关主题")

    return "\n".join(criteria)


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
            session = db.query(DemandAnalysisSession).filter(
                DemandAnalysisSession.session_id == request.session_id,
                DemandAnalysisSession.user_id == current_user.id
            ).first()
            
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
                created_at=datetime.now()
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        # 更新对话历史
        session.dialogue_history.append({
            "role": "user",
            "content": request.message,
            "timestamp": time.time()
        })
        
        # 生成对话提示
        prompt = generate_dialogue_prompt(
            request.message,
            session.current_context or {},
            session.dialogue_history
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
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                llm_result = json.loads(json_match.group())
            else:
                raise LLMServiceError("LLM返回格式错误")
        
        # 更新会话
        session.dialogue_history.append({
            "role": "assistant",
            "content": llm_result.get("content", ""),
            "timestamp": time.time()
        })
        
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
            "message": "对话处理成功"
        }
        
        logger.info(
            "需求解析对话完成",
            session_id=session.session_id,
            completed=completed,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        return response_data
        
    except (LLMServiceError, ValidationError) as e:
        logger.error(f"对话处理失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"对话处理系统错误: {e}",
            exc_info=True
        )
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
        session = db.query(DemandAnalysisSession).filter(
            DemandAnalysisSession.session_id == request.session_id,
            DemandAnalysisSession.user_id == current_user.id
        ).first()
        
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
            status="active"
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
            user_id=current_user.id
        )
        
        return GeneratePromptTemplateResponse(
            template_id=prompt_template["template_id"],
            prompt_template=prompt_template,
            message="提示词模板生成成功"
        )
        
    except (ValidationError) as e:
        logger.error(f"生成提示词模板失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"生成提示词模板系统错误: {e}",
            exc_info=True
        )
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
    session = db.query(DemandAnalysisSession).filter(
        DemandAnalysisSession.session_id == session_id,
        DemandAnalysisSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "session_id": session.session_id,
        "status": session.status,
        "dialogue_history": session.dialogue_history,
        "current_context": session.current_context,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
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
        PromptTemplate.user_id == current_user.id,
        PromptTemplate.status == "active"
    )
    
    total = query.count()
    templates = query.order_by(
        PromptTemplate.created_at.desc()
    ).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": [
            {
                "template_id": t.template_id,
                "template_content": t.template_content,
                "created_at": t.created_at.isoformat(),
                "status": t.status
            }
            for t in templates
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }
