from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.database import Base, engine
from app.auth.routes import router as auth_router
from app.products.routes import router as products_router
from app.products.public_routes import router as public_products_router
from app.cart.routes import router as cart_router
from app.orders.routes import router as orders_routers
from fastapi import status
import logging
from app.middleware.logging import LoggingMiddleware

app = FastAPI(title="E-commerce Backend API", version="1.0.0")

# Configure logging
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app.add_middleware(LoggingMiddleware)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logger = logging.getLogger(__name__)
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Invalid input data",
            "code": 422,
            "details": exc.errors()
        }
    )

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(public_products_router)
app.include_router(cart_router)
app.include_router(orders_routers)