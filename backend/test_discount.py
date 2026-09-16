def test_discount_logic():
    # User's scenario
    db_base_price = 1350.0
    scraper_display_price = 1228.50
    second_cheapest_price = 1301.38
    
    # Calculate hidden discount
    if scraper_display_price < db_base_price:
        discount_rate = 1 - (scraper_display_price / db_base_price)
        print(f"Gizli N11 İndirimi Oranı: %{discount_rate*100:.2f}")
    else:
        discount_rate = 0.0
        print("İndirim yok.")
        
    # Target price to beat the second cheapest by 10 TL
    target_display_price = second_cheapest_price - 10.0
    print(f"Hedef Sepet Fiyatı: {target_display_price}")
    
    # Calculate the NEW base price we need to send to N11 API
    if discount_rate > 0:
        new_base_price = target_display_price / (1 - discount_rate)
        print(f"N11 API'ye Gönderilecek Yeni İndirimsiz Fiyat (Base Price): {new_base_price:.2f}")
    else:
        new_base_price = target_display_price
        print(f"N11 API'ye Gönderilecek Yeni İndirimsiz Fiyat: {new_base_price:.2f}")
        
    # Verify: If we send new_base_price, what will the customer see?
    customer_sees = new_base_price * (1 - discount_rate)
    print(f"Müşterinin Göreceği Yeni Fiyat: {customer_sees:.2f} (Beklenen: {target_display_price:.2f})")

if __name__ == "__main__":
    test_discount_logic()
