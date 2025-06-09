from fastapi import FastAPI
from app.core.database import Base, engine
from app.auth.routes import router as auth_router
import logging
from app.middleware.logging import LoggingMiddleware

app = FastAPI(title="E-commerce Backend API", version="1.0.0")

# Configure logging
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create database tables
Base.metadata.create_all(bind=engine)
app.add_middleware(LoggingMiddleware)
# Include routers
app.include_router(auth_router)
