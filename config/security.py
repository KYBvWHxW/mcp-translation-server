"""
Security configuration for MCP Translation Server.
"""
import os
from datetime import timedelta

class SecurityConfig:
    # JWT Settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')  # Change in production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # API Key Settings
    API_KEY_LENGTH = 32
    API_KEY_DEFAULT_EXPIRY_DAYS = 365
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT = 100  # requests per window
    DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'X-Content-Type-Options': 'nosniff',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Access Control
    REQUIRED_SCOPES = {
        'translate': ['translate:read', 'translate:write'],
        'admin': ['admin:read', 'admin:write'],
        'metrics': ['metrics:read']
    }
    
    # IP Allowlist/Blocklist
    IP_ALLOWLIST = os.getenv('IP_ALLOWLIST', '').split(',')
    IP_BLOCKLIST = os.getenv('IP_BLOCKLIST', '').split(',')
    
    # Request Size Limits
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Password Policy
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = True
    PASSWORD_MAX_AGE = timedelta(days=90)
    
    @classmethod
    def init_app(cls, app):
        """Initialize security settings for the Flask app."""
        # Set security-related config
        app.config['JWT_SECRET_KEY'] = cls.JWT_SECRET_KEY
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = cls.JWT_ACCESS_TOKEN_EXPIRES
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = cls.JWT_REFRESH_TOKEN_EXPIRES
        app.config['MAX_CONTENT_LENGTH'] = cls.MAX_CONTENT_LENGTH
        app.config['SESSION_COOKIE_SECURE'] = cls.SESSION_COOKIE_SECURE
        app.config['SESSION_COOKIE_HTTPONLY'] = cls.SESSION_COOKIE_HTTPONLY
        app.config['SESSION_COOKIE_SAMESITE'] = cls.SESSION_COOKIE_SAMESITE
        app.config['PERMANENT_SESSION_LIFETIME'] = cls.PERMANENT_SESSION_LIFETIME
        
        # Register security headers
        def add_security_headers(response):
            for header, value in cls.SECURITY_HEADERS.items():
                response.headers[header] = value
            return response
        
        # IP filtering middleware
        def ip_filtering():
            from flask import request, abort
            client_ip = request.remote_addr
            
            # Check blocklist
            if client_ip in cls.IP_BLOCKLIST:
                abort(403)
            
            # Check allowlist if not empty
            if cls.IP_ALLOWLIST and client_ip not in cls.IP_ALLOWLIST:
                abort(403)
        
        # 只在第一次初始化时注册中间件
        if not hasattr(app, '_security_initialized'):
            app.after_request(add_security_headers)
            app.before_request(ip_filtering)
            app._security_initialized = True
