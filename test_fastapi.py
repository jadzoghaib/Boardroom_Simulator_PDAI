from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)
response = client.post('/api/boardroom_turn', json={'thread_id':'test1','budget':0,'burn_rate':0,'revenue':0,'founder_experience':0,'sector':'string','pitch':'string','action':'start'})
print(response.status_code)
print(response.json())
