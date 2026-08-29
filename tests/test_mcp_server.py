from fastapi.testclient import TestClient

from app.main import app


def test_mcp_server_exposes_tools_and_health():
    client = TestClient(app)

    health = client.get('/mcp/health')
    assert health.status_code == 200
    assert health.json()['status'] == 'ok'

    response = client.post('/mcp', json={
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/list',
        'params': {}
    })

    assert response.status_code == 200
    data = response.json()
    tool_names = {tool['name'] for tool in data['result']['tools']}
    assert 'search_agents' in tool_names
    assert 'register_agent' in tool_names
    assert 'negotiate_contract' in tool_names
