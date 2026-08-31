import urllib.request
import urllib.parse
import json

import sqlite3

def main():
    # Connect to local SQLite DB if it exists, or we can just hardcode credentials if I have them?
    # I don't have them hardcoded. Let's read from the DB.
    # The app uses PostgreSQL in production, but local testing uses what? The user's DB URL is in backend/.env
    import os
    from dotenv import load_dotenv
    load_dotenv('backend/.env')
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
        
    print("Connecting to:", db_url)
    
    import psycopg2
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT api_key, api_secret, store_url FROM marketplace_integrations WHERE marketplace_name = 'pazarama' AND is_active = true LIMIT 1")
        row = cur.fetchone()
        if not row:
            print("Pazarama entegrasyonu bulunamadı.")
            return
        api_key, api_secret, merchant_id = row
        print(f"Merchant ID: {merchant_id}, API Key: {api_key}")
    except Exception as e:
        print("DB Hatası:", e)
        return
        
    # 1. Get Token
    token_url = "https://isortagimgiris.pazarama.com/connect/token"
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": "merchantgatewayapi.fullaccess"
    }).encode("utf-8")
    
    req = urllib.request.Request(token_url, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "client_id": api_key,
        "client_secret": api_secret
    })
    
    try:
        with urllib.request.urlopen(req) as response:
            resp_data = json.loads(response.read().decode())
            token = resp_data.get("data", {}).get("accessToken") or resp_data.get("access_token")
            print("Token alındı.")
    except Exception as e:
        print("Token alınamadı:", e)
        if hasattr(e, 'read'):
            print(e.read().decode())
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    endpoints = [
        "/Category",
        "/category",
        "/api/Category",
        "/api/v1/Category",
        "/categories",
        "/api/categories",
        "/Category/get-categories"
    ]
    
    for ep in endpoints:
        url = f"https://isortagimapi.pazarama.com{ep}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                print(f"GET {ep} -> {response.status}")
                if response.status == 200:
                    print("Başarılı:", response.read().decode()[:200])
        except urllib.error.HTTPError as e:
            print(f"GET {ep} -> {e.code}")
        except Exception as e:
            print(f"GET {ep} -> Error: {e}")

if __name__ == "__main__":
    main()
