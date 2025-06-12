from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.auth.models import User
from app.auth.utils import get_current_user
from app.cart.models import ShoppingCart, ShoppingCartItem
from app.products.models import Product
from app.orders.models import Order, OrderItem, OrderStatus
from app.orders.schemas import OrderInfo, OrderSummary
import logging

router = APIRouter(prefix="/orders", tags=["orders"])

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#endpoint for checking out
@router.post("/checkout", response_model=OrderInfo, status_code=status.HTTP_201_CREATED)
async def checkout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"{user.id} has attempted to checkout")
    shopping_cart = db.query(ShoppingCart).options(joinedload(ShoppingCart.cart_items).joinedload(ShoppingCartItem.product)).filter(ShoppingCart.user_id == user.id).first()

    if not shopping_cart or not shopping_cart.cart_items:
        logger.warning(f"The Cart is Empty")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error":True, "message":"Empty Cart", "code":422}
        )
    
    try:
        for item in shopping_cart.cart_items:
            if item.product.stock < item.quantity:
                logger.warning(f"Insufficient stock for the product {item.product_id}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"error":True, "message":f"Insufficient stock for {item.product.name}", "code":422}
                )
        total_sum = sum(item.quantity * item.price for item in shopping_cart.cart_items)
        order = Order(
            user_id=user.id,
            total = total_sum,
            status=OrderStatus.PENDING
        )
        db.add(order)
        db.flush()

        for item in shopping_cart.cart_items:
            order_item = OrderItem(
                order_id = order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
            db.add(order_item)
            item.product.stock -= item.quantity
        
        db.query(ShoppingCartItem).filter(ShoppingCartItem.cart_id == shopping_cart.id).delete()
        db.commit()

        db.refresh(order)
        order = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(Order.id == order.id).first()

        items_info = [
            {
                "id":item.id,
                "product_id":item.product_id,
                "product_name":item.product.name,
                "quantity": item.quantity,
                "price":item.price,
                "total": item.quantity * item.price
            }
            for item in order.items
        ]
        logger.info(f"Order created for user ID: {user.id}, order ID: {order.id}")
        return {
            "id": order.id,
            "total": order.total,
            "status": order.status,
            "created_at": order.created_at,
            "items": items_info
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in Checking out")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = {"error":True, "message":"Error in checking out", "code":500}
        )

#Endpoint for Fetching Order information
@router.get("/", response_model=List[OrderSummary])
async def get_orders_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching Orders")

    try:
        orders = db.query(Order).filter(Order.user_id == user.id).all()
        return [
            {
                "id":order.id,
                "total":order.total,
                "status": order.status,
                "created_at": order.created_at

            }

            for order in orders
        ]
    except Exception as e:
        logger.error(f"Error in fetching orders for user ID: {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Failed to fetch orders", "code": 500}
        )
    

#Endpoint for fetching particular order
@router.get("/{order_id}", response_model=OrderInfo)
async def get_order_info(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching order {order_id} for user ID: {user.id}")
    order = db.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
        Order.id == order_id,
        Order.user_id == user.id
    ).first()

    if not order:
        logger.warning(f"Order {order_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Order not found", "code":404}
        )
    try:
        items_info = [
             {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price": item.price,
                "total": item.quantity * item.price
            }
            for item in order.items
        ]
        logger.info(f"Order {order_id} fetched for User: {user.id}")
        return{
            "id": order.id,
            "total": order.total,
            "status": order.status,
            "created_at": order.created_at,
            "items": items_info
        }
    except Exception as e:
        logger.error(f"Get order error for order {order_id}, user ID: {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Failed to Fetch Order", "code": 500}
        )