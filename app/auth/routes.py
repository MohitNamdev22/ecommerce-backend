from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.models import ResetPassToken, User, UserRole
from app.auth.schemas import UserCreate, UserResponse, Token, SignInRequest, ForgotPassword, ResetPassword
from app.auth.utils import hash_password, reset_token_generation, send_reset_password_email, verify_password, create_access_token, create_refresh_token
import logging
from typing import cast

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Signup attempt for email: {user.email}")

    # Check if email already exists
    if db.query(User).filter(User.email == user.email).first():
        logger.warning(f"Signup failed: Email {user.email} already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": True, "message": "Email already registered", "code": 400}
        )

    try:
        hashed_password = hash_password(user.password)

        # Create user with role (admin if specified, else user)
        db_user = User(
            name=user.name,
            email=user.email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN if user.role == "admin" else UserRole.USER
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"User created successfully: {user.email}, role: {db_user.role}")
        return db_user

    except Exception as e:
        db.rollback()
        logger.error(f"Signup error for {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )

@router.post("/signin", response_model=Token)
async def signin(request: SignInRequest, db: Session = Depends(get_db)):
    logger.info(f"Signin attempt for email: {request.email}")

    # Fetch user
    user = cast(User, db.query(User).filter(User.email == request.email).first())
    if not user:
        logger.warning(f"Signin failed: Email {request.email} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": True, "message": "Invalid email or password", "code": 401}
        )

    # Verify password
    if not verify_password(request.password, str(user.hashed_password)):
        logger.warning(f"Signin failed: Invalid password for {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": True, "message": "Invalid email or password", "code": 401}
        )

    try:
        # Generate tokens
        access_token = create_access_token({"sub": user.email, "role": user.role.value})
        refresh_token = create_refresh_token({"sub": user.email, "role": user.role.value})

        logger.info(f"Signin successful for {request.email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        logger.error(f"Signin error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )
    
#Endpoint for Forgot-password
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPassword, db: Session = Depends(get_db)):
    logger.info("Forgot Password for the email", request.email)
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.warning(f"Forgot password failed: Email {request.email} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": True, "message": "Email not found", "code": 404}
        )
    try:
        reset_token_str = reset_token_generation()
        expiry_period = datetime.utcnow() + timedelta(hours=1)
        reset_token = ResetPassToken(
            user_id = user.id,
            reset_token = reset_token_str,
            expiry_period=expiry_period,
            is_used=False
        )
        db.add(reset_token)
        db.commit()

        send_reset_password_email(user.email, reset_token_str)

        logger.info(f"Password reset token generated for user ID: {user.id}")
        return {"error": False, "message": "Password reset email sent successfully", "code": 200}
    except Exception as e:
        db.rollback()
        logger.error(f"Forgot password error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )
    
#endpoint for reset password
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    logger.info("Password Reset Request")
    reset_token = db.query(ResetPassToken).filter(ResetPassToken.reset_token == request.reset_token).first()

    if not reset_token:
        logger.warning(f"Invalid or expired token: {request.reset_token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": True, "message": "Invalid or expired token", "code": 400}
        )
    if reset_token.is_used:
        logger.warning(f"Token already used: {request.reset_token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": True, "message": "Token has already been used", "code": 400}
        )
    if reset_token.expiry_period < datetime.utcnow():
        logger.warning(f"Token expired: {request.reset_token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": True, "message": "Token has expired", "code": 400}
        )
    try:
        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            logger.error(f"User not found for token: {request.reset_token[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": True, "message": "User not found", "code": 404}
            )
        # Update password
        user.hashed_password = hash_password(request.new_password)
        reset_token.is_used = True
        db.commit()

        logger.info(f"Password reset successful for user ID: {user.id}")
        return {"error": False, "message": "Password updated successfully", "code": 200}
    except Exception as e:
        db.rollback()
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": True, "message": "Internal server error", "code": 500}
        )