from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    
    
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=2, max_length=100)
    stock: int = Field(..., ge=0)
    image: str | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    category: str
    stock: int
    image: str | None

    class Config:
        from_attributes = True
        
class CartCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    product_name: str
    price: float
    total_price: float 
    
class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    payment_status: str

    class Config:
        from_attributes = True       
    