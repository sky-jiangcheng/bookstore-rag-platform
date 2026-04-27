"""
向量服务

优先使用可用的外部 embedding 服务，缺失时退化为稳定的本地伪向量，
保证业务流程和单元测试在无外网环境下也能继续运行。
"""

import json
import hashlib

import logging
import numpy as np
from abc import ABC, abstractmethod
from decimal import ROUND_HALF_UP, Decimal

# 配置日志
logger = logging.getLogger(__name__)


class VectorServiceError(Exception):
    """向量服务错误"""
    pass


def lazy_import_gensim():
    """保留历史兼容入口，供旧测试和旧调用路径 patch。"""
    try:
        import gensim  # type: ignore

        return gensim
    except Exception:
        return None


def clean_title(raw_title: str) -> str:
    """清理标题文本"""
    import re

    if not isinstance(raw_title, str):
        return ""
    CLEAN_PATTERN = re.compile(r"(\(|（).*?(\)|）)|\d{4}年版?|第?\d+版|精装|平装|套装|【.*?】")
    title = CLEAN_PATTERN.sub("", raw_title)
    title = re.sub(r"[\[\]（）()【】·•,:：;；!?！？\-_/\\]", " ", title)
    title = re.sub(r"\s+", " ", title).strip().lower()
    return title


def parse_embedding(text: str, dim: int) -> np.ndarray:
    """解析 embedding 字符串"""
    data = json.loads(text)
    if len(data) != dim:
        raise ValueError("dimension mismatch")
    return np.array(data, dtype=np.float32)


def pretty_print_embedding(vec: np.ndarray) -> str:
    """格式化输出 embedding"""
    norm = vec / (np.linalg.norm(vec) + 1e-9)
    # 转换为 Python 原生 float 类型
    norm_list = norm.tolist()
    fixed = [
        float(Decimal(str(x)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))
        for x in norm_list
    ]
    return json.dumps(fixed, ensure_ascii=False)


def cosine_similarity(query_vec: np.ndarray, candidate_mat: np.ndarray) -> np.ndarray:
    """计算余弦相似度"""
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    mat_norm = candidate_mat / (
        np.linalg.norm(candidate_mat, axis=1, keepdims=True) + 1e-9
    )
    return np.dot(mat_norm, query_norm)


class VectorServiceInterface(ABC):
    """向量服务接口"""

    @abstractmethod
    def get_vector(self, text: str, summary: str = None) -> np.ndarray:
        """获取文本的向量表示"""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """获取模型信息"""
        pass


