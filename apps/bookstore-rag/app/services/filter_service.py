from typing import Dict, List, Optional, Tuple

import logging

from app.config.filter_keywords import (
    FILTER_CATEGORIES,
    ALL_FILTER_KEYWORDS,
)

logger = logging.getLogger(__name__)


class FilterService:
    """屏蔽词服务类（保留原有功能）"""

    def parse_filter_document(self, content: str) -> Dict[str, List[str]]:
        """
        解析屏蔽词文档

        文档格式：
        - 类别行：包含类别名称，后面可能跟空格
        - 屏蔽词行：包含多个屏蔽词，用空格分隔
        - 不同类别之间用空行分隔

        Args:
            content: 文档内容

        Returns:
            解析结果，格式为 {"类别": ["屏蔽词1", "屏蔽词2", ...]}
        """
        try:
            lines = content.strip().split("\n")
            result = {}
            current_category = None

            for line in lines:
                line = line.strip()
                if not line:
                    current_category = None  # 空行表示类别结束
                    continue

                # 检查是否包含空格，如果不包含空格，或者包含空格但看起来像类别名称
                # 简单规则：如果一行包含多个空格分隔的词，且不是以空格开头，则认为是类别
                # 否则认为是屏蔽词
                words = line.split()
                if len(words) == 1 or (len(words) > 1 and not line.startswith(" ")):
                    # 这是一个类别
                    current_category = line.strip()
                    result[current_category] = []
                    logger.info(f"Found category: {current_category}")
                elif current_category:
                    # 这是屏蔽词行
                    keywords = line.split()
                    for keyword in keywords:
                        keyword = keyword.strip()
                        if keyword:
                            result[current_category].append(keyword)
                            logger.info(
                                f"Added keyword '{keyword}' to category '{current_category}'"
                            )

            logger.info(
                f"Parsed {len(result)} categories with total {sum(len(words) for words in result.values())} keywords"
            )
            return result

        except Exception as e:
            logger.error(f"Error parsing filter document: {str(e)}")
            return {}

    def validate_filter_data(self, data: Dict[str, List[str]]) -> Tuple[bool, str]:
        """
        验证过滤数据

        Args:
            data: 过滤数据

        Returns:
            (是否有效, 错误信息)
        """
        if not data:
            return False, "数据为空"

        for category, keywords in data.items():
            if not category or not isinstance(category, str):
                return False, "类别名称无效"

            if not isinstance(keywords, list):
                return False, f"类别 '{category}' 的关键词必须是列表"

            for keyword in keywords:
                if not keyword or not isinstance(keyword, str):
                    return False, f"类别 '{category}' 中包含无效关键词"

        return True, ""


