import asyncio
from services.n11_scraper import N11Scraper

def main():
    url = "https://www.n11.com/urun/yildiz-iki-agiz-anahtar-14x15-130617729?magaza=saygingrup"
    scraper = N11Scraper()
    competitors = scraper.get_competitors(url)
    
    print("Scraped Competitors:")
    for idx, c in enumerate(competitors):
        print(f"{idx+1}. Seller: {c['seller_name']} - Price: {c['price']} - Discount: {c['discount_rate']}%")
        
    if not competitors:
        print("No competitors found!")
        return

    cheapest = competitors[0]
    
    tenant_name = "saygıngrup"
    cheapest_name = cheapest["seller_name"].lower().replace(' ', '')
    
    if tenant_name in cheapest_name or cheapest_name in tenant_name:
        print("\n=> Biz en ucuzuz!")
        if len(competitors) > 1:
            second = competitors[1]
            diff = second["price"] - cheapest["price"]
            print(f"=> 2. ile aramızdaki fark: {diff} TL")
            if diff > 10:
                new_price = second["price"] - 10
                print(f"=> Hedef Fiyat: {new_price} TL (Fark 10 TL'den büyük, fiyat güncellenecek!)")
                if cheapest["discount_rate"] > 0:
                    base = new_price / (1 - (cheapest["discount_rate"] / 100))
                    print(f"=> N11 İndirimi var, API'ye gönderilecek baz fiyat: {base} TL")
            else:
                print("=> Fark 10 TL'den az veya eşit, dokunulmayacak.")
        else:
            print("=> Tek satıcıyız, dokunulmayacak.")
    else:
        print(f"\n=> En ucuz biz değiliz (En ucuz: {cheapest['seller_name']}). Dokunulmayacak.")

if __name__ == "__main__":
    main()
