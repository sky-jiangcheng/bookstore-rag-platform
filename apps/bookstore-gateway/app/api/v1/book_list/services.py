"""
书单生成 - 核心业务逻辑

这个模块包含所有核心的书单生成逻辑，确保前端和 API 使用完全相同的推荐算法
"""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.api.v1.book_list.schemas import (
    BookRecommendation,
    CategoryRequirement,
    ParsedRequirements,
)
from app.core.exceptions import (
    BookRecommendationError,
    LLMServiceError,
    ValidationError,
    VectorServiceError,
)
from app.models import BookInfo, BookListSession, CustomBookList, FilterKeyword
from app.models.auth import User

logger = logging.getLogger(__name__)


class RequirementParser:
    """需求解析器 - 封装 LLM 调用和解析逻辑"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    def parse_user_input(
        self,
        user_input: str,
        user_history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[ParsedRequirements, float, List[str]]:
        """
        使用 LLM 解析用户输入
        
        Args:
            user_input: 用户原始输入
            user_history: 用户历史反馈（可选）
            
        Returns:
            (ParsedRequirements, confidence_score, suggestions)
        """
        try:
            # 构建历史上下文
            history_context = ""
            if user_history:
                history_context = f"\n\n用户历史偏好：\n{json.dumps(user_history, ensure_ascii=False, indent=2)}"
            
            # 构建提示
            prompt = f"""请分析以下图书推荐需求，提取关键信息：

需求：{user_input}{history_context}

请以JSON格式返回以下信息（严格按照格式，确保是有效的JSON）：
{{
    "target_audience": "目标受众（如：大学生、中学生、职场人士，如未提及则为null）",
    "cognitive_level": "认知水平（如：大学生、中学生、初学者、专业人士，如未提及则为null）",
    "categories": [
        {{"category": "分类名称", "percentage": 百分比数字（不带%符号）}}
    ],
    "keywords": ["关键词1", "关键词2"],
    "constraints": ["约束条件1", "约束条件2"],
    "exclude_textbooks": true,
    "confidence_score": 0.85,
    "suggestions": ["建议1", "建议2"]
}}

注意事项：
1. categories中的percentage只需要数字，不要%符号
2. 如果没有明确提到某项，设为null或空数组
3. confidence_score表示解析置信度（0-1）
4. suggestions是给用户的优化建议
5. 只返回JSON，不要其他文字
"""
            
            # 调用 LLM
            response = self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500,
            )
            
            # 解析响应
            result = self._parse_llm_response(response)
            
            # 提取置信度和建议
            confidence_score = result.pop("confidence_score", 0.8)
            suggestions = result.pop("suggestions", [])
            
            # 构建 ParsedRequirements
            parsed_reqs = self._build_parsed_requirements(result)
            
            return parsed_reqs, confidence_score, suggestions
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM 返回格式错误: {str(e)}")
            raise LLMServiceError(f"LLM 返回格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"需求解析失败: {str(e)}")
            raise LLMServiceError(f"需求解析失败: {str(e)}")
    
    def refine_requirements(
        self,
        before_reqs: ParsedRequirements,
        refinement_input: str
    ) -> Tuple[ParsedRequirements, List[str]]:
        """
        使用 LLM 细化需求
        
        Args:
            before_reqs: 原始需求
            refinement_input: 细化输入文本
            
        Returns:
            (refined_requirements, changes_summary)
        """
        try:
            prompt = f"""用户想要细化书单推荐需求，请根据用户的细化输入，更新需求参数。

当前需求：
{json.dumps(before_reqs.model_dump(), ensure_ascii=False, indent=2)}

用户细化输入：{refinement_input}

请返回更新后的完整需求（JSON格式）：
{{
    "target_audience": "...",
    "cognitive_level": "...",
    "categories": [...],
    "keywords": [...],
    "constraints": [...],
    "exclude_textbooks": true,
    "changes_summary": ["变更1", "变更2"]
}}