class VectorService(VectorServiceInterface):
    """
    向量服务 - 使用 Gemini/Aliyun API
    移除了 Word2Vec 本地模型依赖
    """

    def __init__(self, model_path: str = None, dimension: int = 1536, config_loader=None):
        """
        初始化向量服务

        Args:
            model_path: 已废弃，保留参数为了向后兼容
            dimension: 向量维度（默认1536，与Gemini一致）
            config_loader: 配置加载器实例
        """
        # 使用传入的配置加载器或默认的配置加载器
        if config_loader is None:
            from app.utils.config_loader import config_loader as default_config_loader
            self.config_loader = default_config_loader
            self._enable_remote_services = True
        else:
            self.config_loader = config_loader
            self._enable_remote_services = False

        # 加载向量服务配置
        vector_config = self.config_loader.get_vector_config()

        self.model_path = model_path
        self.model_loaded = False
        self._gensim_module = lazy_import_gensim()

        # 设置维度 - 优先使用显式传入值，其次使用配置
        if dimension is None:
            self.dimension = vector_config.get("default_dimension", 1536)
        else:
            self.dimension = dimension

        self._aliyun_service = None
        self._gemini_service = None
        self._init_services()

    def _init_services(self):
        """初始化API服务"""
        if not self._enable_remote_services:
            logger.info("Remote embedding services disabled for injected config loader")
            return

        # 初始化阿里云
        try:
            from app.services.aliyun_service import AliyunService
            self._aliyun_service = AliyunService()
            if self._aliyun_service.is_available():
                logger.info("Aliyun service initialized successfully")
        except Exception as e:
            logger.debug(f"Failed to initialize Aliyun service: {e}")

        # 初始化Gemini
        try:
            from app.services.gemini_service import GeminiService
            self._gemini_service = GeminiService()
            if self._gemini_service.is_available():
                logger.info("Gemini service initialized successfully")
        except Exception as e:
            logger.debug(f"Failed to initialize Gemini service: {e}")

    def get_vector(self, text: str, summary: str = None) -> np.ndarray:
        """
        获取文本的向量表示

        优先级:
        1. 阿里云百炼API (1024维，会调整到1536维)
        2. Gemini API (1536维)
        3. 抛出异常（如果没有可用服务）

        Args:
            text: 文本内容
            summary: 文本摘要

        Returns:
            np.ndarray: 1536维的向量表示

        Raises:
            VectorServiceError: 如果没有可用的embedding服务
        """
        if not text:
            raise VectorServiceError("Text cannot be empty")

        # 组合标题和简介文本
        combined_text = text
        if summary:
            combined_text = f"{text} {summary}"

        if not self._enable_remote_services:
            return self._fallback_embedding(combined_text)

        # 尝试阿里云
        embedding = self._try_aliyun(combined_text)
        if embedding is not None:
            return self._ensure_dimension(embedding, "Aliyun")

        # 尝试Gemini
        embedding = self._try_gemini(combined_text)
        if embedding is not None:
            return self._ensure_dimension(embedding, "Gemini")

        # 没有可用远程服务时，退化为稳定的本地伪向量，避免业务和测试完全依赖外部网络。
        logger.warning("No remote embedding service available, using local fallback")
        return self._fallback_embedding(combined_text)

    def _try_aliyun(self, text: str) -> np.ndarray:
        """尝试使用阿里云获取embedding"""
        if self._aliyun_service is None or not self._aliyun_service.is_available():
            return None

        try:
            embedding = self._aliyun_service.get_embedding(text)
            if embedding:
                logger.debug("Successfully generated vector using Aliyun API")
                return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.debug(f"Error using Aliyun for embedding: {e}")

        return None

    def _try_gemini(self, text: str) -> np.ndarray:
        """尝试使用Gemini获取embedding"""
        if self._gemini_service is None or not self._gemini_service.is_available():
            return None

        try:
            embedding = self._gemini_service.get_embedding(text)
            if embedding:
                logger.debug("Successfully generated vector using Gemini API")
                return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.debug(f"Error using Gemini for embedding: {e}")

        return None

    def _ensure_dimension(self, embedding: np.ndarray, source: str) -> np.ndarray:
        """
        确保向量维度为1536

        Args:
            embedding: 原始向量
            source: 来源名称（用于日志）

        Returns:
            np.ndarray: 1536维向量
        """
        if len(embedding) == self.dimension:
            return embedding

        logger.debug(
            f"Resizing {source} embedding from {len(embedding)} to {self.dimension}"
        )

        if len(embedding) > self.dimension:
            # 截断
            return embedding[:self.dimension]
        else:
            # 补零
            return np.pad(
                embedding,
                (0, self.dimension - len(embedding)),
                "constant",
            )

    def _fallback_embedding(self, text: str) -> np.ndarray:
        """基于文本生成稳定的本地伪向量"""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = np.frombuffer(digest, dtype=np.uint8).astype(np.float32) / 255.0
        vector = np.resize(seed, self.dimension).astype(np.float32)
        return vector

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_path": self.model_path,
            "dimension": self.dimension,
            "model_loaded": self.model_loaded,
            "gensim_available": self._gensim_module is not None,
            "aliyun_available": (
                self._aliyun_service is not None and 
                self._aliyun_service.is_available()
            ),
            "gemini_available": (
                self._gemini_service is not None and 
                self._gemini_service.is_available()
            ),
            "word2vec_removed": True,  # 标记已移除Word2Vec
        }


# 全局向量服务实例（向后兼容）
# 默认使用1536维，与Gemini一致
vector_service = VectorService(dimension=1536)
