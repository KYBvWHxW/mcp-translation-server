# MCP Translation Server

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](docs/operations.md)

## Overview

MCP Translation Server 是一个专门用于满-汉双向翻译的高性能机器翻译系统。它基于先进的语言学处理和深度学习技术，为低资源语言翻译提供全面的解决方案。

## 主要特性

### 1. 增强型形态分析
- 🔍 完整的满语语言规则支持
- 🎯 精确的元音和谐分析
- 📊 智能词形变化预测
- ✨ 自动错误检测和纠正

### 2. 高级翻译引擎
- 🚀 多级翻译策略
- 📚 智能语料库匹配
- 🔄 形态分析集成
- 📊 详细翻译元数据

### 3. 丰富的语言资源
- 📖 完整的语言规则系统
- 💾 扩展的平行语料库
- 📚 优化的词典结构
- 🔍 上下文感知分析

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/yourusername/mcp-translation-server.git
cd mcp-translation-server
```

### 2. 环境设置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置
```bash
# 复制配置模板
cp config/config.example.json config/config.json

# 编辑配置文件
vim config/config.json  # 或使用其他编辑器
```

### 4. 运行演示
```bash
# 运行综合演示
python demo/comprehensive_demo.py

# 运行翻译服务器
python server.py
```

## 系统架构

### 核心组件
1. **形态分析器** (`enhanced_morphology.py`)
   - 词形分析和生成
   - 元音和谐处理
   - 错误检测和纠正

2. **翻译引擎** (`enhanced_translation.py`)
   - 多级翻译策略
   - 语料库匹配
   - 形态分析集成

3. **语言资源**
   - 语言规则 (`manchu_rules.json`)
   - 平行语料库 (`parallel_corpus.json`)
   - 词典系统 (`dictionary.json`)

## API 文档

### 基本翻译
```python
POST /api/v1/translate
Content-Type: application/json

{
    "text": "bi bithe arambi",
    "source_lang": "manchu",
    "target_lang": "chinese"
}
```

### 形态分析
```python
POST /api/v1/analyze
Content-Type: application/json

{
    "text": "arambi",
    "type": "morphology"
}
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- 感谢所有为满语研究做出贡献的学者
- 感谢开源社区的支持
- 特别感谢为本项目提供语料和建议的专家们
# Copy example configuration file
cp config.example.py config.py

# Edit config.py with your settings
vim config.py  # or use your preferred editor

# Set required environment variables
export MCP_SECRET_KEY="your-secure-random-string"  # Required
export MCP_API_TOKEN="your-api-token"            # Required
export MCP_REDIS_PASSWORD="your-redis-password"  # Optional
export MCP_SMTP_PASSWORD="your-smtp-password"    # Optional
```

4. Run the server:
```bash
python server.py
```

### Configuration

#### Environment Variables

The following environment variables are supported:

| Variable | Required | Description | Example |
|----------|----------|-------------|----------|
| `MCP_SECRET_KEY` | Yes | Secret key for session encryption | `openssl rand -hex 32` |
| `MCP_API_TOKEN` | Yes | API authentication token | `openssl rand -hex 32` |
| `MCP_REDIS_PASSWORD` | No | Redis server password | `your-redis-password` |
| `MCP_SMTP_PASSWORD` | No | SMTP server password | `your-smtp-password` |

#### Configuration File

The server can be configured by copying `config.example.py` to `config.py` and editing the values. The configuration file supports:

- API settings (host, port, debug mode)
- Security settings (secret key, API token)
- Rate limiting rules
- Cache configuration
- Model settings
- Resource paths
- Monitoring options
- Logging configuration
- Email notifications

**Important Security Notes:**

1. Never commit `config.py` to version control
2. Use strong, random values for `SECRET_KEY` and `API_TOKEN`
3. Store sensitive credentials in environment variables
4. Keep your `.env` file secure and never commit it
5. Regularly rotate security credentials

## Documentation

- [API Documentation](docs/api.md)
- [Usage Examples](docs/examples.md)
- [Operations Guide](docs/operations.md)
- [Contributing Guide](CONTRIBUTING.md)

## Architecture

### Core Components

1. Translation Engine
   - MT5-based neural translation
   - Context-aware processing
   - Batch processing support

2. Language Resources
   - Comprehensive dictionary
   - Grammar rule engine
   - Morphological analyzer
   - Parallel corpus

3. System Features
   - Efficient caching
   - Performance monitoring
   - Resource management
   - Error handling

## Performance

- Average translation latency: < 1s
- 95th percentile latency: < 2s
- Concurrent request handling: 100+ req/s
- Cache hit rate: > 80%

## Monitoring

- Real-time metrics via Prometheus
- Visualizations through Grafana
- Automated alerting system
- Performance tracking

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Research paper authors
- Open-source community
- Contributors and maintainers

## Contact

- GitHub Issues: For bug reports and feature requests
- Email: your.email@example.com
- Documentation: [Full Documentation](docs/)
   - Analysis (C^a)
   - Structure (C^a+s)
