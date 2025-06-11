from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    reset_tokens = relationship("ResetPassToken", back_populates="user")


class ResetPassToken(Base):
    __tablename__ = "reset_password_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reset_token = Column(String(255), unique=True, nullable=False)
    expiry_period = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    user = relationship("User",back_populates="reset_tokens")



