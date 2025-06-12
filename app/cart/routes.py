from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.core.database import get_db
from app.auth.models import User
from app.auth.utils import get_current_user
from .models import ShoppingCart, ShoppingCartItem
from app.products.models import Product
from .schemas import  CreateCartItem, UpdateItemInCart, CartResponse, CartItemResponse
import logging

router = APIRouter(prefix="/cart", tags=["cart"])

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#Add to Cart Route
@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    item_data: CreateCartItem,
    db_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Add Item to Cart")

    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        logger.warning(f"Product not found: {item_data.product_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Product not found", "code": 404}
        )

    if product.stock < item_data.quantity:
        logger.warning(f"Not enough stock for product {item_data.product_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": True, "message": "Insufficient Stock", "code": 400}
        )

    try:
        cart = db.query(ShoppingCart).filter(ShoppingCart.user_id == db_user.id).first()
        if not cart:
            cart = ShoppingCart(user_id=db_user.id)
            db.add(cart)
            db.commit()
            db.refresh(cart)

        cart_item = db.query(ShoppingCartItem).filter(
            ShoppingCartItem.cart_id == cart.id,
            ShoppingCartItem.product_id == item_data.product_id
        ).first()

        if cart_item:
            cart_item.quantity += item_data.quantity
            cart_item.price = product.price
        else:
            cart_item = ShoppingCartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=product.price
            )
            db.add(cart_item)

        db.commit()
        db.refresh(cart_item)

        logger.info(f"Item {item_data.product_id} added to cart for user {db_user.id}")

        return {
            "id": cart_item.id,
            "product_id": cart_item.product_id,
            "quantity": cart_item.quantity,
            "price": cart_item.price,
            "total": cart_item.quantity * cart_item.price
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error adding to cart for user ID {db_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )
    

@router.get("/", response_model=CartResponse)
async def get_cart_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Retrieving cart for user: {user.id}")
    try:
        cart = db.query(ShoppingCart).options(
            joinedload(ShoppingCart.cart_items).joinedload(ShoppingCartItem.product)
        ).filter(ShoppingCart.user_id == user.id).first()

        if not cart:
            return {"id": 0, "items": [], "total": 0.0}

        items = [
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "total": item.quantity * item.price
            }
            for item in cart.cart_items
        ]
        total = sum(item["total"] for item in items)

        logger.info(f"Cart retrieved for user: {user.id}")
        return {"id": cart.id, "items": items, "total": total}

    except Exception as e:
        logger.error(f"Get cart error for user ID: {user.id}: {str(e)}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )
    
@router.put("/{item_id}", response_model=CartItemResponse)
async def update_items_in_cart(
    item_id: int,
    item_data: UpdateItemInCart,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    logger.info(f"Updating cart item {item_id} for user ID: {user.id}")
    
    cart_item = db.query(ShoppingCartItem).join(ShoppingCart).filter(
        ShoppingCartItem.id == item_id,
        ShoppingCart.user_id == user.id
    ).first()

    if not cart_item:
        logger.warning(f"Cart item not found: {item_id} for user ID: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Cart item not found", "code": 404}
        )

    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    
    if product.stock < item_data.quantity:
        logger.warning(f"Insufficient stock for product {cart_item.product_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": True, "message": "Insufficient stock", "code": 400}
        )

    try:
        cart_item.quantity = item_data.quantity
        db.commit()
        db.refresh(cart_item)

        logger.info(f"Cart item {item_id} updated for user ID: {user.id}")
        return {
            "id": cart_item.id,
            "product_id": cart_item.product_id,
            "quantity": cart_item.quantity,
            "price": cart_item.price,
            "total": cart_item.quantity * cart_item.price
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Update cart item error for item {item_id}, user ID: {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_item_from_cart(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logger.info(f"Attempt to delete cart item {item_id} for user ID: {user.id}")

    cart_item = db.query(ShoppingCartItem).join(ShoppingCart).filter(
        ShoppingCartItem.id == item_id,
        ShoppingCart.user_id == user.id
    ).first()

    if not cart_item:
        logger.warning(f"Cart item not found: {item_id} for user ID: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Cart item not found", "code": 404}
        )

    try:
        db.delete(cart_item)
        db.commit()
        logger.info(f"Cart item {item_id} deleted for user ID: {user.id}")
        return {
            "error": False,
            "message": "Cart item removed successfully",
            "code": 200
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Delete cart item error for {item_id}, user ID: {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.delete("/", status_code=status.HTTP_200_OK)
async def empty_cart(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Attempting to clear cart for user ID: {user.id}")
    try:
        cart = db.query(ShoppingCart).filter(ShoppingCart.user_id == user.id).first()
        if not cart:
            logger.info(f"No cart found for user ID: {user.id}")
            return {"error": False, "message": "Cart is already empty", "code": 200}

        db.query(ShoppingCartItem).filter(ShoppingCartItem.cart_id == cart.id).delete()
        db.commit()

        logger.info(f"Cart cleared for user ID: {user.id}")
        return {"error": False, "message": "Cart cleared successfully", "code": 200}

    except Exception as e:
        db.rollback()
        logger.error(f"Clear cart error for user ID: {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )
