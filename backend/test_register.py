import urllib.request
import json
import urllib.error

data = json.dumps({
    "tenant_name": "Test Magaza",
    "email": "test2@test.com",
    "password": "123"
}).encode('utf-8')

req = urllib.request.Request('http://localhost:8001/api/v1/auth/register', data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as response:
        print(response.getcode())
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode('utf-8'))
