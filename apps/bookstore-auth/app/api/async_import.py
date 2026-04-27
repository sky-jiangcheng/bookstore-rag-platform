"""
异步导入API - 优化大批量数据导入

功能:
1. 异步文件处理
2. 批量数据库操作
3. 批量向量生成
4. 实时进度更新
"""

import json
import logging
import os
import tempfile

import pandas as pd
from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     UploadFile)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.core.async_task_manager import AsyncTask, get_task_manager
from app.models import BookInfo
from app.models.auth import User
from app.models.import_model import ImportData, ImportRecord
from app.services.log_service import LogService
from app.services.vector_service import (VectorService, clean_title,
                                         pretty_print_embedding)
from app.utils.batch_processor import DatabaseBatchProcessor
from app.utils.database import get_db

router = APIRouter()

logger = logging.getLogger(__name__)

vector_service = VectorService(dimension=1536)
log_service = LogService()

# ==================== 请求/响应模型 ====================


class AsyncImportRequest(BaseModel):
    """异步导入请求"""

    filename: str
    file_size: int
    file_type: str


class AsyncImportResponse(BaseModel):
    """异步导入响应"""

    task_id: str
    import_id: int
    message: str
    status: str


# ==================== 核心导入函数 ====================


def process_import_task(
    task: AsyncTask,
    import_id: int,
    file_path: str,
    filename: str,
    db: Session,
):
    """
    处理导入任务（后台执行）

    Args:
        task: 任务对象
        import_id: 导入记录ID
        file_path: 文件路径
        filename: 文件名
        db: 数据库会话
    """
    try:
        file_success_count = 0
        file_failure_count = 0
        processed_barcodes = set()

        # 更新进度
        task.update_progress(5, 100, "读取文件")

        # 读取文件
        if filename.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(file_path)
        else:
            raise Exception(f"不支持的文件格式: {filename}")

        total_rows = len(df)
        logger.info(f"开始处理文件 {filename}, 共 {total_rows} 行")

        task.update_progress(10, total_rows, "开始处理数据")

        # 创建批量处理器
        db_batch_processor = DatabaseBatchProcessor(batch_size=50)

        # 准备待插入数据
        import_records_to_add = []
        books_to_add = []
        books_to_update = []

        # 处理每一行
        for index, row in df.iterrows():
            try:
                # 提取字段
                barcode = (
                    str(row.get("barcode", "")).strip()
                    or str(row.get("条码", "")).strip()
                    or str(row.get("ISBN", "")).strip()
                    or str(row.get("isbn", "")).strip()
                )
                title = (
                    str(row.get("title", "")).strip()
                    or str(row.get("书名", "")).strip()
                    or str(row.get("图书名称", "")).strip()
                )

                # 创建导入数据记录
                original_data = {}
                for col in df.columns:
                    try:
                        original_data[col] = (
                            str(row.get(col)) if row.get(col) is not None else None
                        )
                    except Exception:
                        original_data[col] = None

                import_data = ImportData(
                    import_id=import_id,
                    barcode=barcode or f"EMPTY_{index+1}",
                    title=title or f"Untitled_{index+1}",
                    author=str(row.get("author", "")).strip()
                    or str(row.get("作者", "")).strip(),
                    publisher=str(row.get("publisher", "")).strip()
                    or str(row.get("出版社", "")).strip(),
                    series=str(row.get("series", "")).strip()
                    or str(row.get("系列", "")).strip()
                    or str(row.get("丛书", "")).strip(),
                    price=None,
                    stock=0,
                    discount=0,
                    original_data=json.dumps(original_data, ensure_ascii=False),
                    status="PENDING",
                )
                import_records_to_add.append(import_data)

                if not barcode or not title:
                    import_data.status = "FAILURE"
                    import_data.error_message = (
                        "Missing required fields: barcode or title"
                    )
                    file_failure_count += 1
                elif barcode in processed_barcodes:
                    import_data.status = "FAILURE"
                    import_data.error_message = "Duplicate barcode in file"
                    file_failure_count += 1
                else:
                    processed_barcodes.add(barcode)

                    # 提取其他字段
                    title_clean = clean_title(title)
                    author = (
                        str(row.get("author", "")).strip()
                        or str(row.get("作者", "")).strip()
                    )
                    publisher = (
                        str(row.get("publisher", "")).strip()
                        or str(row.get("出版社", "")).strip()
                    )
                    series = (
                        str(row.get("series", "")).strip()
                        or str(row.get("系列", "")).strip()
                        or str(row.get("丛书", "")).strip()
                    )
                    summary = (
                        str(row.get("summary", "")).strip()
                        or str(row.get("简介", "")).strip()
                        or str(row.get("内容简介", "")).strip()
                    )

                    # 处理价格
                    price_value = row.get("price") or row.get("价格")
                    price = int(float(price_value) * 100) if price_value else None

                    # 处理库存
                    stock = (
                        int(row.get("stock", 0))
                        if row.get("stock")
                        else int(row.get("库存", 0))
                        if row.get("库存")
                        else 0
                    )

                    # 处理折扣
                    discount_value = row.get("discount") or row.get("折扣")
                    discount = int(float(discount_value) * 100) if discount_value else 0

                    # 生成向量
                    vector = vector_service.get_vector(title_clean, summary)
                    embedding = pretty_print_embedding(vector)

                    # 检查是否已存在
                    existing_book = (
                        db.query(BookInfo).filter(BookInfo.barcode == barcode).first()
                    )

                    if existing_book:
                        # 准备更新
                        books_to_update.append(
                            {
                                "id": existing_book.id,
                                "title": title,
                                "title_clean": title_clean,
                                "author": author,
                                "publisher": publisher,
                                "series": series,
                                "summary": summary,
                                "price": price / 100 if price else None,
                                "stock": stock,
                                "discount": discount / 100 if discount else 0,
                                "embedding": embedding,
                            }
                        )
                    else:
                        # 准备插入
                        books_to_add.append(
                            {
                                "barcode": barcode,
                                "title": title,
                                "title_clean": title_clean,
                                "author": author,
                                "publisher": publisher,
                                "series": series,
                                "summary": summary,
                                "price": price / 100 if price else None,
                                "stock": stock,
                                "discount": discount / 100 if discount else 0,
                                "embedding": embedding,
                            }
                        )

                    import_data.status = "SUCCESS"
                    file_success_count += 1

                # 更新进度（每100行）
                if (index + 1) % 100 == 0:
                    progress = int(((index + 1) / total_rows) * 80) + 10
                    task.update_progress(
                        progress,
                        total_rows,
                        f"已处理 {index + 1}/{total_rows} 行",
                    )

            except Exception as e:
                logger.error(f"Error processing row {index+1}: {str(e)}")
                file_failure_count += 1

        # 批量保存导入数据记录
        task.update_progress(90, total_rows, "保存导入记录")
        db.add_all(import_records_to_add)
        db.commit()

        # 批量更新现有书籍
        if books_to_update:
            task.update_progress(92, total_rows, f"更新 {len(books_to_update)} 本现有书籍")
            update_list = [
                (b["id"], {k: v for k, v in b.items() if k != "id"})
                for b in books_to_update
            ]
            db_batch_processor.bulk_update(
                db,
                BookInfo,
                update_list,
                progress_callback=lambda p, t, m: task.update_progress(
                    int(92 + (p / t) * 3), total_rows, m
                ),
            )

        # 批量插入新书籍
        if books_to_add:
            task.update_progress(95, total_rows, f"添加 {len(books_to_add)} 本新书籍")
            db_batch_processor.bulk_insert(
                db,
                BookInfo,
                books_to_add,
                progress_callback=lambda p, t, m: task.update_progress(
                    int(95 + (p / t) * 3), total_rows, m
                ),
            )

        # 更新导入记录
        import_record = (
            db.query(ImportRecord).filter(ImportRecord.id == import_id).first()
        )
        if import_record:
            import_record.success_count = file_success_count
            import_record.failure_count = file_failure_count
            import_record.status = "SUCCESS"
            db.commit()

        # 记录批量操作日志
        operation_data = {
            "import_id": import_id,
            "filename": filename,
            "success_count": file_success_count,
            "failure_count": file_failure_count,
            "total_records": file_success_count + file_failure_count,
        }
        log_service.record_batch_operation(
            operation_type="IMPORT_BOOKS_ASYNC",
            status="SUCCESS",
            batch_size=file_success_count + file_failure_count,
            success_count=file_success_count,
            failure_count=file_failure_count,
            user_id=task.user_id,
            details=operation_data,
        )

        task.update_progress(
            100, total_rows, f"导入完成: 成功 {file_success_count}, 失败 {file_failure_count}"
        )

        logger.info(
            f"异步导入完成: {filename}, 成功 {file_success_count}, 失败 {file_failure_count}"
        )

        # 返回结果
        task.set_success(
            {
                "import_id": import_id,
                "success_count": file_success_count,
                "failure_count": file_failure_count,
            }
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"异步导入失败: {error_msg}")

        # 更新导入记录状态
        try:
            import_record = (
                db.query(ImportRecord).filter(ImportRecord.id == import_id).first()
            )
            if import_record:
                import_record.status = "FAILURE"
                import_record.error_message = error_msg
                db.commit()
        except Exception:
            pass

        task.set_failed(error_msg)