注意：
1. 保留未变更的字段
2. 只更新用户明确提到的部分
3. changes_summary列出主要变更
4. 确保返回有效的JSON
"""
            
            response = self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500,
            )
            
            result = self._parse_llm_response(response)
            changes_summary = result.pop("changes_summary", ["需求已更新"])
            
            # 构建更新后的需求
            refined_reqs = self._build_parsed_requirements(result, before_reqs)
            
            return refined_reqs, changes_summary
            
        except Exception as e:
            logger.error(f"需求细化失败: {str(e)}")
            raise LLMServiceError(f"需求细化失败: {str(e)}")
    
    @staticmethod
    def _parse_llm_response(response: str) -> Dict[str, Any]:
        """解析 LLM JSON 响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise LLMServiceError("无法解析 LLM 返回")
    
    @staticmethod
    def _build_parsed_requirements(
        result: Dict[str, Any],
        before_reqs: Optional[ParsedRequirements] = None
    ) -> ParsedRequirements:
        """
        从 LLM 响应构建 ParsedRequirements
        
        Args:
            result: LLM 返回的字典
            before_reqs: 原始需求（用于细化时的默认值）
        """
        limit = 20
        category_requirements = []
        
        categories = result.get("categories")
        
        # 如果没有 categories 字段，检查是否有 updated_context.book_categories 字段（来自 MockLLM）
        if not categories and result.get("updated_context"):
            categories = result["updated_context"].get("book_categories")
        
        if categories and isinstance(categories, list):
            processed_categories = []
            
            for cat in categories:
                if isinstance(cat, str):
                    # 字符串格式
                    processed_categories.append({
                        "category": cat,
                        "percentage": 100 / len(categories)
                    })
                elif isinstance(cat, dict) and "category" in cat and "percentage" in cat:
                    # 字典格式
                    processed_categories.append(cat)
            
            # 计算总百分比并调整
            if processed_categories:
                total_percentage = sum(cat["percentage"] for cat in processed_categories)
                
                for cat in processed_categories:
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
        
        # 构建最终需求
        if before_reqs:
            # 细化场景 - 使用原值作为默认
            return ParsedRequirements(
                target_audience=result.get("target_audience") or before_reqs.target_audience,
                cognitive_level=result.get("cognitive_level") or before_reqs.cognitive_level,
                categories=category_requirements or before_reqs.categories,
                keywords=result.get("keywords") or before_reqs.keywords,
                constraints=result.get("constraints") or before_reqs.constraints,
                exclude_textbooks=result.get("exclude_textbooks", before_reqs.exclude_textbooks),
                min_cognitive_level=result.get("cognitive_level") or before_reqs.min_cognitive_level,
            )
        else:
            # 新建场景
            return ParsedRequirements(
                target_audience=result.get("target_audience"),
                cognitive_level=result.get("cognitive_level"),
                categories=category_requirements,
                keywords=result.get("keywords", []),
                constraints=result.get("constraints", []),
                exclude_textbooks=result.get("exclude_textbooks", True),
                min_cognitive_level=result.get("cognitive_level"),
            )


