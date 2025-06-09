from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.models import User, UserRole
from app.auth.schemas import UserCreate, UserResponse, Token, SignInRequest
from app.auth.utils import hash_password, verify_password, create_access_token, create_refresh_token
import logging
from typing import cast

router = APIRouter(prefix="/auth", tags=["auth"])

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="api.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user or admin based on the role provided.
    """
    logger.info(f"Signup attempt for email: {user.email}")

    # Check if email already exists
    if db.query(User).filter(User.email == user.email).first():
        logger.warning(f"Signup failed: Email {user.email} already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": True, "message": "Email already registered", "code": 400}
        )

    try:
        # Hash password
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
    """
    Authenticate user and return JWT tokens.
    """
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