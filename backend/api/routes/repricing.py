from fastapi import APIRouter, BackgroundTasks
from core.database import AsyncSessionLocal
from sqlalchemy.future import select
from models.user import User
from models.tenant import Tenant
from fastapi import Depends, HTTPException
from api.deps import get_current_user

router = APIRouter()

@router.post("/n11/trigger")
async def trigger_n11_repricing(background_tasks: BackgroundTasks):
    """
    Sisteme kaydedilmiş olan N11 ürünlerinin rakip fiyatlarını analiz edip,
    kârı maksimize edecek şekilde fiyatları güncelleyen 'Repricing' algoritmasını manuel tetikler.
    (Normalde bu işlem her gece 03:00'da otomatik çalışır.)
    """
    from services.repricing import run_n11_repricing
    
    # Sadece yetkili kullanıcıların veya test için adminin tetikleyebilmesi için (Şimdilik izin veriyoruz)
    background_tasks.add_task(run_n11_repricing)
    
    return {
        "message": "N11 Otomatik Fiyatlandırma (Repricing) arka planda başlatıldı. Terminal loglarından süreci takip edebilirsiniz."
    }