# ==================== API端点 ====================


@router.post("/upload-async", response_model=AsyncImportResponse)
async def upload_file_async(
    files: list[UploadFile] = File(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = None,
):
    """
    异步文件上传 - 适合大批量数据导入

    功能:
    1. 后台异步处理
    2. 实时进度更新
    3. 批量数据库操作优化
    4. 批量向量生成优化

    返回task_id，可通过任务管理API查询进度
    """
    task_manager = get_task_manager()

    # 处理文件列表
    if files:
        all_files = files
    elif file:
        all_files = [file]
    else:
        logger.warning("No files provided in request")
        raise HTTPException(status_code=400, detail="请提供文件进行上传")

    logger.info(f"Received async file upload request with {len(all_files)} files")

    # 目前只支持单文件异步处理
    if len(all_files) > 1:
        raise HTTPException(status_code=400, detail="异步导入暂只支持单文件，请逐个上传")

    file = all_files[0]

    try:
        logger.info(f"Processing file async: {file.filename}")

        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 读取文件内容
        content = await file.read()
        file_size = len(content)

        # 保存临时文件
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        # 确定文件类型
        file_type = (
            "CSV"
            if file.filename.endswith(".csv")
            else "EXCEL"
            if file.filename.endswith(".xlsx")
            else "UNKNOWN"
        )

        if file_type == "UNKNOWN":
            os.unlink(temp_file_path)
            raise HTTPException(status_code=400, detail="不支持的文件格式，仅支持CSV和Excel")

        # 创建导入记录
        import_record = ImportRecord(
            filename=file.filename,
            file_size=file_size,
            file_type=file_type,
            status="PENDING",
        )
        db.add(import_record)
        db.commit()
        db.refresh(import_record)

        # 创建后台任务
        task_id = task_manager.create_task(
            func=process_import_task,
            kwargs={
                "import_id": import_record.id,
                "file_path": temp_file_path,
                "filename": file.filename,
                "db": db,
            },
            name=f"导入文件: {file.filename}",
            user_id=current_user.id,
            background_tasks=background_tasks,
        )

        logger.info(
            f"Created async import task {task_id} for import record {import_record.id}"
        )

        return AsyncImportResponse(
            task_id=task_id,
            import_id=import_record.id,
            message=f"文件已接收，正在后台处理中，可通过task_id: {task_id} 查询进度",
            status="PENDING",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in async file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")
