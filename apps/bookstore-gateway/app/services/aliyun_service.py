from typing import Any, List

import logging

from app.utils.config_loader import config_loader

# 尝试导入dashscope，如果失败则设置为None
try:
    import dashscope
    from http import HTTPStatus
except ImportError as e:
    dashscope = None
    HTTPStatus = None
    logging.warning(f"Failed to import dashscope: {str(e)}")
    logging.warning("Aliyun service will be disabled")

logger = logging.getLogger(__name__)


class AliyunService:
    def __init__(self):
        """初始化阿里云百炼服务"""
        # 从配置文件中读取阿里云百炼API配置
        vector_config = config_loader.get_vector_config()
        providers = vector_config.get("providers", {})
        aliyun_config = providers.get("aliyun", {})
        
        self.api_key = aliyun_config.get("api_key")
        self.model_name = aliyun_config.get("model", "text-embedding-v4")
        self.dimensions = aliyun_config.get("dimensions", 1024)
        
        if dashscope and self.api_key:
            try:
                dashscope.api_key = self.api_key
                logger.info("Aliyun DashScope initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Aliyun DashScope: {str(e)}")
                logger.warning("Aliyun service will be disabled")
        else:
            if not dashscope:
                logger.warning(
                    "dashscope not installed, Aliyun service disabled"
                )
            elif not self.api_key:
                logger.warning("No Aliyun API key found, Aliyun service disabled")

    def is_available(self) -> bool:
        """检查阿里云百炼服务是否可用

        Returns:
            bool: 阿里云百炼服务是否可用
        """
        return dashscope is not None and self.api_key is not None

    def get_embedding(self, text: str) -> list:
        """使用阿里云百炼API获取文本嵌入

        Args:
            text: 需要嵌入的文本

        Returns:
            list: 文本的嵌入向量
        """
        if not self.is_available():
            logger.warning("Aliyun API not available for embedding")
            return []

        try:
            # 使用阿里云百炼的嵌入功能
            result = dashscope.TextEmbedding.call(
                model=self.model_name,
                input=text,
                dimension=self.dimensions,
                output_type="dense"
            )
            
            if result.status_code == HTTPStatus.OK:
                return result.output['embeddings'][0]['embedding']
            else:
                logger.error(f"Error getting embedding from Aliyun: {result.message}")
                return []
        except Exception as e:
            logger.error(f"Error getting embedding from Aliyun: {str(e)}")
            return []

    def generate_recommendation_reason(
        self, user_query: str, books: List[dict]
    ) -> str:
        """使用阿里云百炼生成推荐理由

        Args:
            user_query: 用户查询需求
            books: 推荐的图书列表

        Returns:
            生成的推荐理由
        """
        # 注意：此功能需要使用阿里云百炼的生成模型，
        # 这里仅作为示例，实际实现需要额外配置
        logger.warning("Recommendation reason generation not implemented for Aliyun service")
        return "根据您的需求，我们为您推荐了以下图书。"


# 全局阿里云服务实例
ali_service = AliyunService()
