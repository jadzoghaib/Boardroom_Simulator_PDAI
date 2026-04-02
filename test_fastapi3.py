from fastapi.testclient import TestClient
from test_fastapi2 import app
try:
    client = TestClient(app)
    response = client.post('/api/boardroom_turn', json={'thread_id':'testerr1','budget':0,'burn_rate':0,'revenue':0,'founder_experience':0,'sector':'string','pitch':'string','action':'start'})
    print(response.status_code)
    print(response.json())
except Exception as e:
    import traceback
    print("Caught unhandled exception:")
    traceback.print_exc()
