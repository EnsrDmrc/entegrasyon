import asyncio
import httpx
import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import engine, AsyncSessionLocal
from models.integration import MarketplaceIntegration

def test_xml(api_key, api_secret, xml_body, name):
    print(f"\n--- Testing format: {name} ---")
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    res = httpx.post("https://api.n11.com/ws/ProductService.wsdl", content=xml_body, headers=headers)
    print("Status:", res.status_code)
    try:
        fault_root = ET.fromstring(res.text)
        fault_elem = fault_root.find(".//faultstring")
        if fault_elem is not None:
            print("Fault:", fault_elem.text)
        else:
            print("Full response:", res.text)
    except Exception as e:
        print("Raw response:", res.text)

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MarketplaceIntegration).where(MarketplaceIntegration.marketplace_name == "n11"))
        integration = result.scalars().first()
        if not integration or not integration.api_key:
            print("N11 integration not found in DB.")
            return

        api_key = integration.api_key
        api_secret = integration.api_secret

        # Variation 1: auth and children NO PREFIX
        v1 = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
           <soapenv:Header/>
           <soapenv:Body>
              <sch:GetProductListRequest>
                 <auth>
                    <appKey>{api_key}</appKey>
                    <appSecret>{api_secret}</appSecret>
                 </auth>
                 <pagingData>
                    <currentPage>0</currentPage>
                    <pageSize>10</pageSize>
                 </pagingData>
              </sch:GetProductListRequest>
           </soapenv:Body>
        </soapenv:Envelope>"""

        # Variation 2: auth WITH PREFIX, children NO PREFIX
        v2 = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
           <soapenv:Header/>
           <soapenv:Body>
              <sch:GetProductListRequest>
                 <sch:auth>
                    <appKey>{api_key}</appKey>
                    <appSecret>{api_secret}</appSecret>
                 </sch:auth>
                 <pagingData>
                    <currentPage>0</currentPage>
                    <pageSize>10</pageSize>
                 </pagingData>
              </sch:GetProductListRequest>
           </soapenv:Body>
        </soapenv:Envelope>"""

        # Variation 3: All WITH PREFIX
        v3 = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
           <soapenv:Header/>
           <soapenv:Body>
              <sch:GetProductListRequest>
                 <sch:auth>
                    <sch:appKey>{api_key}</sch:appKey>
                    <sch:appSecret>{api_secret}</sch:appSecret>
                 </sch:auth>
                 <pagingData>
                    <sch:currentPage>0</sch:currentPage>
                    <sch:pageSize>10</sch:pageSize>
                 </pagingData>
              </sch:GetProductListRequest>
           </soapenv:Body>
        </soapenv:Envelope>"""

        # Variation 4: Auth in header?
        v4 = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:sch="http://www.n11.com/ws/schemas">
           <soapenv:Header/>
           <soapenv:Body>
              <sch:GetProductListRequest>
                 <auth>
                    <appKey>{api_key}</appKey>
                    <appSecret>{api_secret}</appSecret>
                 </auth>
                 <pagingData>
                    <currentPage>0</currentPage>
                    <pageSize>10</pageSize>
                 </pagingData>
              </sch:GetProductListRequest>
           </soapenv:Body>
        </soapenv:Envelope>"""

        test_xml(api_key, api_secret, v1, "NO PREFIX")
        test_xml(api_key, api_secret, v2, "AUTH PREFIX ONLY")
        test_xml(api_key, api_secret, v3, "ALL PREFIX")

if __name__ == "__main__":
    asyncio.run(main())
