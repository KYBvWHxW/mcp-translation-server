"""
全面的安全功能测试套件
"""
import pytest
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from api.auth import AuthManager, RateLimiter, require_auth, rate_limit
from config.security import SecurityConfig

@pytest.fixture
def app():
    """创建测试用Flask应用"""
    app = Flask(__name__)
    SecurityConfig.init_app(app)
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    # 模拟Redis连接
    mock_redis = MagicMock()
    app.auth_manager = AuthManager()
    app.auth_manager.redis = mock_redis
    app.rate_limiter = RateLimiter()
    app.rate_limiter.redis = mock_redis
    
    return app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

class TestAuthManager:
    def test_generate_api_key(self, app):
        """测试API密钥生成"""
        with app.app_context():
            auth_manager = app.auth_manager
            api_key = auth_manager.generate_api_key(
                user_id='test_user',
                scopes=['test:read', 'test:write']
            )
            assert len(api_key) > 0
            assert auth_manager.redis.hmset.called

    def test_validate_api_key(self, app):
        """测试API密钥验证"""
        with app.app_context():
            auth_manager = app.auth_manager
            # 模拟有效的API密钥数据
            auth_manager.redis.hgetall.return_value = {
                'user_id': 'test_user',
                'scopes': "['test:read']",
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
            
            result = auth_manager.validate_api_key('test-key')
            assert result is not None
            assert result['user_id'] == 'test_user'

    def test_generate_jwt(self, app):
        """测试JWT令牌生成"""
        with app.app_context():
            auth_manager = app.auth_manager
            token = auth_manager.generate_jwt(
                user_id='test_user',
                scopes=['test:read']
            )
            assert token is not None
            
            # 验证令牌
            payload = jwt.decode(
                token,
                app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            assert payload['user_id'] == 'test_user'
            assert 'test:read' in payload['scopes']

    def test_validate_jwt(self, app):
        """测试JWT令牌验证"""
        with app.app_context():
            auth_manager = app.auth_manager
            token = auth_manager.generate_jwt(
                user_id='test_user',
                scopes=['test:read']
            )
            
            result = auth_manager.validate_jwt(token)
            assert result is not None
            assert result['user_id'] == 'test_user'
            assert 'test:read' in result['scopes']

    def test_blacklist_jwt(self, app):
        """测试JWT令牌黑名单"""
        with app.app_context():
            auth_manager = app.auth_manager
            token = auth_manager.generate_jwt(
                user_id='test_user',
                scopes=['test:read']
            )
            
            assert auth_manager.blacklist_jwt(token)
            assert not auth_manager.validate_jwt(token)

class TestRateLimiter:
    def test_rate_limit_allowed(self, app):
        """测试请求频率限制 - 允许的情况"""
        with app.app_context():
            rate_limiter = app.rate_limiter
            pipeline_mock = MagicMock()
            pipeline_mock.execute.return_value = [1]
            rate_limiter.redis.pipeline.return_value.__enter__.return_value = pipeline_mock
            
            assert rate_limiter.is_allowed('test_key', 100)

    def test_rate_limit_exceeded(self, app):
        """测试请求频率限制 - 超限的情况"""
        with app.app_context():
            rate_limiter = app.rate_limiter
            pipeline_mock = MagicMock()
            pipeline_mock.execute.return_value = [101]
            rate_limiter.redis.pipeline.return_value.__enter__.return_value = pipeline_mock
            
            assert not rate_limiter.is_allowed('test_key', 100)

    def test_get_limit_headers(self, app):
        """测试频率限制响应头"""
        with app.app_context():
            rate_limiter = app.rate_limiter
            rate_limiter.redis.get.return_value = b'50'
            
            headers = rate_limiter.get_limit_headers('test_key', 100)
            assert 'X-RateLimit-Limit' in headers
            assert 'X-RateLimit-Remaining' in headers
            assert 'X-RateLimit-Reset' in headers

class TestSecurityMiddleware:
    def test_security_headers(self, client):
        """测试安全响应头"""
        response = client.get('/')
        
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        assert 'Strict-Transport-Security' in response.headers

    def test_ip_filtering(self, app):
        """测试IP过滤"""
        with app.test_request_context():
            # 测试IP黑名单
            app.test_client().get('/', environ_base={'REMOTE_ADDR': '192.168.1.1'})
            SecurityConfig.IP_BLOCKLIST = ['192.168.1.1']
            SecurityConfig.init_app(app)
            
            response = app.test_client().get('/', environ_base={'REMOTE_ADDR': '192.168.1.1'})
            assert response.status_code == 403
            
            # 测试IP白名单
            SecurityConfig.IP_ALLOWLIST = ['192.168.1.3']
            SecurityConfig.IP_BLOCKLIST = []
            SecurityConfig.init_app(app)
            
            response = app.test_client().get('/', environ_base={'REMOTE_ADDR': '192.168.1.2'})
            assert response.status_code == 403
            
            response = app.test_client().get('/', environ_base={'REMOTE_ADDR': '192.168.1.3'})
            assert response.status_code == 404  # 404因为路由未定义

def test_protected_endpoint(app, client):
    """测试受保护的API端点"""
    @app.route('/protected')
    @require_auth(['test:read'])
    def protected():
        return jsonify({'message': 'success'})
    
    # 重置安全设置
    SecurityConfig.IP_ALLOWLIST = []
    SecurityConfig.IP_BLOCKLIST = []
    SecurityConfig.init_app(app)
    
    # 测试无认证请求
    response = client.get('/protected')
    assert response.status_code == 401
    
    # 测试有效JWT认证
    with app.app_context():
        token = app.auth_manager.generate_jwt(
            user_id='test_user',
            scopes=['test:read']
        )
        
        response = client.get(
            '/protected',
            headers={'Authorization': f'JWT {token}'}
        )
        assert response.status_code == 200
        
    # 测试无效JWT认证
    response = client.get(
            '/protected',
            headers={'Authorization': 'JWT invalid-token'}
        )
    assert response.status_code == 401

def test_rate_limited_endpoint(app, client):
    """测试带频率限制的API端点"""
    @app.route('/limited')
    @rate_limit(limit=2)
    def limited():
        return jsonify({'message': 'success'})
    
    # 重置安全设置
    SecurityConfig.IP_ALLOWLIST = []
    SecurityConfig.IP_BLOCKLIST = []
    SecurityConfig.init_app(app)
    
    # 模拟Redis pipeline
    pipeline_mock = MagicMock()
    pipeline_mock.execute.side_effect = [[1], [2], [3]]
    app.rate_limiter.redis.pipeline.return_value.__enter__.return_value = pipeline_mock
    
    # 前两个请求应该成功
    for _ in range(2):
        response = client.get('/limited')
        assert response.status_code == 200
        assert 'X-RateLimit-Remaining' in response.headers
    
    # 第三个请求应该被限制
    response = client.get('/limited')
    assert response.status_code == 429
