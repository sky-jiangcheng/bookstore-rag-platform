import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth_management import get_current_active_user
from app.models import BookInfo
from app.models.auth import User
from app.models.purchase import (PurchaseOrder, PurchaseOrderItem,
                                 PurchaseStatus, Supplier)
from app.utils.database import get_db

router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)


# 供应商相关API
@router.get("/suppliers")
async def get_suppliers(
    name: Optional[str] = Query(None, description="供应商名称"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取供应商列表，支持分页和筛选
    """
    try:
        # 构建查询
        query = db.query(Supplier)

        # 应用筛选条件
        if name:
            query = query.filter(Supplier.name.like(f"%{name}%"))

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        suppliers = query.order_by(Supplier.id.desc()).offset(offset).limit(limit).all()

        # 转换结果
        result = []
        for supplier in suppliers:
            result.append(
                {
                    "id": supplier.id,
                    "name": supplier.name,
                    "contact_person": supplier.contact_person,
                    "phone": supplier.phone,
                    "email": supplier.email,
                    "address": supplier.address,
                    "tax_number": supplier.tax_number,
                    "bank_account": supplier.bank_account,
                    "remark": supplier.remark,
                    "create_time": supplier.create_time,
                    "update_time": supplier.update_time,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"Error getting suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail="获取供应商列表失败")


@router.post("/suppliers")
async def create_supplier(
    supplier_data: dict = Body(..., description="供应商信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建供应商
    """
    try:
        required_fields = ["name", "contact_person", "phone"]
        for field in required_fields:
            if field not in supplier_data or not supplier_data[field]:
                raise HTTPException(status_code=400, detail=f"缺少必要字段: {field}")

        # 检查名称是否已存在
        existing = (
            db.query(Supplier).filter(Supplier.name == supplier_data["name"]).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="供应商名称已存在")

        supplier = Supplier(
            name=supplier_data["name"],
            contact_person=supplier_data["contact_person"],
            phone=supplier_data["phone"],
            email=supplier_data.get("email"),
            address=supplier_data.get("address"),
            tax_number=supplier_data.get("tax_number"),
            bank_account=supplier_data.get("bank_account"),
            remark=supplier_data.get("remark"),
        )

        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        return {
            "id": supplier.id,
            "name": supplier.name,
            "contact_person": supplier.contact_person,
            "phone": supplier.phone,
            "create_time": supplier.create_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="创建供应商失败")


@router.get("/suppliers/{supplier_id}")
async def get_supplier_detail(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取供应商详情
    """
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")

        return {
            "id": supplier.id,
            "name": supplier.name,
            "contact_person": supplier.contact_person,
            "phone": supplier.phone,
            "email": supplier.email,
            "address": supplier.address,
            "tax_number": supplier.tax_number,
            "bank_account": supplier.bank_account,
            "remark": supplier.remark,
            "create_time": supplier.create_time,
            "update_time": supplier.update_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier detail: {str(e)}")
        raise HTTPException(status_code=500, detail="获取供应商详情失败")


@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    supplier_data: dict = Body(..., description="供应商信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新供应商信息
    """
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")

        # 更新字段
        if "name" in supplier_data:
            # 检查名称是否已被其他供应商使用
            existing = (
                db.query(Supplier)
                .filter(
                    Supplier.name == supplier_data["name"], Supplier.id != supplier_id
                )
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="供应商名称已存在")
            supplier.name = supplier_data["name"]

        if "contact_person" in supplier_data:
            supplier.contact_person = supplier_data["contact_person"]

        if "phone" in supplier_data:
            supplier.phone = supplier_data["phone"]

        if "email" in supplier_data:
            supplier.email = supplier_data["email"]

        if "address" in supplier_data:
            supplier.address = supplier_data["address"]

        if "tax_number" in supplier_data:
            supplier.tax_number = supplier_data["tax_number"]

        if "bank_account" in supplier_data:
            supplier.bank_account = supplier_data["bank_account"]

        if "remark" in supplier_data:
            supplier.remark = supplier_data["remark"]

        db.commit()
        db.refresh(supplier)

        return {
            "id": supplier.id,
            "name": supplier.name,
            "contact_person": supplier.contact_person,
            "phone": supplier.phone,
            "update_time": supplier.update_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="更新供应商信息失败")


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除供应商
    """
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")

        # 检查是否有关联的采购单
        purchase_count = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.supplier_id == supplier_id)
            .count()
        )
        if purchase_count > 0:
            raise HTTPException(status_code=400, detail="该供应商存在关联的采购单，无法删除")

        db.delete(supplier)
        db.commit()

        return {"message": "供应商删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="删除供应商失败")


# 采购单相关API
@router.get("/purchase/orders")
async def get_purchase_orders(
    order_number: Optional[str] = Query(None, description="订单编号"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    status: Optional[str] = Query(None, description="订单状态"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取采购单列表，支持分页和筛选
    """
    try:
        # 构建查询
        query = db.query(PurchaseOrder).join(Supplier)

        # 应用筛选条件
        if order_number:
            query = query.filter(PurchaseOrder.order_number.like(f"%{order_number}%"))

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)

        if status:
            try:
                query = query.filter(PurchaseOrder.status == PurchaseStatus(status))
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的订单状态")

        if start_date:
            query = query.filter(PurchaseOrder.create_time >= start_date)

        if end_date:
            query = query.filter(PurchaseOrder.create_time <= end_date)

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        orders = (
            query.order_by(PurchaseOrder.create_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # 转换结果
        result = []
        for order in orders:
            result.append(
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "supplier_id": order.supplier_id,
                    "supplier_name": order.supplier.name,
                    "total_amount": order.total_amount,
                    "status": order.status.value,
                    "order_date": order.order_date,
                    "expected_delivery_date": order.expected_delivery_date,
                    "actual_delivery_date": order.actual_delivery_date,
                    "remark": order.remark,
                    "create_time": order.create_time,
                    "update_time": order.update_time,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting purchase orders: {str(e)}")
        raise HTTPException(status_code=500, detail="获取采购单列表失败")


@router.post("/purchase/orders")
async def create_purchase_order(
    order_data: dict = Body(..., description="采购单信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建采购单
    """
    try:
        required_fields = ["supplier_id", "items"]
        for field in required_fields:
            if field not in order_data or not order_data[field]:
                raise HTTPException(status_code=400, detail=f"缺少必要字段: {field}")

        # 检查供应商是否存在
        supplier = (
            db.query(Supplier).filter(Supplier.id == order_data["supplier_id"]).first()
        )
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")

        # 检查items格式
        if not isinstance(order_data["items"], list) or len(order_data["items"]) == 0:
            raise HTTPException(status_code=400, detail="采购明细不能为空")

        # 生成订单编号
        order_number = (
            f"PO{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        )

        # 计算总金额
        total_amount = 0
        valid_items = []

        for item in order_data["items"]:
            if (
                "book_id" not in item
                or "quantity" not in item
                or "unit_price" not in item
            ):
                raise HTTPException(status_code=400, detail="采购明细缺少必要字段")

            # 检查书籍是否存在
            book = db.query(BookInfo).filter(BookInfo.id == item["book_id"]).first()
            if not book:
                raise HTTPException(
                    status_code=404, detail=f"书籍ID {item['book_id']} 不存在"
                )

            # 计算金额
            item_total = item["quantity"] * item["unit_price"]
            total_amount += item_total

            valid_items.append(
                {
                    "book_id": item["book_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "total_price": item_total,
                    "remark": item.get("remark"),
                }
            )

        # 处理日期时间格式
        expected_delivery_date = None
        if order_data.get("expected_delivery_date"):
            # 转换ISO格式的日期时间字符串为datetime对象
            try:
                expected_delivery_date = datetime.fromisoformat(
                    order_data.get("expected_delivery_date").replace("Z", "+00:00")
                )
            except Exception as e:
                logger.error(f"Error parsing expected_delivery_date: {str(e)}")
                raise HTTPException(status_code=400, detail="无效的预计送达日期格式")

        # 创建采购单
        purchase_order = PurchaseOrder(
            order_number=order_number,
            supplier_id=order_data["supplier_id"],
            total_amount=total_amount,
            status=PurchaseStatus.PENDING,
            expected_delivery_date=expected_delivery_date,
            remark=order_data.get("remark"),
        )

        db.add(purchase_order)
        db.flush()  # 获取order.id

        # 创建采购明细
        for item in valid_items:
            order_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                book_id=item["book_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                total_price=item["total_price"],
                remark=item["remark"],
            )
            db.add(order_item)

        db.commit()
        db.refresh(purchase_order)

        return {
            "id": purchase_order.id,
            "order_number": purchase_order.order_number,
            "supplier_id": purchase_order.supplier_id,
            "supplier_name": supplier.name,
            "total_amount": purchase_order.total_amount,
            "status": purchase_order.status.value,
            "create_time": purchase_order.create_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating purchase order: {str(e)}")
        raise HTTPException(status_code=500, detail="创建采购单失败")


@router.get("/purchase/orders/{order_id}")
async def get_purchase_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取采购单详情
    """
    try:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="采购单不存在")

        # 获取采购明细
        items = []
        for item in order.order_items:
            book = db.query(BookInfo).filter(BookInfo.id == item.book_id).first()
            items.append(
                {
                    "id": item.id,
                    "book_id": item.book_id,
                    "book_title": book.title if book else "未知书籍",
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "remark": item.remark,
                }
            )

        return {
            "id": order.id,
            "order_number": order.order_number,
            "supplier_id": order.supplier_id,
            "supplier_name": order.supplier.name,
            "total_amount": order.total_amount,
            "status": order.status.value,
            "order_date": order.order_date,
            "expected_delivery_date": order.expected_delivery_date,
            "actual_delivery_date": order.actual_delivery_date,
            "remark": order.remark,
            "items": items,
            "create_time": order.create_time,
            "update_time": order.update_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting purchase order detail: {str(e)}")
        raise HTTPException(status_code=500, detail="获取采购单详情失败")


@router.put("/purchase/orders/{order_id}/status")
async def update_purchase_order_status(
    order_id: int,
    status_data: dict = Body(..., description="订单状态数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新采购单状态
    """
    try:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="采购单不存在")

        # 获取状态值
        status = status_data.get("status")
        if not status:
            raise HTTPException(status_code=400, detail="缺少状态字段")

        # 验证状态
        try:
            new_status = PurchaseStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的订单状态")

        # 更新状态
        order.status = new_status

        # 如果状态为DELIVERED，更新实际送达时间
        if new_status == PurchaseStatus.DELIVERED:
            order.actual_delivery_date = datetime.now()

        db.commit()
        db.refresh(order)

        return {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "actual_delivery_date": order.actual_delivery_date,
            "update_time": order.update_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating purchase order status: {str(e)}")
        raise HTTPException(status_code=500, detail="更新采购单状态失败")


@router.delete("/purchase/orders/{order_id}")
async def delete_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除采购单
    """
    try:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="采购单不存在")

        # 只能删除待处理状态的订单
        if order.status != PurchaseStatus.PENDING:
            raise HTTPException(status_code=400, detail="只能删除待处理状态的采购单")

        db.delete(order)
        db.commit()

        return {"message": "采购单删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting purchase order: {str(e)}")
        raise HTTPException(status_code=500, detail="删除采购单失败")


# 书籍查询API（用于采购单选择书籍）
@router.get("/purchase/books")
async def get_books(
    title: Optional[str] = Query(None, description="书籍标题"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(100, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取书籍列表，支持分页和筛选（用于采购单选择书籍）
    """
    try:
        # 构建查询
        query = db.query(BookInfo)

        # 应用筛选条件
        if title:
            query = query.filter(BookInfo.title.like(f"%{title}%"))

        # 计算总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        books = query.order_by(BookInfo.id.desc()).offset(offset).limit(limit).all()

        # 转换结果
        result = []
        for book in books:
            result.append(
                {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "publisher": book.publisher,
                    "price": book.price,
                    "stock": book.stock,
                }
            )

        return {
            "items": result,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    except Exception as e:
        logger.error(f"Error getting books: {str(e)}")
        raise HTTPException(status_code=500, detail="获取书籍列表失败")
