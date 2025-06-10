from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.products.models import Product
from app.products.schemas import ProductResponse, ProductListResponse
import logging
from typing import List, Optional

router = APIRouter(prefix="/products", tags=["products"])

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@router.get("/", response_model=ProductListResponse)
async def list_products(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, min_length=2, max_length=50),
    min_price: Optional[float] = Query(None, gt=0),
    max_price: Optional[float] = Query(None, gt=0),
    sort_by: Optional[str] = Query(None, regex="^(price|name)(:(asc|desc))?$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    List products with optional filtering, sorting, and pagination.
    """
    logger.info(
        f"List products request: category={category}, min_price={min_price}, "
        f"max_price={max_price}, sort_by={sort_by}, page={page}, page_size={page_size}"
    )

    try:
        # Build query
        query = db.query(Product)
        
        # Apply filters
        if category:
            query = query.filter(Product.category == category)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Apply sorting
        if sort_by:
            field, order = (sort_by.split(":") + ["asc"])[:2]
            if field == "price":
                query = query.order_by(Product.price.asc() if order == "asc" else Product.price.desc())
            elif field == "name":
                query = query.order_by(Product.name.asc() if order == "asc" else Product.name.desc())
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        skip = (page - 1) * page_size
        products = query.offset(skip).limit(page_size).all()

        if not products and total > 0:
            logger.warning(f"No products found for page {page} with given filters")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "No products found for the specified page",
                    "code": 404
                }
            )

        logger.info(f"Retrieved {len(products)} products, total: {total}")
        return {
            "items": products,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"List products error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.get("/search", response_model=ProductListResponse)
async def search_products(
    db: Session = Depends(get_db),
    keyword: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    Search products by keyword in name or description.
    """
    logger.info(f"Search products request: keyword={keyword}, page={page}, page_size={page_size}")

    try:
        # Build query with keyword search
        query = db.query(Product).filter(
            or_(
                Product.name.ilike(f"%{keyword}%"),
                Product.description.ilike(f"%{keyword}%")
            )
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        skip = (page - 1) * page_size
        products = query.offset(skip).limit(page_size).all()

        if not products and total > 0:
            logger.warning(f"No products found for keyword '{keyword}' on page {page}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "No products found for the specified page",
                    "code": 404
                }
            )

        logger.info(f"Retrieved {len(products)} products for keyword '{keyword}', total: {total}")
        return {
            "items": products,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        logger.error(f"Search products error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.get("/{id}", response_model=ProductResponse)
async def get_product(id: int, db: Session = Depends(get_db)):
    """
    Get product details by ID.
    """
    logger.info(f"Get product details request: product_id={id}")

    try:
        product = db.query(Product).filter(Product.id == id).first()
        if not product:
            logger.warning(f"Product not found: id {id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": True, "message": "Product not found", "code": 404}
            )
        logger.info(f"Retrieved product: id {id}, name: {product.name}")
        return product
    except Exception as e:
        logger.error(f"Get product error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )