import pytest
from flask.testing import FlaskClient
from server import app, init_app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_translate_endpoint(client):
    """Test the basic translation endpoint."""
    response = client.post('/api/v1/translate',
                          json={'text': 'ere amba de tehe'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'translation' in data
    assert isinstance(data['translation'], str)

def test_translate_with_context(client):
    """Test translation with context."""
    response = client.post('/api/v1/translate',
                          json={
                              'text': 'ere amba de tehe',
                              'context': 'location'
                          })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'translation' in data
    assert 'context' in data

def test_batch_translate(client):
    """Test batch translation endpoint."""
    texts = ['ere amba', 'tere amba']
    response = client.post('/api/v1/batch_translate',
                          json={'texts': texts})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'translations' in data
    assert len(data['translations']) == len(texts)

def test_dictionary_lookup(client):
    """Test dictionary lookup endpoint."""
    response = client.get('/api/v1/dictionary/amba')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'definitions' in data

def test_invalid_input(client):
    """Test error handling for invalid input."""
    response = client.post('/api/v1/translate',
                          json={'text': ''})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_rate_limiting(client):
    """Test rate limiting functionality."""
    # Make multiple requests in quick succession
    responses = []
    for _ in range(10):
        response = client.post('/api/v1/translate',
                             json={'text': 'test'})
        responses.append(response)
    
    # Check if rate limiting was applied
    assert any(r.status_code == 429 for r in responses)

def test_cache_control(client):
    """Test cache control headers."""
    text = 'ere amba de tehe'
    
    # First request
    response1 = client.post('/api/v1/translate',
                           json={'text': text})
    assert response1.status_code == 200
    
    # Second request with same text
    response2 = client.post('/api/v1/translate',
                           json={'text': text})
    assert response2.status_code == 200
    
    # Check cache headers
    assert 'Cache-Control' in response2.headers

def test_error_handling(client):
    """Test various error scenarios."""
    # Test missing required field
    response = client.post('/api/v1/translate',
                          json={})
    assert response.status_code == 400
    
    # Test invalid JSON
    response = client.post('/api/v1/translate',
                          data='invalid json')
    assert response.status_code == 400
    
    # Test method not allowed
    response = client.get('/api/v1/translate')
    assert response.status_code == 405

def test_metrics_endpoint(client):
    """Test metrics collection endpoint."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'translation_requests_total' in response.data

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
