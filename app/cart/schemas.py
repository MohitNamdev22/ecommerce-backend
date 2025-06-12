from pydantic import BaseModel, field_validator
from typing import List

class CreateCartItem(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_check(cls, v:int) -> int:
        if v<=0:
            raise ValueError("Qty should be more than zero")
        return v
    
class UpdateItemInCart(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_check(cls, v:int) -> int:
        if v<=0:
            raise ValueError("Qty should be more than zero")
        return v

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    total: float

    class Config:
        from_attributes = True
    
class CartResponse(BaseModel):
    id: int
    items: List[CartItemResponse]
    total: float

    class Config:
        from_attribute = True

