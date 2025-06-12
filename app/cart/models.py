from sqlalchemy import Column,Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class ShoppingCart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    user = relationship("User", back_populates="cart")
    cart_items = relationship("ShoppingCartItem", back_populates="cart", cascade="all, delete-orphan")

class ShoppingCartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    cart = relationship("ShoppingCart", back_populates="cart_items")
    product = relationship("Product")
