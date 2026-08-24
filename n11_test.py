import sys

def test_n11(api_key, api_secret):
    try:
        import zeep
    except ImportError:
        print("Lütfen önce kütüphaneyi kurun: pip install zeep")
        return

    print(f"Test Başlıyor...\nAppKey: {api_key}\nAppSecret: {api_secret[:3]}...{api_secret[-3:]}\n")
    
    try:
        client = zeep.Client('https://api.n11.com/ws/ProductService.wsdl')
        auth = {'appKey': api_key.strip(), 'appSecret': api_secret.strip()}
        paging = {'currentPage': 0, 'pageSize': 1}
        
        print("N11 sunucusuna bağlanılıyor...")
        res = client.service.GetProductList(auth=auth, pagingData=paging)
        
        if res.result.status == "failure":
            print("\n[BAŞARISIZ] N11 şu hatayı döndürdü:")
            print(res.result.errorMessage)
            print("\nBunun Anlamı: N11 API şifrenizi REDDETTİ. (Ya şifre yanlış, ya da N11 sizin IP'nizi engelliyor.)")
        else:
            print("\n[BAŞARILI] Mükemmel! N11 API bağlantısı sorunsuz kuruldu.")
            print("Ürünler başarıyla çekilebiliyor.")
            
    except Exception as e:
        print(f"\n[SİSTEM HATASI] Beklenmeyen bir hata oluştu: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Kullanım: python n11_test.py <API_KEY> <API_SECRET>")
    else:
        test_n11(sys.argv[1], sys.argv[2])
