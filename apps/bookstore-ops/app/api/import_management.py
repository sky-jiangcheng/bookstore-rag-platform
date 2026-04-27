import json
import os

import logging
import pandas as pd
import tempfile
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.models.import_model import ImportData, ImportRecord
from app.services.log_service import LogService
from app.services.permission_service import require_permission
from app.services.vector_db_service import vector_db
from app.services.vector_service import (
    VectorService,
    clean_title,
    pretty_print_embedding,
)
from app.utils.database import get_db

router = APIRouter()

# 获取日志记录器
logger = logging.getLogger(__name__)

vector_service = VectorService(dimension=1536)
log_service = LogService()


@router.post("/upload")
async def upload_file(
    files: list[UploadFile] = File(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    total_success_count = 0
    total_failure_count = 0
    import_records = []

    try:
        # 处理文件列表
        if files:
            all_files = files
        elif file:
            all_files = [file]
        else:
            logger.warning("No files provided in request")
            return {"successCount": 0, "failureCount": 0, "message": "请提供文件进行上传"}

        logger.info(f"Received file upload request with {len(all_files)} files")

        for file in all_files:
            file_success_count = 0
            file_failure_count = 0
            file_status = "SUCCESS"
            file_error_message = None

            try:
                logger.info(f"Processing file: {file.filename}")

                if not file.filename:
                    logger.warning("File with no filename")
                    total_failure_count += 1
                    continue

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

                # 创建导入记录
                import_record = ImportRecord(
                    filename=file.filename,
                    file_size=file_size,
                    file_type=file_type,
                    status="PROCESSING",
                )
                db.add(import_record)
                db.commit()  # 提交以获取自增ID
                import_id = import_record.id
                import_records.append(import_id)
                logger.info(
                    f"Created import record with ID: {import_id} for file: {file.filename}"
                )

                # 读取文件
                if file.filename.endswith(".csv"):
                    df = pd.read_csv(temp_file_path)
                elif file.filename.endswith(".xlsx"):
                    df = pd.read_excel(temp_file_path)
                else:
                    logger.warning(f"Unsupported file format: {file.filename}")
                    raise HTTPException(
                        status_code=400, detail="Unsupported file format"
                    )

                # 打印列名以便调试
                logger.info(f"File columns: {list(df.columns)}")
                logger.info(f"Total rows: {len(df)}")

                # 处理数据
                processed_barcodes = set()  # 用于跟踪已处理的条码，避免重复处理

                for index, row in df.iterrows():
                    row_success = False
                    row_error = None

                    try:
                        # 尝试多种可能的列名映射
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

                        # 创建导入数据记录（无论成功失败都创建）
                        original_data = {}
                        for col in df.columns:
                            try:
                                original_data[col] = (
                                    str(row.get(col))
                                    if row.get(col) is not None
                                    else None
                                )
                            except Exception:
                                original_data[col] = None

                        # 创建导入数据记录
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
                        db.add(import_data)

                        if not barcode or not title:
                            logger.warning(
                                f"Missing required fields at row {index+1}: barcode={barcode}, title={title}"
                            )
                            row_error = "Missing required fields: barcode or title"
                            file_failure_count += 1
                            total_failure_count += 1
                        elif barcode in processed_barcodes:
                            logger.warning(
                                f"Duplicate barcode at row {index+1}: {barcode}"
                            )
                            row_error = "Duplicate barcode in file"
                            file_failure_count += 1
                            total_failure_count += 1
                        else:
                            # 处理其他字段
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

                            # 处理价格（转换为分）
                            price_value = row.get("price") or row.get("价格")
                            price = (
                                int(float(price_value) * 100) if price_value else None
                            )

                            # 处理库存
                            stock = (
                                int(row.get("stock", 0))
                                if row.get("stock")
                                else int(row.get("库存", 0))
                                if row.get("库存")
                                else 0
                            )

                            # 处理折扣（转换为百分比）
                            discount_value = row.get("discount") or row.get("折扣")
                            discount = (
                                int(float(discount_value) * 100)
                                if discount_value
                                else 0
                            )

                            # 生成向量
                            vector = vector_service.get_vector(title_clean, summary)
                            embedding = pretty_print_embedding(vector)

                            # 更新导入数据记录
                            import_data.author = author
                            import_data.publisher = publisher
                            import_data.series = series
                            import_data.price = price
                            import_data.stock = stock
                            import_data.discount = discount

                            # 检查是否已存在于主库（去重）
                            existing_book = (
                                db.query(BookInfo)
                                .filter(BookInfo.barcode == barcode)
                                .first()
                            )
                            if existing_book:
                                # 更新现有记录
                                existing_book.title = title
                                existing_book.title_clean = title_clean
                                existing_book.author = author
                                existing_book.publisher = publisher
                                existing_book.series = series
                                existing_book.summary = summary
                                existing_book.price = (
                                    price / 100 if price else None
                                )  # 转换为元
                                existing_book.stock = stock
                                existing_book.discount = (
                                    discount / 100 if discount else 0
                                )  # 转换为小数
                                existing_book.embedding = embedding

                                # 同步更新向量数据库
                                try:
                                    vector = vector_service.get_vector(
                                        title_clean
                                    ).tolist()
                                    metadata = {
                                        "title": title,
                                        "author": author,
                                        "publisher": publisher,
                                        "series": series,
                                        "summary": summary,
                                    }
                                    vector_db.update_book_vector(
                                        existing_book.id, vector, metadata
                                    )
                                    logger.info(
                                        f"Updated vector for existing book in vector DB: barcode={barcode}, title={title}"
                                    )
                                except Exception as vector_error:
                                    logger.error(
                                        f"Error updating vector in vector DB: {str(vector_error)}"
                                    )

                                logger.info(
                                    f"Updated existing book in main library: barcode={barcode}, title={title}"
                                )
                            else:
                                try:
                                    # 创建新记录
                                    new_book = BookInfo(
                                        barcode=barcode,
                                        title=title,
                                        title_clean=title_clean,
                                        author=author,
                                        publisher=publisher,
                                        series=series,
                                        summary=summary,
                                        price=price / 100 if price else None,  # 转换为元
                                        stock=stock,
                                        discount=discount / 100
                                        if discount
                                        else 0,  # 转换为小数
                                        embedding=embedding,
                                    )
                                    db.add(new_book)

                                    # 同步添加向量到向量数据库
                                    try:
                                        # 直接使用 new_book 实例，不需要 flush
                                        vector = vector_service.get_vector(
                                            title_clean
                                        ).tolist()
                                        metadata = {
                                            "title": title,
                                            "author": author,
                                            "publisher": publisher,
                                            "series": series,
                                            "summary": summary,
                                        }
                                        # 注意：这里可能会因为 new_book.id 未分配而失败
                                        # 但我们会捕获异常，确保导入过程继续
                                        vector_db.add_book_vector(
                                            new_book.id, vector, metadata
                                        )
                                        logger.info(
                                            f"Added vector for new book to vector DB: barcode={barcode}, title={title}"
                                        )
                                    except Exception as vector_error:
                                        logger.error(
                                            f"Error adding vector to vector DB: {str(vector_error)}"
                                        )

                                    logger.info(
                                        f"Added new book to main library: barcode={barcode}, title={title}"
                                    )
                                except Exception as insert_error:
                                    # 捕获插入错误，可能是唯一键冲突
                                    logger.warning(
                                        f"Error inserting book, trying to update instead: {str(insert_error)}"
                                    )
                                    # 再次检查是否存在
                                    existing_book = (
                                        db.query(BookInfo)
                                        .filter(BookInfo.barcode == barcode)
                                        .first()
                                    )
                                    if existing_book:
                                        # 更新现有记录
                                        existing_book.title = title
                                        existing_book.title_clean = title_clean
                                        existing_book.author = author
                                        existing_book.publisher = publisher
                                        existing_book.series = series
                                        existing_book.summary = summary
                                        existing_book.price = (
                                            price / 100 if price else None
                                        )
                                        existing_book.stock = stock
                                        existing_book.discount = (
                                            discount / 100 if discount else 0
                                        )
                                        existing_book.embedding = embedding

                                        # 同步更新向量数据库
                                        try:
                                            vector = vector_service.get_vector(
                                                title_clean
                                            ).tolist()
                                            metadata = {
                                                "title": title,
                                                "author": author,
                                                "publisher": publisher,
                                                "series": series,
                                                "summary": summary,
                                            }
                                            vector_db.update_book_vector(
                                                existing_book.id, vector, metadata
                                            )
                                            logger.info(
                                                f"Updated vector for existing book in vector DB: barcode={barcode}, title={title}"
                                            )
                                        except Exception as vector_error:
                                            logger.error(
                                                f"Error updating vector in vector DB: {str(vector_error)}"
                                            )

                                        logger.info(
                                            f"Updated existing book after insert error: barcode={barcode}, title={title}"
                                        )
                                    else:
                                        # 如果仍然不存在，可能是其他错误
                                        raise

                            # 更新导入数据状态
                            import_data.status = "SUCCESS"
                            row_success = True
                            file_success_count += 1
                            total_success_count += 1
                            processed_barcodes.add(barcode)  # 添加到已处理集合

                    except Exception as e:
                        row_error = str(e)
                        logger.error(
                            f"Error processing row {index+1}: {row_error}, data: {row.to_dict() if hasattr(row, 'to_dict') else str(row)}"
                        )
                        file_failure_count += 1
                        total_failure_count += 1

                    # 更新当前导入数据状态
                    if not row_success and row_error:
                        # 更新当前导入数据状态
                        try:
                            import_data.status = "FAILURE"
                            import_data.error_message = row_error[:500]  # 限制错误消息长度
                        except Exception:
                            pass
                    else:
                        # 更新为成功状态
                        try:
                            import_data.status = "SUCCESS"
                        except Exception:
                            pass

                # 更新导入记录状态
                import_record.success_count = file_success_count
                import_record.failure_count = file_failure_count
                import_record.status = "SUCCESS"

                # 统计失败原因
                failure_reasons = {}
                try:
                    # 查询失败的导入数据
                    failed_records = (
                        db.query(ImportData)
                        .filter(
                            ImportData.import_id == import_id,
                            ImportData.status == "FAILURE",
                        )
                        .all()
                    )

                    for record in failed_records:
                        if record.error_message:
                            reason = record.error_message
                            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                except Exception:
                    pass

                # 记录批量操作日志
                operation_data = {
                    "import_id": import_id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "file_type": file_type,
                    "success_count": file_success_count,
                    "failure_count": file_failure_count,
                    "total_records": file_success_count + file_failure_count,
                    "failure_reasons": failure_reasons,
                }
                log_service.record_batch_operation(
                    operation_type="IMPORT_BOOKS",
                    status="SUCCESS" if file_success_count > 0 else "FAILURE",
                    batch_size=file_success_count + file_failure_count,
                    success_count=file_success_count,
                    failure_count=file_failure_count,
                    user_id=None,
                    details=operation_data,
                )

                logger.info(
                    f"Successfully processed file: {file.filename}, {file_success_count} success, {file_failure_count} failure"
                )

            except HTTPException as e:
                # 重新抛出HTTPException，让FastAPI处理
                if "import_record" in locals():
                    import_record.status = "FAILURE"
                    import_record.error_message = str(e)[:500]
                raise
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing file {file.filename}: {error_msg}")
                file_failure_count += 1
                total_failure_count += 1
                file_status = "FAILURE"
                file_error_message = error_msg[:500]  # 限制错误消息长度

                # 更新导入记录状态
                if "import_record" in locals():
                    import_record.status = "FAILURE"
                    import_record.error_message = file_error_message

                    # 记录批量操作日志（失败）
                    operation_data = {
                        "filename": file.filename,
                        "error_message": file_error_message,
                    }
                    if "import_id" in locals():
                        operation_data["import_id"] = import_id

                    log_service.record_batch_operation(
                        operation_type="IMPORT_BOOKS",
                        status="FAILURE",
                        batch_size=0,
                        success_count=0,
                        failure_count=1,
                        user_id=None,
                        details=operation_data,
                    )
            finally:
                # 清理临时文件
                if "temp_file_path" in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

                # 确保导入记录状态被更新
                if "import_record" in locals():
                    import_record.success_count = file_success_count
                    import_record.failure_count = file_failure_count
                    if file_status == "FAILURE":
                        import_record.status = "FAILURE"
                        import_record.error_message = file_error_message

        # 提交所有事务
        db.commit()

        logger.info(
            f"File upload completed: {total_success_count} success, {total_failure_count} failure"
        )

        return {
            "successCount": total_success_count,
            "failureCount": total_failure_count,
            "importRecords": import_records,
            "message": f"导入完成，成功 {total_success_count} 条，失败 {total_failure_count} 条",
        }

    except HTTPException:
        # 重新抛出HTTPException，让FastAPI处理
        if "db" in locals():
            db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_file: {str(e)}")
        if "db" in locals():
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/records")
async def get_import_records(
    page: int = 1, limit: int = 20, status: str = None, db: Session = Depends(get_db)
):
    """
    获取导入记录列表
    """
    try:
        # 构建查询
        query = db.query(ImportRecord)

        # 添加状态过滤
        if status:
            query = query.filter(ImportRecord.status == status)

        # 计算总数
        total = query.count()

        # 添加分页
        records = (
            query.order_by(ImportRecord.create_time.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        # 转换为字典
        records_list = []
        for record in records:
            records_list.append(
                {
                    "id": record.id,
                    "filename": record.filename,
                    "fileSize": record.file_size,
                    "fileType": record.file_type,
                    "successCount": record.success_count,
                    "failureCount": record.failure_count,
                    "status": record.status,
                    "errorMessage": record.error_message,
                    "createTime": record.create_time,
                    "updateTime": record.update_time,
                }
            )

        logger.info(
            f"Returned {len(records_list)} import records, page: {page}, limit: {limit}, total: {total}"
        )

        return {
            "items": records_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"Error getting import records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/records/{import_id}/data")
async def get_import_data(
    import_id: int,
    page: int = 1,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
):
    """
    获取指定导入记录的详细数据
    """
    try:
        # 检查导入记录是否存在
        import_record = (
            db.query(ImportRecord).filter(ImportRecord.id == import_id).first()
        )
        if not import_record:
            raise HTTPException(status_code=404, detail="Import record not found")

        # 构建查询
        query = db.query(ImportData).filter(ImportData.import_id == import_id)

        # 添加状态过滤
        if status:
            query = query.filter(ImportData.status == status)

        # 计算总数
        total = query.count()

        # 添加分页
        data = (
            query.order_by(ImportData.id).offset((page - 1) * limit).limit(limit).all()
        )

        # 转换为字典
        data_list = []
        for item in data:
            data_list.append(
                {
                    "id": item.id,
                    "importId": item.import_id,
                    "barcode": item.barcode,
                    "title": item.title,
                    "author": item.author,
                    "publisher": item.publisher,
                    "series": item.series,
                    "price": item.price / 100 if item.price else None,  # 转换为元
                    "stock": item.stock,
                    "discount": item.discount / 100 if item.discount else 0,  # 转换为小数
                    "originalData": json.loads(item.original_data)
                    if item.original_data
                    else {},
                    "status": item.status,
                    "errorMessage": item.error_message,
                    "createTime": item.create_time,
                    "updateTime": item.update_time,
                }
            )

        logger.info(
            f"Returned {len(data_list)} import data items for record ID: {import_id}, page: {page}, limit: {limit}, total: {total}"
        )

        return {
            "importRecord": {
                "id": import_record.id,
                "filename": import_record.filename,
                "fileSize": import_record.file_size,
                "fileType": import_record.file_type,
                "successCount": import_record.success_count,
                "failureCount": import_record.failure_count,
                "status": import_record.status,
                "createTime": import_record.create_time,
            },
            "items": data_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
