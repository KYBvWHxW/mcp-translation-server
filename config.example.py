"""
Example configuration file for MCP Translation Server.
Copy this file to config.py and update the values with your own settings.
DO NOT commit config.py to version control.
"""

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 5000
API_DEBUG = False

# Security Settings
SECRET_KEY = "your-secret-key-here"  # Change this to a secure random string
API_TOKEN = "your-api-token-here"    # Change this to a secure random string

# Rate Limiting
RATE_LIMIT = {
    "default": "100/hour",
    "authenticated": "1000/hour"
}

# Cache Configuration
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://localhost:6379/0"
CACHE_DEFAULT_TIMEOUT = 300

# Model Configuration
MODEL_PATH = "/path/to/your/model"
MODEL_DEVICE = "cuda"  # or "cpu"
MODEL_BATCH_SIZE = 32
MODEL_MAX_LENGTH = 512

# Resource Paths
DICTIONARY_PATH = "resources/dictionary.json"
GRAMMAR_RULES_PATH = "resources/grammar.json"
MORPHOLOGY_RULES_PATH = "resources/morphology.json"

# Monitoring
ENABLE_METRICS = True
PROMETHEUS_PORT = 9090

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/translation_server.log"

# Email Notifications (Optional)
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@example.com"
SMTP_PASSWORD = "your-email-password"  # Use environment variable in production
ALERT_EMAIL = "alerts@example.com"

# Load sensitive information from environment variables
import os

# Override settings with environment variables if they exist
SECRET_KEY = os.getenv("MCP_SECRET_KEY", SECRET_KEY)
API_TOKEN = os.getenv("MCP_API_TOKEN", API_TOKEN)
SMTP_PASSWORD = os.getenv("MCP_SMTP_PASSWORD", SMTP_PASSWORD)

# Redis credentials (if using authentication)
REDIS_PASSWORD = os.getenv("MCP_REDIS_PASSWORD", None)
if REDIS_PASSWORD:
    CACHE_REDIS_URL = f"redis://:{REDIS_PASSWORD}@localhost:6379/0"
