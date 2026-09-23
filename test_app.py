from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ask_question():
    response = client.post(
        "/ask",
        json={"question": "How many automations can I have on the Team plan?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "billing-faq.md" in data["sources"]