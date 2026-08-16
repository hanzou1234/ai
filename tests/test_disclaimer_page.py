from fastapi.testclient import TestClient

from app.main import app


def test_disclaimer_page_available():
    client = TestClient(app)
    response = client.get("/disclaimer")

    assert response.status_code == 200
    assert "取引に関する免責事項" in response.text
    assert "AIエージェントの誤作動" in response.text
