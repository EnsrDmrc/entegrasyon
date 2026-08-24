import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

def _send_email_sync(to_email: str, subject: str, body_html: str):
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("="*50)
        print(f"MOCK EMAIL (SMTP Ayarları Yok)")
        print(f"Alıcı: {to_email}")
        print(f"Konu: {subject}")
        print(f"İçerik: \n{body_html}")
        print("="*50)
        return

    msg = MIMEMultipart()
    msg['From'] = f"Entegrasyon Sistemi <{settings.SMTP_USER}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body_html, 'html'))

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email başarıyla gönderildi: {to_email}")
    except Exception as e:
        print(f"E-Posta gönderme hatası: {e}")

async def send_verification_email(to_email: str, code: str):
    subject = "Entegrasyon Kayıt Doğrulama Kodu"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Hesabınızı Doğrulayın</h2>
        <p>Entegrasyon sistemine kayıt olduğunuz için teşekkürler. Hesabınızı aktifleştirmek için aşağıdaki doğrulama kodunu kullanın:</p>
        <div style="background-color: #f4f4f4; padding: 15px; font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 5px; margin: 20px 0;">
            {code}
        </div>
        <p>Bu kod 10 dakika boyunca geçerlidir.</p>
    </body>
    </html>
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _send_email_sync, to_email, subject, body)

async def send_password_reset_email(to_email: str, code: str):
    subject = "Şifre Sıfırlama Kodu"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Şifre Sıfırlama</h2>
        <p>Şifrenizi sıfırlamak için aşağıdaki doğrulama kodunu kullanın:</p>
        <div style="background-color: #f4f4f4; padding: 15px; font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 5px; margin: 20px 0;">
            {code}
        </div>
        <p>Bu kod 10 dakika boyunca geçerlidir.</p>
        <p>Eğer bu işlemi siz yapmadıysanız lütfen bu e-postayı dikkate almayın.</p>
    </body>
    </html>
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _send_email_sync, to_email, subject, body)

async def send_password_change_email(to_email: str, code: str):
    subject = "Şifre Değiştirme Doğrulama Kodu"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Şifre Değişikliği Talebi</h2>
        <p>Hesap ayarlarınızdan şifre değişikliği talep ettiniz. İşlemi onaylamak için aşağıdaki kodu girin:</p>
        <div style="background-color: #f4f4f4; padding: 15px; font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 5px; margin: 20px 0;">
            {code}
        </div>
        <p>Bu kod 10 dakika boyunca geçerlidir.</p>
    </body>
    </html>
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _send_email_sync, to_email, subject, body)
