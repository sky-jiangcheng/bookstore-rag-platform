"""
批量处理器 - 优化大批量数据处理的工具

功能:
1. 批量数据库操作
2. 批量向量计算
3. 并发控制
4. 进度回调
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """批量处理器"""

    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers

    def process_in_batches(
        self,
        items: List[Any],
        process_func: Callable[[List[Any]], Tuple[int, int]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        分批处理项目

        Args:
            items: 待处理项目列表
            process_func: 处理函数，接收批次数据，返回 (成功数, 失败数)
            progress_callback: 进度回调函数 (当前进度, 总数, 消息)

        Returns:
            (总成功数, 总失败数, 错误详情列表)
        """
        total_success = 0
        total_failure = 0
        errors = []
        total = len(items)

        logger.info(f"开始批量处理 {total} 个项目，批次大小: {self.batch_size}")

        # 分批处理
        for i in range(0, total, self.batch_size):
            batch = items[i : i + self.batch_size]
            current = len(batch)
            progress = i + current

            try:
                # 更新进度
                if progress_callback:
                    progress_callback(
                        progress,
                        total,
                        f"处理批次 {i//self.batch_size + 1}/{(total-1)//self.batch_size + 1}",
                    )

                # 处理批次
                success, failure = process_func(batch)
                total_success += success
                total_failure += failure

                logger.info(
                    f"批次 {i//self.batch_size + 1} 完成: 成功 {success}, 失败 {failure}"
                )

            except Exception as e:
                error_msg = f"批次 {i//self.batch_size + 1} 处理失败: {str(e)}"
                logger.error(error_msg)
                errors.append({"batch": i // self.batch_size + 1, "error": error_msg})
                total_failure += current

        logger.info(f"批量处理完成: 总计 {total}, 成功 {total_success}, 失败 {total_failure}")

        return total_success, total_failure, errors

    def process_in_batches_parallel(
        self,
        items: List[Any],
        process_func: Callable[[Any], Tuple[bool, Optional[str]]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        并发分批处理项目（适用于独立可并行的处理）

        Args:
            items: 待处理项目列表
            process_func: 处理函数，接收单个项目，返回 (成功标志, 错误消息)
            progress_callback: 进度回调函数 (当前进度, 总数, 消息)

        Returns:
            (总成功数, 总失败数, 错误详情列表)
        """
        total_success = 0
        total_failure = 0
        errors = []
        total = len(items)

        logger.info(
            f"开始并发批量处理 {total} 个项目，批次大小: {self.batch_size}, 并发数: {self.max_workers}"
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            # 提交所有任务
            for i, item in enumerate(items):
                future = executor.submit(process_func, item)
                futures[future] = i

            # 收集结果
            completed = 0
            for future in as_completed(futures):
                try:
                    success, error_msg = future.result()

                    if success:
                        total_success += 1
                    else:
                        total_failure += 1
                        if error_msg:
                            errors.append(
                                {"index": futures[future], "error": error_msg}
                            )

                    completed += 1

                    # 更新进度
                    if progress_callback and completed % 10 == 0:
                        progress_callback(completed, total, f"已完成 {completed}/{total}")

                except Exception as e:
                    total_failure += 1
                    error_msg = f"项目 {futures[future]} 处理异常: {str(e)}"
                    logger.error(error_msg)
                    errors.append({"index": futures[future], "error": error_msg})

            # 最终进度更新
            if progress_callback:
                progress_callback(total, total, "处理完成")

        logger.info(f"并发批量处理完成: 总计 {total}, 成功 {total_success}, 失败 {total_failure}")

        return total_success, total_failure, errors

    def process_in_batches_parallel_optimized(
        self,
        items: List[Any],
        process_func: Callable[[List[Any]], Tuple[int, int, List[str]]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        优化的并发分批处理（先分批，再并发处理批次）

        Args:
            items: 待处理项目列表
            process_func: 处理函数，接收批次数据，返回 (成功数, 失败数, 错误消息列表)
            progress_callback: 进度回调函数 (当前进度, 总数, 消息)

        Returns:
            (总成功数, 总失败数, 错误详情列表)
        """
        total_success = 0
        total_failure = 0
        all_errors = []
        total = len(items)

        logger.info(
            f"开始优化的并发批量处理 {total} 个项目，批次大小: {self.batch_size}, 并发数: {self.max_workers}"
        )

        # 先分批
        batches = [
            items[i : i + self.batch_size] for i in range(0, total, self.batch_size)
        ]
        num_batches = len(batches)

        # 并发处理批次
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(process_func, batch): idx
                for idx, batch in enumerate(batches)
            }

            completed_batches = 0
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]

                try:
                    success, failure, batch_errors = future.result()
                    total_success += success
                    total_failure += failure

                    # 收集错误
                    if batch_errors:
                        for error in batch_errors:
                            all_errors.append({"batch": batch_idx + 1, "error": error})

                    completed_batches += 1

                    # 更新进度
                    if progress_callback:
                        processed = min(completed_batches * self.batch_size, total)
                        progress_callback(
                            processed,
                            total,
                            f"已完成 {completed_batches}/{num_batches} 批次",
                        )

                    logger.info(f"批次 {batch_idx + 1} 完成: 成功 {success}, 失败 {failure}")

                except Exception as e:
                    error_msg = f"批次 {batch_idx + 1} 处理失败: {str(e)}"
                    logger.error(error_msg)
                    all_errors.append({"batch": batch_idx + 1, "error": error_msg})
                    total_failure += len(batches[batch_idx])

                    completed_batches += 1

        logger.info(f"优化的并发批量处理完成: 总计 {total}, 成功 {total_success}, 失败 {total_failure}")

        return total_success, total_failure, all_errors


class DatabaseBatchProcessor:
    """数据库批量处理器"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def bulk_insert(
        self,
        db,
        model_class,
        items: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        批量插入

        Args:
            db: 数据库会话
            model_class: 模型类
            items: 待插入数据列表
            progress_callback: 进度回调

        Returns:
            (成功数, 失败数, 错误列表)
        """
        total_success = 0
        total_failure = 0
        errors = []
        total = len(items)

        logger.info(f"开始批量插入 {total} 条记录，批次大小: {self.batch_size}")

        for i in range(0, total, self.batch_size):
            batch_data = items[i : i + self.batch_size]
            current = len(batch_data)
            progress = i + current

            try:
                # 批量插入
                db_objects = [model_class(**data) for data in batch_data]
                db.bulk_save_objects(db_objects)
                db.commit()

                total_success += current

                # 更新进度
                if progress_callback:
                    progress_callback(
                        progress,
                        total,
                        f"已插入 {progress}/{total} 条记录",
                    )

            except Exception as e:
                db.rollback()
                error_msg = f"批次 {i//self.batch_size + 1} 插入失败: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                total_failure += current

        logger.info(f"批量插入完成: 总计 {total}, 成功 {total_success}, 失败 {total_failure}")

        return total_success, total_failure, errors

    def bulk_update(
        self,
        db,
        model_class,
        updates: List[Tuple[int, Dict[str, Any]]],  # (id, update_data)
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        批量更新

        Args:
            db: 数据库会话
            model_class: 模型类
            updates: 待更新数据列表 (id, update_data)
            progress_callback: 进度回调

        Returns:
            (成功数, 失败数, 错误列表)
        """
        total_success = 0
        total_failure = 0
        errors = []
        total = len(updates)

        logger.info(f"开始批量更新 {total} 条记录，批次大小: {self.batch_size}")

        for i in range(0, total, self.batch_size):
            batch_updates = updates[i : i + self.batch_size]
            current = len(batch_updates)
            progress = i + current

            try:
                # 批量更新
                for obj_id, update_data in batch_updates:
                    db.query(model_class).filter(model_class.id == obj_id).update(
                        update_data
                    )

                db.commit()
                total_success += current

                # 更新进度
                if progress_callback:
                    progress_callback(
                        progress,
                        total,
                        f"已更新 {progress}/{total} 条记录",
                    )

            except Exception as e:
                db.rollback()
                error_msg = f"批次 {i//self.batch_size + 1} 更新失败: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                total_failure += current

        logger.info(f"批量更新完成: 总计 {total}, 成功 {total_success}, 失败 {total_failure}")

        return total_success, total_failure, errors


class VectorBatchProcessor:
    """向量批量处理器"""

    def __init__(
        self,
        embedding_service,
        vector_db_service,
        batch_size: int = 50,
        max_workers: int = 4,
    ):
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.batch_size = batch_size
        self.max_workers = max_workers

    def batch_generate_vectors(
        self,
        texts: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[List[List[float]], List[str]]:
        """
        批量生成向量

        Args:
            texts: 文本列表
            progress_callback: 进度回调

        Returns:
            (向量列表, 错误列表)
        """
        total = len(texts)
        vectors = []
        errors = []

        logger.info(f"开始批量生成 {total} 个向量，批次大小: {self.batch_size}")

        try:
            # 使用嵌入服务的批量编码
            vectors = self.embedding_service.encode_batch(
                texts, batch_size=self.batch_size
            )

            if progress_callback:
                progress_callback(total, total, f"已生成 {total} 个向量")

            logger.info(f"批量向量生成完成: {len(vectors)} 个向量")

        except Exception as e:
            error_msg = f"批量向量生成失败: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        return vectors, errors

    def batch_add_vectors(
        self,
        book_vectors: List[
            Tuple[int, List[float], Dict[str, Any]]
        ],  # (book_id, vector, metadata)
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        批量添加向量到向量数据库

        Args:
            book_vectors: (book_id, vector, metadata) 列表
            progress_callback: 进度回调

        Returns:
            (成功数, 失败数, 错误列表)
        """
        total_success = 0
        total_failure = 0
        errors = []
        total = len(book_vectors)

        logger.info(f"开始批量添加 {total} 个向量，批次大小: {self.batch_size}")

        # 由于Qdrant的upsert本身支持批量，直接使用
        try:
            from qdrant_client.models import PointStruct

            points = []
            for book_id, vector, metadata in book_vectors:
                point_id = f"book_{book_id}"
                point = PointStruct(id=point_id, vector=vector, payload=metadata)
                points.append(point)

            # 批量插入
            self.vector_db_service.client.upsert(
                collection_name=self.vector_db_service.collection_name, points=points
            )

            total_success = total

            if progress_callback:
                progress_callback(total, total, f"已添加 {total} 个向量")

            logger.info(f"批量向量添加完成: {total_success} 个向量")

        except Exception as e:
            error_msg = f"批量向量添加失败: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            total_failure = total

        return total_success, total_failure, errors