class BookListGenerator:
    """书单生成器 - 核心推荐算法"""
    
    # 认知水平映射
    COGNITIVE_LEVEL_MAP = {
        "儿童": 1,
        "小学生": 2,
        "中学生": 3,
        "高中生": 4,
        "大学生": 5,
        "研究生": 6,
        "专业人士": 7,
        "通用": 3,
    }
    
    # 教材关键词
    TEXTBOOK_KEYWORDS = ["教材", "教程", "习题集", "教学", "课本"]
    
    def __init__(
        self,
        vector_service,
        vector_db,
        db: Session
    ):
        self.vector_service = vector_service
        self.vector_db = vector_db
        self.db = db
    
    def generate(
        self,
        parsed_reqs: ParsedRequirements,
        limit: int = 20
    ) -> Tuple[List[BookRecommendation], Dict[str, int]]:
        """
        生成书单
        
        Args:
            parsed_reqs: 解析后的需求
            limit: 推荐数量
            
        Returns:
            (recommendations, category_distribution)
        """
        try:
            # 获取屏蔽词
            blocked_keywords = self._get_blocked_keywords()
            
            all_recommendations = []
            category_distribution = {}
            
            # 按分类搜索
            if parsed_reqs.categories:
                all_recommendations, category_distribution = self._generate_by_categories(
                    parsed_reqs=parsed_reqs,
                    limit=limit,
                    blocked_keywords=blocked_keywords
                )
            else:
                # 无具体分类，使用关键词搜索
                all_recommendations, category_distribution = self._generate_by_keywords(
                    parsed_reqs=parsed_reqs,
                    limit=limit,
                    blocked_keywords=blocked_keywords
                )
            
            # 限制数量
            all_recommendations = all_recommendations[:limit]
            
            if not all_recommendations:
                raise BookRecommendationError("未找到符合条件的书籍，请调整需求")
            
            return all_recommendations, category_distribution
            
        except Exception as e:
            logger.error(f"书单生成失败: {str(e)}")
            raise
    
    def _get_blocked_keywords(self) -> List[str]:
        """获取屏蔽词"""
        try:
            return [
                kw.keyword
                for kw in self.db.query(FilterKeyword).filter(FilterKeyword.is_active == 1).all()
            ]
        except Exception as e:
            logger.warning(f"获取屏蔽词失败: {str(e)}")
            return []
    
    def _generate_by_categories(
        self,
        parsed_reqs: ParsedRequirements,
        limit: int,
        blocked_keywords: List[str]
    ) -> Tuple[List[BookRecommendation], Dict[str, int]]:
        """按分类生成书单"""
        all_recommendations = []
        category_distribution = {}
        
        required_level_value = self.COGNITIVE_LEVEL_MAP.get(
            parsed_reqs.cognitive_level or "通用", 3
        )
        
        for cat_req in parsed_reqs.categories:
            category_books = self._search_category(
                category=cat_req.category,
                count=cat_req.count,
                parsed_reqs=parsed_reqs,
                required_level_value=required_level_value,
                blocked_keywords=blocked_keywords
            )
            
            all_recommendations.extend(category_books)
            category_distribution[cat_req.category] = len(category_books)
        
        return all_recommendations, category_distribution
    
    def _generate_by_keywords(
        self,
        parsed_reqs: ParsedRequirements,
        limit: int,
        blocked_keywords: List[str]
    ) -> Tuple[List[BookRecommendation], Dict[str, int]]:
        """按关键词生成书单"""
        required_level_value = self.COGNITIVE_LEVEL_MAP.get(
            parsed_reqs.cognitive_level or "通用", 3
        )
        
        search_query = " ".join(parsed_reqs.keywords or [parsed_reqs.target_audience or "推荐"])
        
        all_recommendations = self._search_query(
            query=search_query,
            limit=limit,
            parsed_reqs=parsed_reqs,
            required_level_value=required_level_value,
            blocked_keywords=blocked_keywords
        )
        
        category_distribution = {"通用": len(all_recommendations)}
        
        return all_recommendations, category_distribution
    
    def _search_category(
        self,
        category: str,
        count: int,
        parsed_reqs: ParsedRequirements,
        required_level_value: int,
        blocked_keywords: List[str]
    ) -> List[BookRecommendation]:
        """搜索特定分类的书籍"""
        try:
            # 获取查询向量
            query_vector = self.vector_service.get_vector(category)
            
            # 向量搜索
            search_results = self.vector_db.search_similar_books(
                query_vector=query_vector.tolist(),
                top_k=count * 3,
                score_threshold=0.3,
            )
        except Exception as e:
            logger.warning(f"向量搜索失败（{category}），使用数据库查询: {str(e)}")
            # 降级到数据库查询
            search_results = self._fallback_search(category, count * 3)
        
        category_books = []
        
        for result in search_results:
            if len(category_books) >= count:
                break
            
            book = self.db.query(BookInfo).filter(BookInfo.id == result["book_id"]).first()
            if not book or book.stock <= 0:
                continue
            
            # 应用过滤规则
            if self._should_filter_out(
                book=book,
                parsed_reqs=parsed_reqs,
                required_level_value=required_level_value,
                blocked_keywords=blocked_keywords
            ):
                continue
            
            # 生成推荐
            remark = self._generate_remark(book, required_level_value)
            
            category_books.append(
                BookRecommendation(
                    book_id=book.id,
                    barcode=book.barcode,
                    title=book.title,
                    author=book.author,
                    publisher=book.publisher,
                    price=float(book.price) if book.price else None,
                    stock=book.stock,
                    category=category,
                    cognitive_level=book.cognitive_level,
                    difficulty_level=book.difficulty_level,
                    match_score=result.get("score", 0.8),
                    remark=remark,
                )
            )
        
        return category_books
    
    def _search_query(
        self,
        query: str,
        limit: int,
        parsed_reqs: ParsedRequirements,
        required_level_value: int,
        blocked_keywords: List[str]
    ) -> List[BookRecommendation]:
        """按查询搜索书籍"""
        try:
            query_vector = self.vector_service.get_vector(query)
            search_results = self.vector_db.search_similar_books(
                query_vector=query_vector.tolist(),
                top_k=limit * 3,
                score_threshold=0.3,
            )
        except Exception as e:
            logger.warning(f"向量搜索失败，使用数据库查询: {str(e)}")
            search_results = self._fallback_search(query, limit * 3)
        
        all_recommendations = []
        
        for result in search_results:
            if len(all_recommendations) >= limit:
                break
            
            book = self.db.query(BookInfo).filter(BookInfo.id == result["book_id"]).first()
            if not book or book.stock <= 0:
                continue
            
            if self._should_filter_out(
                book=book,
                parsed_reqs=parsed_reqs,
                required_level_value=required_level_value,
                blocked_keywords=blocked_keywords
            ):
                continue
            
            remark = self._generate_remark(book, required_level_value)
            
            all_recommendations.append(
                BookRecommendation(
                    book_id=book.id,
                    barcode=book.barcode,
                    title=book.title,
                    author=book.author,
                    publisher=book.publisher,
                    price=float(book.price) if book.price else None,
                    stock=book.stock,
                    category="通用",
                    cognitive_level=book.cognitive_level,
                    difficulty_level=book.difficulty_level,
                    match_score=result.get("score", 0.8),
                    remark=remark,
                )
            )
        
        return all_recommendations
    
    def _fallback_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """数据库搜索（降级方案）"""
        db_books = self.db.query(BookInfo).limit(limit).all()
        
        results = []
        for book in db_books:
            results.append({
                "book_id": book.id,
                "title": book.title,
                "author": book.author or "",
                "score": 0.5,
                "categories": [],
                "cognitive_level": book.cognitive_level,
                "difficulty_level": book.difficulty_level,
                "target_audience": [],
                "tags": [],
                "semantic_description": book.semantic_description or "",
            })
        
        return results
    
    def _should_filter_out(
        self,
        book: BookInfo,
        parsed_reqs: ParsedRequirements,
        required_level_value: int,
        blocked_keywords: List[str]
    ) -> bool:
        """判断是否应该过滤掉该书"""
        # 过滤教材
        if parsed_reqs.exclude_textbooks:
            book_text = f"{book.title} {book.series or ''}"
            if any(kw in book_text for kw in self.TEXTBOOK_KEYWORDS):
                return True
        
        # 过滤屏蔽词
        book_text = f"{book.title} {book.author or ''} {book.publisher or ''}"
        if any(kw in book_text for kw in blocked_keywords):
            return True
        
        # 认知水平检查
        book_level_value = self.COGNITIVE_LEVEL_MAP.get(book.cognitive_level or "通用", 3)
        if book_level_value < required_level_value:
            return True
        
        return False
    
    @staticmethod
    def _generate_remark(book: BookInfo, required_level_value: int) -> Optional[str]:
        """生成书籍备注"""
        book_level_value = BookListGenerator.COGNITIVE_LEVEL_MAP.get(
            book.cognitive_level or "通用", 3
        )
        
        if book_level_value > required_level_value + 1:
            return f"认知水平较高（{book.cognitive_level}），可能有一定挑战"
        
        return None


