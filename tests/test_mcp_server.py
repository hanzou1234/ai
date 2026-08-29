from fastapi.testclient import TestClient

from app.main import app


def test_mcp_server_exposes_tools_and_health():
    with TestClient(app, base_url='https://ai-qmtw.onrender.com') as client:
        health = client.get('/mcp/health')
        assert health.status_code == 200
        assert health.json()['status'] == 'ok'

        initialize = client.post('/mcp', json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-11-25',
                'capabilities': {},
                'clientInfo': {'name': 'pytest', 'version': '1.0.0'},
            },
        }, headers={'Accept': 'application/json, text/event-stream'})

        assert initialize.status_code == 200
        assert initialize.json()['result']['serverInfo']['name'] == 'agent-economy-engine'

        response = client.post('/mcp', json={
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/list',
            'params': {},
        }, headers={'Accept': 'application/json, text/event-stream'})

        assert response.status_code == 200
        data = response.json()
        tool_names = {tool['name'] for tool in data['result']['tools']}
        assert 'search_agents' in tool_names
        assert 'register_agent' in tool_names
        assert 'negotiate_contract' in tool_names
