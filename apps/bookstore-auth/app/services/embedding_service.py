"""
嵌入模型服务 - 支持多种嵌入模型
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import jieba
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

from app.services.rag_config import rag_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """嵌入模型服务"""

    def __init__(self):
        self.config = rag_config.embedding_model
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self._load_model()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _get_device(self) -> str:
        """获取设备类型"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_model(self):
        """加载嵌入模型"""
        try:
            model_name = self.config["model_name"]

            if "bge" in model_name.lower():
                # BGE模型加载
                self.model = SentenceTransformer(model_name, device=self.device)
                logger.info(f"Loaded BGE model: {model_name} on {self.device}")
            else:
                # 其他模型加载
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name).to(self.device)
                logger.info(f"Loaded model: {model_name} on {self.device}")

        except Exception as e:
            logger.error(
                f"Failed to load embedding model {self.config['model_name']}: {e}"
            )
            # 降级到简单模型
            self._load_fallback_model()

    def _load_fallback_model(self):
        """加载备用模型"""
        try:
            fallback_model = (
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.model = SentenceTransformer(fallback_model, device=self.device)
            logger.warning(f"Loaded fallback model: {fallback_model}")
        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            # 最后降级到随机向量
            self.model = None

    def preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not text or not isinstance(text, str):
            return ""

        # 清理文本
        import re

        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)  # 保留中英文和数字
        text = re.sub(r"\s+", " ", text).strip()

        # 中文分词
        if self._contains_chinese(text):
            words = jieba.lcut(text)
            text = " ".join(words)

        return text

    def _contains_chinese(self, text: str) -> bool:
        """检查是否包含中文"""
        return any("\u4e00" <= char <= "\u9fff" for char in text)

    def encode_text(self, text: str) -> List[float]:
        """编码单个文本"""
        try:
            # 预处理
            cleaned_text = self.preprocess_text(text)
            if not cleaned_text:
                return np.zeros(self.config["dimension"]).tolist()

            # 截断文本
            max_length = self.config["max_length"]
            if len(cleaned_text) > max_length * 4:  # 粗略估算字符数
                cleaned_text = cleaned_text[: max_length * 4]

            # 生成嵌入向量
            if isinstance(self.model, SentenceTransformer):
                embedding = self.model.encode(
                    cleaned_text, convert_to_numpy=True, normalize_embeddings=True
                )
            else:
                embedding = self._encode_with_transformers(cleaned_text)

            # 降维到配置的维度
            target_dim = self.config["dimension"]
            if len(embedding) > target_dim:
                # 使用简单的降维方法（取前 target_dim 个元素）
                embedding = embedding[:target_dim]
                # 重新归一化
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            elif len(embedding) < target_dim:
                # 补零到目标维度
                embedding = np.pad(
                    embedding, (0, target_dim - len(embedding)), mode="constant"
                )

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return np.random.randn(self.config["dimension"]).tolist()

    def _encode_with_transformers(self, text: str) -> np.ndarray:
        """使用Transformers模型编码"""
        try:
            # 分词
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=self.config["max_length"],
            ).to(self.device)

            # 获取嵌入
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 使用[CLS]标记的嵌入或平均池化
                if (
                    hasattr(outputs, "pooler_output")
                    and outputs.pooler_output is not None
                ):
                    embedding = outputs.pooler_output.squeeze().cpu().numpy()
                else:
                    # 平均池化
                    embedding = (
                        outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                    )

            # 归一化
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            return embedding

        except Exception as e:
            logger.error(f"Failed to encode with transformers: {e}")
            return np.random.randn(self.config["dimension"])

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """批量编码文本"""
        try:
            # 预处理所有文本
            cleaned_texts = [self.preprocess_text(text) for text in texts]

            if isinstance(self.model, SentenceTransformer):
                # 使用SentenceTransformer的批量编码
                embeddings = self.model.encode(
                    cleaned_texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=True,
                )
                return embeddings.tolist()
            else:
                # 手动批量处理
                results = []
                for i in range(0, len(cleaned_texts), batch_size):
                    batch = cleaned_texts[i : i + batch_size]
                    batch_embeddings = []

                    for text in batch:
                        embedding = self._encode_with_transformers(text)
                        batch_embeddings.append(embedding)

                    results.extend(batch_embeddings)

                return [emb.tolist() for emb in results]

        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            # 降级到单个处理
            return [self.encode_text(text) for text in texts]

    def encode_parallel(
        self, texts: List[str], max_workers: int = 4
    ) -> List[List[float]]:
        """并行编码文本"""
        try:
            futures = []
            for text in texts:
                future = self.executor.submit(self.encode_text, text)
                futures.append(future)

            results = []
            for future in as_completed(futures):
                embedding = future.result()
                results.append(embedding)

            return results

        except Exception as e:
            logger.error(f"Failed to encode parallel: {e}")
            # 降级到顺序处理
            return [self.encode_text(text) for text in texts]

    def compute_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """计算两个嵌入向量的余弦相似度"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # 计算余弦相似度
            similarity = np.dot(vec1, vec2) / (
                np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8
            )
            return float(similarity)

        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0

    def compute_batch_similarity(
        self, query_embedding: List[float], candidate_embeddings: List[List[float]]
    ) -> List[float]:
        """批量计算相似度"""
        try:
            query_vec = np.array(query_embedding)
            candidate_matrix = np.array(candidate_embeddings)

            # 归一化
            query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
            candidate_norm = candidate_matrix / (
                np.linalg.norm(candidate_matrix, axis=1, keepdims=True) + 1e-8
            )

            # 计算余弦相似度
            similarities = np.dot(candidate_norm, query_norm)
            return similarities.tolist()

        except Exception as e:
            logger.error(f"Failed to compute batch similarity: {e}")
            return [0.0] * len(candidate_embeddings)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.config["model_name"],
            "dimension": self.config["dimension"],
            "max_length": self.config["max_length"],
            "device": self.device,
            "is_loaded": self.model is not None,
        }

    def __del__(self):
        """清理资源"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)


# 全局嵌入服务实例
embedding_service = EmbeddingService()
