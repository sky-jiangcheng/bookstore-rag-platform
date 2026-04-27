from typing import List, Optional, Tuple

import lance
import numpy as np
import pyarrow as pa

from app.config import VECTOR_DB_URL, VECTOR_DIMENSION


class VectorDBManager:
    """
    向量数据库管理器，使用LanceDB进行向量存储和相似度搜索
    所有配置从app.config读取，支持配置文件迁移
    """

    def __init__(self, uri: str = None, vector_dim: int = None):
        # 统一从配置文件读取，不再依赖环境变量
        self.uri = uri or VECTOR_DB_URL.replace("lancedb://", "")
        self.vector_dim = vector_dim or VECTOR_DIMENSION
        self.db = None
        self.table = None
        self._init_db()

    def _init_db(self):
        """初始化向量数据库"""
        try:
            # 创建LanceDB数据库
            import lancedb

            self.db = lancedb.connect(self.uri)

            # 检查表是否存在
            table_name = "book_embeddings"
            if table_name in self.db.table_names():
                self.table = self.db[table_name]
            else:
                # 创建表结构
                schema = pa.schema(
                    [
                        pa.field("book_id", pa.int64()),
                        pa.field("title", pa.string()),
                        pa.field("embedding", pa.list_(pa.float32(), self.vector_dim)),
                        pa.field("metadata", pa.string()),  # 存储其他相关信息
                    ]
                )

                # 创建空表
                empty_data = pa.table(
                    {
                        "book_id": pa.array([], type=pa.int64()),
                        "title": pa.array([], type=pa.string()),
                        "embedding": pa.array(
                            [], type=pa.list_(pa.float32(), self.vector_dim)
                        ),
                        "metadata": pa.array([], type=pa.string()),
                    }
                )

                self.table = self.db.create_table(
                    table_name, empty_data, mode="overwrite"
                )
        except ImportError:
            print("Warning: lancedb not installed, using mock implementation")
            self.db = None
            self.table = None

    def insert_vector(
        self, book_id: int, title: str, vector: List[float], metadata: dict = None
    ):
        """
        插入向量到数据库
        """
        if self.table is None:
            return

        metadata_str = str(metadata) if metadata else "{}"

        # 准备数据
        data = pa.table(
            {
                "book_id": [book_id],
                "title": [title],
                "embedding": [vector],
                "metadata": [metadata_str],
            }
        )

        # 添加到表
        self.table.add(data)

    def batch_insert_vectors(
        self,
        book_ids: List[int],
        titles: List[str],
        vectors: List[List[float]],
        metadatas: List[dict] = None,
    ):
        """
        批量插入向量到数据库
        """
        if self.table is None:
            return

        if metadatas is None:
            metadatas = [{}] * len(book_ids)

        metadata_strs = [str(meta) if meta else "{}" for meta in metadatas]

        # 准备数据
        data = pa.table(
            {
                "book_id": book_ids,
                "title": titles,
                "embedding": vectors,
                "metadata": metadata_strs,
            }
        )

        # 添加到表
        self.table.add(data)

    def search_similar(
        self, query_vector: List[float], limit: int = 10, min_score: float = 0.5
    ) -> List[Tuple[int, str, float]]:
        """
        搜索相似向量
        返回: [(book_id, title, similarity_score), ...]
        """
        if self.table is None:
            return []

        try:
            # 执行向量搜索
            result = self.table.search(query_vector).limit(limit).to_arrow()

            results = []
            for i in range(len(result)):
                book_id = result["book_id"][i].as_py()
                title = result["title"][i].as_py()
                # 计算相似度分数（这里简化处理，实际可能会使用特定的距离度量）
                score = self._calculate_similarity(
                    query_vector, result["embedding"][i].as_py()
                )

                if score >= min_score:
                    results.append((book_id, title, score))

            return sorted(results, key=lambda x: x[2], reverse=True)  # 按相似度降序排列

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # 归一化向量
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-9)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-9)

        # 计算余弦相似度
        similarity = np.dot(v1_norm, v2_norm)

        # 确保结果在[0, 1]范围内
        return float(max(0, min(1, (similarity + 1) / 2)))

    def delete_by_book_id(self, book_id: int):
        """
        根据书籍ID删除向量
        """
        if self.table is None:
            return

        self.table.delete(f"book_id = {book_id}")

    def update_vector(
        self, book_id: int, title: str, vector: List[float], metadata: dict = None
    ):
        """
        更新向量（删除再插入）
        """
        self.delete_by_book_id(book_id)
        self.insert_vector(book_id, title, vector, metadata)


# 全局实例
vector_db = VectorDBManager()


def get_vector_db():
    """
    获取向量数据库实例
    """
    return vector_db
