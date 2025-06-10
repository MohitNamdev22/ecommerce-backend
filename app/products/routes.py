from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.products.models import Product
from app.products.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.auth.utils import admin_only
from app.auth.models import User
from typing import List
import logging

router = APIRouter(prefix="/admin/products", tags=["admin-products"])

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    """
    Create a new product (admin-only).
    """
    logger.info(f"Create product attempt by admin: {current_user.email}, product: {product.name}")
    if db.query(Product).filter(Product.name == product.name).first():
        logger.warning(f"Product creation failed: {product.name} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": True, "message": "Product with this name already exists", "code": 409}
        )
    
    try:
        db_product = Product(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Product created successfully: {db_product.name}")
        return db_product
    except Exception as e:
        db.rollback()
        logger.error(f"Create product error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    List products with pagination (admin-only).
    """
    logger.info(f"Get products list by admin: {current_user.email}, page: {page}, page_size: {page_size}")
    
    try:
        skip = (page - 1) * page_size
        products = db.query(Product).offset(skip).limit(page_size).all()
        return products
    except Exception as e:
        logger.error(f"Get products error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.get("/{id}", response_model=ProductResponse)
async def get_product(id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    """
    Get product details by ID (admin-only).
    """
    logger.info(f"Get product details by admin: {current_user.email}, product_id: {id}")
    
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        logger.warning(f"Product not found: id {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Product not found", "code": 404}
        )
    return product

@router.put("/{id}", response_model=ProductResponse)
async def update_product(id: int, product: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    """
    Update a product by ID (admin-only).
    """
    logger.info(f"Update product attempt by admin: {current_user.email}, product_id: {id}")
    
    db_product = db.query(Product).filter(Product.id == id).first()
    if not db_product:
        logger.warning(f"Product not found: id {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Product not found", "code": 404}
        )
    
    try:
        if product.name and product.name != db_product.name:
            if db.query(Product).filter(Product.name == product.name).first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": True, "message": "Product with this name already exists", "code": 409}
                )
            
        update_data = product.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Product updated successfully: id {id}")
        return db_product
    except Exception as e:
        db.rollback()
        logger.error(f"Update product error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.delete("/{id}", response_model=dict)
async def delete_product(id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_only)):
    """
    Delete a product by ID (admin-only).
    """
    logger.info(f"Delete product attempt by admin: {current_user.email}, product_id: {id}")
    
    db_product = db.query(Product).filter(Product.id == id).first()
    if not db_product:
        logger.warning(f"Product not found: id {id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Product not found", "code": 404}
        )
    
    try:
        product_info = {
            "id": db_product.id,
            "name": db_product.name,
            "category": db_product.category
        }
        db.delete(db_product)
        db.commit()
        logger.info(f"Product deleted successfully: id {id}")
        return {
            "error": False,
            "message": f"Product '{product_info['name']}' has been successfully deleted",
            "code": 200,
            "data": product_info
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Delete product error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )