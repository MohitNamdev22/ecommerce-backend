from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)
    image_url = Column(String(255), nullable=True)
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    admin = relationship("User")
