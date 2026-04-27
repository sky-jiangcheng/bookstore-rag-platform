import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class FilterService:
    """屏蔽词服务类"""

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
