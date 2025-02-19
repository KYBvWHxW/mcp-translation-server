"""
Production configuration for MCP Translation Server.
"""
import os

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = int(os.getenv("PORT", "8080"))
API_DEBUG = False

# Security Settings
SECRET_KEY = os.getenv("MCP_SECRET_KEY")
API_TOKEN = os.getenv("MCP_API_TOKEN")

# Rate Limiting
RATE_LIMIT = {
    "default": "100/minute",
    "authenticated": "1000/minute"
}

# Cache Configuration
CACHE_TYPE = "redis"
CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
CACHE_REDIS_PASSWORD = os.getenv("MCP_REDIS_PASSWORD")

# Model Configuration
MODEL_PATH = "/app/models/mt5-manchu-chinese"
MODEL_DEVICE = "cuda" if os.getenv("USE_GPU", "false").lower() == "true" else "cpu"
MODEL_BATCH_SIZE = 32
MODEL_MAX_LENGTH = 512

# Resource Paths
DICTIONARY_PATH = "/app/resources/dictionary.json"
GRAMMAR_RULES_PATH = "/app/resources/grammar.json"
MORPHOLOGY_RULES_PATH = "/app/resources/morphology.json"

# Monitoring
ENABLE_METRICS = True
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "/app/logs/translation_server.log"

# Email Notifications
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("MCP_SMTP_PASSWORD")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

# Performance Tuning
WORKER_PROCESSES = int(os.getenv("WORKER_PROCESSES", "4"))
THREAD_POOL_SIZE = int(os.getenv("THREAD_POOL_SIZE", "4"))
MAX_REQUESTS_JITTER = int(os.getenv("MAX_REQUESTS_JITTER", "1000"))

# Resource Management
MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "4096"))
GRACEFUL_TIMEOUT_SECONDS = int(os.getenv("GRACEFUL_TIMEOUT", "30"))

# Feature Flags
ENABLE_BATCH_PROCESSING = os.getenv("ENABLE_BATCH_PROCESSING", "true").lower() == "true"
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
