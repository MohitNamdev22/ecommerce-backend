from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set to INFO to capture all INFO logs and above


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Request: {request.method} {request.url} from {client_host}"
        )
        try:
            response = await call_next(request)
            logger.info(
                f"Response: {request.method} {request.url} status {response.status_code}"
            )
            return response
        except Exception as e:
            logger.error(f"Error: {request.method} {request.url} - {str(e)}")
            raise

