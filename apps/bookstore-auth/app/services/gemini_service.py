import logging
from typing import Any, Dict, List

from app.utils.config_loader import config_loader

# 尝试导入新版 google.genai，如果失败则设置为None
try:
    import google.genai as genai
except ImportError as e:
    genai = None
    logging.warning(f"Failed to import google.genai: {str(e)}")
    logging.warning("Gemini service will be disabled")

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        """初始化 Gemini 服务"""
        # 从配置文件中读取Gemini API配置
        gemini_config = config_loader.get_gemini_config()
        self.api_key = gemini_config.get("api_key")
        self.model_name = gemini_config.get("model", "gemini-1.5-flash")
        self.model = None

        if genai and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.model = self.client.models
                logger.info("Gemini API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {str(e)}")
                logger.warning("Gemini service will be disabled")
        else:
            if not genai:
                logger.warning("google.genai not installed, Gemini service disabled")
            elif not self.api_key:
                logger.warning("No Gemini API key found, using mock responses")

    def generate_recommendation_reason(
        self, user_query: str, books: List[Dict[str, Any]]
    ) -> str:
        """使用 Gemini 生成推荐理由

        Args:
            user_query: 用户查询需求
            books: 推荐的图书列表

        Returns:
            生成的推荐理由
        """
        if not self.model:
            return "根据您的需求，我们为您推荐了以下图书。"

        try:
            # 格式化图书信息
            books_info = "\n".join(
                [
                    f"- {book.get('title', '未知书名')}（作者：{book.get('author', '未知作者')}，ISBN：{book.get('isbn', '未知ISBN')}）"
                    for book in books[:5]  # 只使用前5本图书
                ]
            )

            prompt = f"""您是一个专业的图书推荐助手。根据用户的查询需求和推荐的图书列表，为用户生成一个友好、专业的推荐理由。
            
            用户需求：{user_query}
            
            推荐图书：
            {books_info}
            
            请生成一个简短的推荐理由，说明为什么这些图书适合用户的需求，不要包含任何无关的内容。
            """

            response = self.model.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            return "根据您的需求，我们为您推荐了以下图书。"
        except Exception as e:
            logger.error(
                f"Error generating recommendation reason with Gemini: {str(e)}"
            )
            return "根据您的需求，我们为您推荐了以下图书。"

    def is_available(self) -> bool:
        """检查 Gemini API 是否可用

        Returns:
            bool: Gemini API 是否可用
        """
        return self.model is not None

    def get_embedding(self, text: str) -> list:
        """使用 Gemini API 获取文本嵌入

        Args:
            text: 需要嵌入的文本

        Returns:
            list: 文本的嵌入向量
        """
        if not genai or not self.api_key:
            logger.warning("Gemini API not available for embedding")
            return []

        try:
            client = genai.Client(api_key=self.api_key)
            result = client.models.embed_content(
                model="models/embedding-001",
                contents=text,
                config={"task_type": "retrieval_document"},
            )
            return getattr(result, "embedding", []) or []
        except Exception as e:
            logger.error(f"Error getting embedding from Gemini: {str(e)}")
            return []
