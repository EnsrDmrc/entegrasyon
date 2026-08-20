from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.security import pwd_context, create_access_token
from models.user import User
from models.tenant import Tenant
from schemas import UserRegister, UserLogin, Token

router = APIRouter()

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 1. E-posta kontrolü
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kullanılıyor.")

    # 2. Önce Tenant (Mağaza) oluştur
    new_tenant = Tenant(name=user_data.tenant_name)
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)

    # 3. Sonra User oluştur ve Tenant'a bağla
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        tenant_id=new_tenant.id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 4. Token üret ve dön
    access_token = create_access_token(subject=str(new_user.id))
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalars().first()

    if not user or not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
