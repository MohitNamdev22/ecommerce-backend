from fastapi import FastAPI
from app.core.database import Base, engine
from app.auth.routes import router as auth_router
from app.products.routes import router as products_router
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

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router)
app.include_router(products_router)