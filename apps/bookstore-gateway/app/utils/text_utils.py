"""文本处理工具模块

提供通用的文本处理和清洗功能

Author: System
Date: 2026-02-01
"""
import re
from typing import List


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    从文本中提取关键词
    
    Args:
        text: 输入文本
        max_keywords: 最大关键词数量
        
    Returns:
        关键词列表
    """
    # 提取中英文关键词
    keywords = re.findall(r"[\u4e00-\u9fa5a-zA-Z]+", text)
    return keywords[:max_keywords]


def contains_keyword(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """
    检查文本是否包含任一关键词
    
    Args:
        text: 待检查文本
        keywords: 关键词列表
        case_sensitive: 是否区分大小写
        
    Returns:
        是否包含关键词
    """
    if not keywords:
        return False
    
    search_text = text if case_sensitive else text.lower()
    
    for keyword in keywords:
        check_keyword = keyword if case_sensitive else keyword.lower()
        if check_keyword in search_text:
            return True
    
    return False


def detect_categories(text: str, category_keywords: dict) -> List[str]:
    """
    根据关键词检测文本分类
    
    Args:
        text: 输入文本
        category_keywords: 分类关键词映射 {分类名: [关键词列表]}
        
    Returns:
        检测到的分类列表
    """
    categories = []
    text_lower = text.lower()
    
    for category, keys in category_keywords.items():
        if any(key.lower() in text_lower for key in keys):
            categories.append(category)
    
    return categories


def detect_constraints(text: str, constraint_keywords: dict) -> List[str]:
    """
    根据关键词检测约束条件
    
    Args:
        text: 输入文本
        constraint_keywords: 约束关键词映射 {约束名: [关键词列表]}
        
    Returns:
        检测到的约束列表
    """
    constraints = []
    text_lower = text.lower()
    
    for constraint, keys in constraint_keywords.items():
        if any(key.lower() in text_lower for key in keys):
            constraints.append(constraint)
    
    return constraints


# 预定义的分类关键词映射
DEFAULT_CATEGORY_KEYWORDS = {
    "计算机": ["编程", "计算机", "软件", "算法", "人工智能", "python", "java", "c++"],
    "文学": ["小说", "文学", "散文", "诗歌", "名著"],
    "历史": ["历史", "古代", "近代", "现代", "世界史", "中国史"],
    "哲学": ["哲学", "思想", "逻辑", "伦理"],
    "科学": ["科学", "物理", "化学", "生物", "数学"],
    "艺术": ["艺术", "音乐", "绘画", "设计", "摄影"],
    "经济": ["经济", "金融", "投资", "理财", "商业"],
    "教育": ["教育", "学习", "考试", "教材", "辅导"],
}

# 预定义的约束关键词映射
DEFAULT_CONSTRAINT_KEYWORDS = {
    "new": ["最新", "新版", "2024", "2025"],
    "classic": ["经典", "名著", "畅销"],
    "professional": ["专业", "权威", "学术"],
    "beginner": ["入门", "基础", "新手"],
    "advanced": ["高级", "进阶", "深入"],
}
