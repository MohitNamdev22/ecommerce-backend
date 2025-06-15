from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
import logging
from typing import Any, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.models import User, UserRole
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

bearer_scheme = HTTPBearer(description="JWT Bearer token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str, credentials_exception: HTTPException) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not isinstance(email, str):
            logger.warning("Invalid token: missing or non-string 'sub' field")
            raise credentials_exception
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise credentials_exception
    
def get_current_user(credentials: str = Depends(bearer_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": True, "message": "Invalid token", "code": 401},
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    payload = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise credentials_exception
    return user

def admin_only(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": True, "message": "Admin access required", "code": 403}
        )
    return current_user

def reset_token_generation() -> str:
    return str(uuid.uuid4())

def send_reset_password_email(to: str, reset_token: str) -> None:
    mail = MIMEMultipart()
    mail['From'] = settings.FROM_EMAIL
    mail['To'] = to
    mail['Subject'] = "Request for Password Reset"


    mail_body = f"""
    Hey there,
    Here is the Token to reset your password:
    {reset_token}
    """

    mail.attach(MIMEText(mail_body, 'plain'))

    try:
        server = smtplib.SMTP('smtp-relay.brevo.com', 587)
        server.starttls()
        server.login(settings.BREVO_SMTP_LOGIN, settings.BREVO_API_KEY)
        server.sendmail(settings.FROM_EMAIL, to, mail.as_string())
        server.quit()
        logger.info("Passwort reset email has been sent to", to)
    except Exception as e:
        logger.error(f"Failed to send reset email to {to}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error":True, "message":"Failed to Send Email", "code":500}
        )