def validate_prompt(prompt: str) -> Dict[str, Any]:
    """
    验证提示词是否包含所有必要的维度
    """
    dimensions = {
        "user_profile": False,
        "filter_category": False,
        "book_categories": False,
        "constraints": False
    }
    
    errors = []
    
    # 检查用户画像
    user_profile_keywords = ["职业", "年龄段", "领域范围", "阅读偏好"]
    if any(keyword in prompt for keyword in user_profile_keywords):
        dimensions["user_profile"] = True
    else:
        errors.append("缺少用户画像信息（职业、年龄段、领域范围等）")
    
    # 检查屏蔽词类别
    if "屏蔽词" in prompt or "屏蔽类别" in prompt:
        dimensions["filter_category"] = True
    else:
        errors.append("缺少屏蔽词类别信息")
    
    # 检查书单分类
    category_keywords = ["分类", "军事", "历史", "传记", "教辅", "比例"]
    if any(keyword in prompt for keyword in category_keywords):
        dimensions["book_categories"] = True
    else:
        errors.append("缺少书单分类及比例信息")
    
    # 检查限制条件
    constraint_keywords = ["限制", "误差范围", "总数", "数量"]
    if any(keyword in prompt for keyword in constraint_keywords):
        dimensions["constraints"] = True
    else:
        errors.append("缺少限制条件信息")
    
    valid = len(errors) == 0
    
    return {
        "valid": valid,
        "errors": errors,
        "dimensions": dimensions
    }
