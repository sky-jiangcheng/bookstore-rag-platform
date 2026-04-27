"""
向量数据库服务 - 基于Qdrant
"""
import json
from typing import Any, Dict, List, Optional, Tuple

import hashlib
import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.services.rag_config import rag_config

# from qdrant_client.http.models import CollectionInfo  # 暂时移除，因为可能导致兼容性问题


logger = logging.getLogger(__name__)


class LocalVectorDB:
    """本地内存向量数据库（作为Qdrant的回退）"""
    def __init__(self):
        self.vectors = {}
        self.metadata = {}
        logger.info("Using local in-memory vector database")

    def add_book_vector(self, book_id: int, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """添加书籍向量"""
        point_id = f"book_{book_id}"
        self.vectors[point_id] = vector
        self.metadata[point_id] = metadata
        return True

    def update_book_vector(self, book_id: int, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """更新书籍向量"""
        point_id = f"book_{book_id}"
        self.vectors[point_id] = vector
        self.metadata[point_id] = metadata
        return True

    def delete_book_vector(self, book_id: int) -> bool:
        """删除书籍向量"""
        point_id = f"book_{book_id}"
        if point_id in self.vectors:
            del self.vectors[point_id]
            del self.metadata[point_id]
        return True

    def search_similar_books(
        self,
        query_vector: List[float],
        top_k: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索相似书籍"""
        # 简单的余弦相似度计算
        def cosine_similarity(vec1, vec2):
            import math
            dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
            norm1 = math.sqrt(sum(v * v for v in vec1))
            norm2 = math.sqrt(sum(v * v for v in vec2))
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)

        results = []
        for point_id, vector in self.vectors.items():
            score = cosine_similarity(query_vector, vector)
            if score >= score_threshold:
                book_id = int(point_id.split("_")[1])
                book_metadata = self.metadata.get(point_id, {})
                results.append({
                    "book_id": book_id,
                    "title": book_metadata.get("title", ""),
                    "author": book_metadata.get("author", ""),
                    "score": score,
                    "categories": book_metadata.get("categories", []),
                    "cognitive_level": book_metadata.get("cognitive_level"),
                    "difficulty_level": book_metadata.get("difficulty_level"),
                    "target_audience": book_metadata.get("target_audience", []),
                    "tags": book_metadata.get("tags", []),
                    "semantic_description": book_metadata.get("semantic_description", ""),
                })

        # 按相似度排序并返回前top_k个结果
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def count_vectors(self) -> int:
        """统计向量数量"""
        return len(self.vectors)

    def clear_collection(self) -> bool:
        """清空集合"""
        self.vectors.clear()
        self.metadata.clear()
        return True


class VectorDBService:
    """向量数据库服务"""

    def __init__(self):
        config = rag_config.vector_db
        self.collection_name = config["collection"]
        self.vector_size = rag_config.embedding_model["dimension"]

        if config.get("provider") == "local":
            self.client = LocalVectorDB()
            self.use_local = True
            logger.info("Using local in-memory vector database (free deployment mode)")
            return

        # 尝试连接Qdrant
        try:
            qdrant_url = config.get("url")
            qdrant_api_key = config.get("api_key")

            if qdrant_url:
                self.client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    timeout=config.get("timeout", 30),
                )
            else:
                self.client = QdrantClient(
                    host=config.get("host", "localhost"), 
                    port=config.get("port", 6333), 
                    timeout=config.get("timeout", 30)
                )
            self.use_local = False
            self._ensure_collection()
            logger.info("Connected to Qdrant vector database")
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}. Using local in-memory vector database.")
            self.client = LocalVectorDB()
            self.use_local = True
            

    def bootstrap_from_database(self):
        """从数据库回填本地向量库"""
        if not self.use_local:
            return

        try:
            from app.models import BookInfo
            from app.utils.database import SessionLocal

            db = SessionLocal()
            try:
                books = db.query(BookInfo).filter(BookInfo.embedding.isnot(None)).all()
                loaded = 0
                for book in books:
                    try:
                        vector = json.loads(book.embedding)
                        if not isinstance(vector, list) or len(vector) == 0:
                            continue

                        # 修正向量维度不匹配的问题
                        if len(vector) != self.vector_size:
                            logger.warning(
                                f"Vector dimension mismatch for book {book.id}: "
                                f"expected {self.vector_size}, got {len(vector)}. "
                                "This will affect search results."
                            )
                            # 更新配置的向量维度
                            self.vector_size = len(vector)
                            logger.info(f"Updated vector size to {self.vector_size}")

                        metadata = {
                            "title": book.title,
                            "author": book.author,
                            "categories": [],
                            "cognitive_level": getattr(book, "cognitive_level", None),
                            "difficulty_level": getattr(book, "difficulty_level", None),
                            "target_audience": [],
                            "tags": [],
                            "semantic_description": getattr(book, "semantic_description", ""),
                        }
                        self.client.add_book_vector(book.id, vector, metadata)
                        loaded += 1
                    except Exception as e:
                        logger.error(f"Error loading vector for book {book.id}: {e}")
                        continue

                logger.info("Bootstrapped %s local vectors from database", loaded)
            finally:
                db.close()
        except Exception as exc:
            logger.warning("Failed to bootstrap local vectors from database: %s", exc)

    def _ensure_collection(self):
        """确保集合存在"""
        if self.use_local:
            return
            
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                # 验证向量维度 - 使用更安全的方式来处理API响应
                try:
                    collection_info = self.client.get_collection(self.collection_name)
                    # 检查是否存在params.vectors属性
                    if hasattr(collection_info.config, "params") and hasattr(
                        collection_info.config.params, "vectors"
                    ):
                        if (
                            collection_info.config.params.vectors.size
                            != self.vector_size
                        ):
                            logger.warning(
                                f"Vector size mismatch, expected: {self.vector_size}, got: {collection_info.config.params.vectors.size}"
                            )
                    elif hasattr(collection_info.config, "vector_size"):  # 兼容不同版本的API
                        if collection_info.config.vector_size != self.vector_size:
                            logger.warning(
                                f"Vector size mismatch, expected: {self.vector_size}, got: {collection_info.config.vector_size}"
                            )
                except Exception as validate_error:
                    logger.warning(
                        f"Could not validate vector dimensions: {validate_error}"
                    )

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise

    def _generate_point_id(self, book_id: int) -> str:
        """生成唯一的向量ID"""
        return f"book_{book_id}"

    def add_book_vector(
        self, book_id: int, vector: List[float], metadata: Dict[str, Any]
    ) -> bool:
        """添加书籍向量"""
        try:
            if self.use_local:
                # 直接调用LocalVectorDB的方法
                return self.client.add_book_vector(book_id, vector, metadata)
            else:
                # 使用Qdrant客户端
                point_id = self._generate_point_id(book_id)

                # 构建元数据
                payload = {
                    "book_id": book_id,
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "categories": metadata.get("categories", []),
                    "cognitive_level": metadata.get("cognitive_level", "通用"),
                    "difficulty_level": metadata.get("difficulty_level", 5),
                    "target_audience": metadata.get("target_audience", []),
                    "tags": metadata.get("tags", []),
                    "semantic_description": metadata.get("semantic_description", ""),
                    "created_at": metadata.get("created_at", ""),
                }

                point = PointStruct(id=point_id, vector=vector, payload=payload)

                # 上传向量
                self.client.upsert(collection_name=self.collection_name, points=[point])

                logger.info(f"Added vector for book {book_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to add vector for book {book_id}: {e}")
            return False

    def update_book_vector(
        self, book_id: int, vector: List[float], metadata: Dict[str, Any]
    ) -> bool:
        """更新书籍向量"""
        try:
            if self.use_local:
                # 直接调用LocalVectorDB的方法
                return self.client.update_book_vector(book_id, vector, metadata)
            else:
                # 使用Qdrant客户端
                point_id = self._generate_point_id(book_id)

                # 构建元数据
                payload = {
                    "book_id": book_id,
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "categories": metadata.get("categories", []),
                    "cognitive_level": metadata.get("cognitive_level", "通用"),
                    "difficulty_level": metadata.get("difficulty_level", 5),
                    "target_audience": metadata.get("target_audience", []),
                    "tags": metadata.get("tags", []),
                    "semantic_description": metadata.get("semantic_description", ""),
                    "updated_at": metadata.get("updated_at", ""),
                }

                point = PointStruct(id=point_id, vector=vector, payload=payload)

                # 更新向量
                self.client.upsert(collection_name=self.collection_name, points=[point])

                logger.info(f"Updated vector for book {book_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update vector for book {book_id}: {e}")
            return False

    def delete_book_vector(self, book_id: int) -> bool:
        """删除书籍向量"""
        try:
            if self.use_local:
                # 直接调用LocalVectorDB的方法
                return self.client.delete_book_vector(book_id)
            else:
                # 使用Qdrant客户端
                point_id = self._generate_point_id(book_id)

                self.client.delete(
                    collection_name=self.collection_name, points_selector=[point_id]
                )

                logger.info(f"Deleted vector for book {book_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete vector for book {book_id}: {e}")
            return False

    def search_similar_books(
        self,
        query_vector: List[float],
        top_k: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索相似书籍"""
        try:
            if self.use_local:
                # 直接调用LocalVectorDB的方法
                return self.client.search_similar_books(
                    query_vector, top_k, score_threshold, filters
                )
            else:
                # 使用Qdrant客户端
                search_params = rag_config.search_params

                # 构建过滤条件
                query_filter = None
                if filters:
                    conditions = []
                    for field, value in filters.items():
                        if isinstance(value, list):
                            conditions.append(
                                FieldCondition(key=field, match=MatchValue(any=value))
                            )
                        else:
                            conditions.append(
                                FieldCondition(key=field, match=MatchValue(value=value))
                            )

                    if conditions:
                        query_filter = Filter(must=conditions)

                # 执行搜索
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=min(top_k, search_params["max_candidates"]),
                    score_threshold=score_threshold,
                )

                # 格式化结果
                results = []
                for hit in search_result:
                    results.append(
                        {
                            "book_id": hit.payload.get("book_id"),
                            "title": hit.payload.get("title"),
                            "author": hit.payload.get("author"),
                            "score": hit.score,
                            "categories": hit.payload.get("categories", []),
                            "cognitive_level": hit.payload.get("cognitive_level"),
                            "difficulty_level": hit.payload.get("difficulty_level"),
                            "target_audience": hit.payload.get("target_audience", []),
                            "tags": hit.payload.get("tags", []),
                            "semantic_description": hit.payload.get(
                                "semantic_description", ""
                            ),
                        }
                    )

                return results

        except Exception as e:
            logger.error(f"Failed to search similar books: {e}")
            return []

    def batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[List[Dict[str, Any]]]:
        """批量搜索"""
        try:
            search_results = []

            for query_vector in query_vectors:
                results = self.search_similar_books(
                    query_vector=query_vector, top_k=top_k, filters=filters
                )
                search_results.append(results)

            return search_results

        except Exception as e:
            logger.error(f"Failed to batch search: {e}")
            return [[] for _ in query_vectors]

    def get_collection_info(self):
        """获取集合信息"""
        try:
            if self.use_local:
                # 返回本地集合信息的模拟对象
                class MockCollectionInfo:
                    def __init__(self, points_count):
                        self.points_count = points_count
                        class Config:
                            pass
                        self.config = Config()
                return MockCollectionInfo(len(self.client.vectors))
            else:
                return self.client.get_collection(self.collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise

    def count_vectors(self) -> int:
        """统计向量数量"""
        try:
            if self.use_local:
                return self.client.count_vectors()
            else:
                collection_info = self.get_collection_info()
                return collection_info.points_count
        except Exception as e:
            logger.error(f"Failed to count vectors: {e}")
            return 0

    def clear_collection(self) -> bool:
        """清空集合"""
        try:
            if self.use_local:
                return self.client.clear_collection()
            else:
                self.client.delete_collection(self.collection_name)
                self._ensure_collection()
                logger.info(f"Cleared collection: {self.collection_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False


# 全局向量数据库服务实例
vector_db = VectorDBService()
