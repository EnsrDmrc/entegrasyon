import xml.etree.ElementTree as ET

xml_data = """<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Header/><SOAP-ENV:Body><ns3:GetProductListResponse xmlns:ns3="http://www.n11.com/ws/schemas"><result><status>failure</status><errorCode>SELLER_API.authenticationFailed</errorCode><errorMessage>Apide dogrulama islemi basarisiz oldu.</errorMessage><errorCategory>SELLER_API</errorCategory></result><products/></ns3:GetProductListResponse></SOAP-ENV:Body></SOAP-ENV:Envelope>"""

root = ET.fromstring(xml_data)
namespaces = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/', 'n11': 'http://www.n11.com/ws/schemas'}

print("n11:result/n11:status =", root.find(".//n11:result/n11:status", namespaces))
print("result/status =", root.find(".//result/status", namespaces))
status_elem = root.find(".//result/status", namespaces)
if status_elem is not None:
    print("Found status:", status_elem.text)
    
err_msg = root.find(".//result/errorMessage", namespaces)
if err_msg is not None:
    print("Found error:", err_msg.text)
