from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone
import random
import string

from core.database import get_db
from core.security import pwd_context, create_access_token, create_refresh_token
from api.deps import get_current_user
from models.user import User
from models.tenant import Tenant
from schemas.schemas import (
    UserRegister, UserLogin, Token, TokenRefresh,
    EmailVerify, ForgotPassword, ResetPassword, PasswordChangeWithOTP
)
from core.email import send_verification_email, send_password_reset_email, send_password_change_email

router = APIRouter()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@router.post("/register")
async def register(user_data: UserRegister, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kullanılıyor.")
        else:
            # Kullanıcı var ama doğrulanmamışsa kodu tekrar gönder
            otp = generate_otp()
            existing_user.otp_code = otp
            existing_user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            await db.commit()
            background_tasks.add_task(send_verification_email, existing_user.email, otp)
            return {"status": "verification_required", "email": existing_user.email, "message": "Doğrulama kodu tekrar gönderildi."}

    # Yeni mağaza oluştur
    new_tenant = Tenant(name=user_data.tenant_name)
    db.add(new_tenant)
    await db.commit()
    await db.refresh(new_tenant)

    # Yeni kullanıcı oluştur
    hashed_password = pwd_context.hash(user_data.password)
    otp = generate_otp()
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        tenant_id=new_tenant.id,
        is_verified=False,
        otp_code=otp,
        otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    db.add(new_user)
    await db.commit()
    
    # E-posta gönder (arka planda çalışacak)
    background_tasks.add_task(send_verification_email, new_user.email, otp)
    
    # Token DÖNMÜYORUZ, doğrulama istiyoruz
    return {"status": "verification_required", "email": new_user.email}


@router.post("/verify-email", response_model=Token)
async def verify_email(data: EmailVerify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Kullanıcı zaten doğrulanmış.")
        
    if not user.otp_code or user.otp_code != data.code:
        raise HTTPException(status_code=400, detail="Geçersiz doğrulama kodu.")
        
    # UTC naive vs aware check
    now = datetime.now(timezone.utc)
    if user.otp_expires_at.tzinfo is None:
        now = datetime.utcnow() # fallback to naive
        
    if user.otp_expires_at < now:
        raise HTTPException(status_code=400, detail="Doğrulama kodunun süresi dolmuş.")
        
    # Doğrulama başarılı
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    await db.commit()
    
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/login")
async def login(user_data: UserLogin, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalars().first()

    if not user or not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_verified:
        # Doğrulanmamışsa kodu tekrar gönder ve özel hata dön
        otp = generate_otp()
        user.otp_code = otp
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        await db.commit()
        background_tasks.add_task(send_verification_email, user.email, otp)
        
        raise HTTPException(
            status_code=403, 
            detail="Lütfen e-posta adresinizi doğrulayın. Yeni bir kod gönderildi."
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

from jose import jwt, JWTError
from core.config import settings

@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(data.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Geçersiz refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Geçersiz refresh token")
        
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
        
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()
    
    if user:
        otp = generate_otp()
        user.otp_code = otp
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        await db.commit()
        background_tasks.add_task(send_password_reset_email, user.email, otp)
        
    return {"message": "Eğer hesabınız varsa şifre sıfırlama kodu gönderildi."}


@router.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()
    
    if not user or not user.otp_code or user.otp_code != data.code:
        raise HTTPException(status_code=400, detail="Geçersiz e-posta veya kod.")
        
    now = datetime.now(timezone.utc)
    if user.otp_expires_at.tzinfo is None:
        now = datetime.utcnow()
        
    if user.otp_expires_at < now:
        raise HTTPException(status_code=400, detail="Kodun süresi dolmuş.")
        
    # Şifreyi güncelle
    user.hashed_password = pwd_context.hash(data.new_password)
    user.otp_code = None
    user.otp_expires_at = None
    await db.commit()
    
    return {"message": "Şifreniz başarıyla sıfırlandı."}


@router.post("/request-password-change")
async def request_password_change(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    otp = generate_otp()
    current_user.otp_code = otp
    current_user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db.commit()
    background_tasks.add_task(send_password_change_email, current_user.email, otp)
    
    return {"message": "Şifre değiştirme kodu e-posta adresinize gönderildi."}


@router.post("/change-password")
async def change_password(data: PasswordChangeWithOTP, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.otp_code or current_user.otp_code != data.code:
        raise HTTPException(status_code=400, detail="Geçersiz doğrulama kodu.")
        
    now = datetime.now(timezone.utc)
    if current_user.otp_expires_at.tzinfo is None:
        now = datetime.utcnow()
        
    if current_user.otp_expires_at < now:
        raise HTTPException(status_code=400, detail="Kodun süresi dolmuş.")
        
    current_user.hashed_password = pwd_context.hash(data.new_password)
    current_user.otp_code = None
    current_user.otp_expires_at = None
    await db.commit()
    
    return {"message": "Şifreniz başarıyla güncellendi."}