class BookFilterService:
    """图书筛选服务 - 用于书目分类和过滤"""

    def __init__(self):
        self.categories = FILTER_CATEGORIES
        self.all_keywords = set(ALL_FILTER_KEYWORDS)

    def analyze_book(
        self,
        title: str,
        author: Optional[str] = None,
        publisher: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        分析图书并返回筛选标签和匹配关键词

        Args:
            title: 图书标题
            author: 作者
            publisher: 出版社
            summary: 图书简介

        Returns:
            dict: {
                "filter_tags": List[str],  # 匹配的筛选分类代码
                "matched_keywords": List[str],  # 匹配到的关键词
                "categories": Dict[str, List[str]]  # 各分类匹配的关键词
            }
        """
        result = {
            "filter_tags": [],
            "matched_keywords": [],
            "categories": {},
        }

        # 合并所有文本进行分析
        text_to_analyze = " ".join(
            filter(
                None,
                [
                    title or "",
                    author or "",
                    publisher or "",
                    summary or "",
                ],
            )
        )

        # 对每个分类进行匹配
        for category_code, category in self.categories.items():
            matched_in_category = []

            for keyword in category.keywords:
                if keyword in text_to_analyze:
                    matched_in_category.append(keyword)

            if matched_in_category:
                result["filter_tags"].append(category_code)
                result["matched_keywords"].extend(matched_in_category)
                result["categories"][category_code] = matched_in_category

        # 去重
        result["matched_keywords"] = list(set(result["matched_keywords"]))

        return result

    def should_filter_book(
        self,
        book_tags: List[str],
        excluded_categories: List[str],
    ) -> bool:
        """
        判断图书是否应该被过滤

        Args:
            book_tags: 图书的筛选标签
            excluded_categories: 用户排除的分类列表

        Returns:
            bool: True表示应该过滤，False表示不过滤
        """
        if not excluded_categories:
            return False

        # 检查是否有任何排除的标签在图书标签中
        return bool(set(book_tags) & set(excluded_categories))

    def get_filter_summary(self, books_data: List[Dict]) -> Dict[str, int]:
        """
        获取筛选统计信息

        Args:
            books_data: 图书数据列表，每个元素包含 filter_tags 字段

        Returns:
            dict: 各分类的图书数量统计
        """
        summary = {code: 0 for code in self.categories.keys()}
        summary["total_filtered"] = 0
        summary["total_analyzed"] = len(books_data)

        for book in books_data:
            tags = book.get("filter_tags", [])
            if tags:
                summary["total_filtered"] += 1
                for tag in tags:
                    if tag in summary:
                        summary[tag] += 1

        return summary

    def batch_analyze_books(
        self,
        books: List[Dict[str, any]],
    ) -> List[Dict[str, any]]:
        """
        批量分析图书并添加筛选标签

        Args:
            books: 图书列表，每个元素包含 title, author, publisher, summary 等字段

        Returns:
            list: 添加了 filter_tags 和 matched_keywords 字段的图书列表
        """
        results = []

        for book in books:
            analysis = self.analyze_book(
                title=book.get("title", ""),
                author=book.get("author"),
                publisher=book.get("publisher"),
                summary=book.get("summary"),
            )

            # 将分析结果添加到图书数据
            book["filter_tags"] = analysis["filter_tags"]
            book["matched_keywords"] = analysis["matched_keywords"]
            book["filter_categories"] = analysis["categories"]

            results.append(book)

        logger.info(f"批量分析完成，共分析 {len(results)} 本图书")
        return results

    def get_category_info(self, category_code: str) -> Optional[Dict]:
        """
        获取筛选分类信息

        Args:
            category_code: 分类代码

        Returns:
            dict: 分类信息，如果不存在返回 None
        """
        category = self.categories.get(category_code)
        if category:
            return {
                "code": category.code,
                "name": category.name,
                "description": category.description,
                "keywords": category.keywords,
                "keyword_count": len(category.keywords),
            }
        return None

    def get_all_categories(self) -> List[Dict]:
        """
        获取所有筛选分类信息

        Returns:
            list: 所有分类信息列表
        """
        return [
            {
                "code": code,
                "name": category.name,
                "description": category.description,
                "keyword_count": len(category.keywords),
            }
            for code, category in self.categories.items()
        ]

    def validate_book_for_filters(
        self,
        book_data: Dict,
        active_filters: List[str],
    ) -> Dict[str, any]:
        """
        验证图书是否符合筛选条件

        Args:
            book_data: 图书数据
            active_filters: 激活的筛选条件（要排除的分类）

        Returns:
            dict: {
                "is_filtered": bool,  # 是否被过滤
                "matched_filters": List[str],  # 匹配到的筛选分类
                "reason": str,  # 过滤原因
            }
        """
        book_tags = book_data.get("filter_tags", [])
        matched_filters = list(set(book_tags) & set(active_filters))

        if matched_filters:
            filter_names = [
                self.categories[code].name for code in matched_filters
            ]
            return {
                "is_filtered": True,
                "matched_filters": matched_filters,
                "reason": f"图书属于以下排除分类: {', '.join(filter_names)}",
            }

        return {
            "is_filtered": False,
            "matched_filters": [],
            "reason": "",
        }


# 创建全局实例
book_filter_service = BookFilterService()
