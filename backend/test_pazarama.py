import asyncio
from fastapi.testclient import TestClient
from main import app
from api.deps import get_current_user, get_db
from models.user import User
from models.integration import MarketplaceIntegration

mock_user = User(id=1, tenant_id=1, email="test@test.com", is_active=True)
app.dependency_overrides[get_current_user] = lambda: mock_user

class MockResult:
    def scalars(self):
        return self
    def first(self):
        return MarketplaceIntegration(tenant_id=1, marketplace_name="pazarama", is_active=True, store_url="merchant_id_123", api_key="api_key_123")

class MockAsyncSession:
    async def execute(self, *args, **kwargs):
        return MockResult()
    async def commit(self):
        pass
    def add(self, obj):
        pass

async def mock_get_db():
    yield MockAsyncSession()

app.dependency_overrides[get_db] = mock_get_db

client = TestClient(app)

def test_sync():
    print("Testing /api/v1/integrations/sync/pazarama")
    try:
        response = client.post("/api/v1/integrations/sync/pazarama", headers={"Authorization": "Bearer fake"})
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
    except Exception as e:
        print("EXCEPTION:", e)

test_sync()
