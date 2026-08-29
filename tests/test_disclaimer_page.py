from fastapi.testclient import TestClient

from app.main import app


def test_disclaimer_page_available():
    client = TestClient(app)
    response = client.get("/disclaimer")

    assert response.status_code == 200
    assert "Transaction Disclaimer" in response.text
    assert "AI agent malfunction" in response.text


def test_home_and_skill_guide_link_to_each_other():
    client = TestClient(app)

    home = client.get("/")
    guide = client.get("/skill.md")

    assert home.status_code == 200
    assert 'href="/skill.md"' in home.text
    assert guide.status_code == 200
    assert "[Marketplace UI](/)" in guide.text
