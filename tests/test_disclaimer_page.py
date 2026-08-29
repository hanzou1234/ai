from fastapi.testclient import TestClient

from app.main import app


def test_disclaimer_page_available():
    client = TestClient(app)
    response = client.get("/disclaimer")

    assert response.status_code == 200
    assert "Transaction Disclaimer" in response.text
    assert "AI agent malfunction" in response.text
