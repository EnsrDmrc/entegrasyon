from pydantic import BaseModel, EmailStr
from typing import Optional, List

# --- AUTH & USERS ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str  # Kullanıcı kaydolurken dükkan adını da girecek

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class EmailVerify(BaseModel):
    email: EmailStr
    code: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class PasswordChangeWithOTP(BaseModel):
    code: str
    new_password: str

# --- TENANT ---
class TenantResponse(BaseModel):
    id: int
    name: str
    domain: Optional[str]

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    tenant_id: int
    tenant: Optional[TenantResponse] = None

    class Config:
        from_attributes = True

# --- PRODUCTS & INVENTORY ---
class InventoryResponse(BaseModel):
    id: int
    marketplace: str
    quantity: int

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    price: float
    inventories: List[InventoryResponse] = []

    class Config:
        from_attributes = True

class ProductUpdateRequest(BaseModel):
    price: Optional[float] = None
    quantity: Optional[int] = None
