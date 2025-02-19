# MCP Translation Server API Documentation

## Overview

MCP Translation Server 提供了完整的 RESTful API 接口，支持满文-汉文双向翻译、词典查询、语法分析等功能。

## 基本信息

### Base URL
```
https://api.mcp-translation.org/v1
```

### 认证

所有 API 请求需要包含 API 密钥：

```bash
Authorization: Bearer YOUR_API_KEY
```

## API 端点

### 1. 翻译服务

#### POST /translate

满文-汉文双向翻译。

**请求参数**

```json
{
    "text": "mini gisun",
    "direction": "m2c",  // "m2c" 或 "c2m"
    "options": {
        "include_analysis": true,
        "include_grammar": true,
        "include_examples": true,
        "model": "mt5-base",  // 可选：mt5-small, mt5-base, mt5-large
        "beam_size": 5
    }
}
```

**响应**

```json
{
    "translation": "我的话",
    "analysis": {
        "morphology": [
            {
                "word": "mini",
                "root": "bi",
                "suffix": "-ni",
                "features": ["1SG", "GEN"]
            },
            {
                "word": "gisun",
                "root": "gisun",
                "features": ["N"]
            }
        ],
        "grammar_rules": [
            {
                "id": "POSS_1",
                "description": "第一人称领属结构",
                "confidence": 0.95
            }
        ],
        "examples": [
            {
                "manchu": "mini gisun be donji",
                "chinese": "听我的话"
            }
        ]
    },
    "confidence": 0.95,
    "alternatives": [
        {
            "text": "我说的",
            "confidence": 0.85
        }
    ],
    "request_id": "tr_abc123",
    "processing_time": 0.15
}
```

#### POST /translate/batch

批量翻译接口。

**请求参数**

```json
{
    "texts": [
        "mini gisun",
        "sini gisun"
    ],
    "direction": "m2c",
    "options": {
        "include_analysis": true
    }
}
```

### 2. 词典服务

#### GET /dictionary/lookup/{word}

词典查询。

**响应**

```json
{
    "word": "mini",
    "lexical": "我的",
    "suffixes": ["-i", "-be"],
    "collocations": [
        "mini gisun",
        "mini jui"
    ],
    "senses": [
        {
            "meaning": "我的",
            "context": "代词",
            "usage_notes": "第一人称单数领属格"
        }
    ],
    "examples": [
        {
            "manchu": "mini gisun be donji",
            "chinese": "听我的话",
            "source": "清文鉴"
        }
    ]
}
```

#### POST /dictionary/search

词典模糊搜索。

**请求参数**

```json
{
    "query": "min",
    "match_type": "prefix",  // prefix, fuzzy, semantic
    "max_results": 10
}
```

### 3. 语法分析

#### POST /analyze/grammar

语法分析。

**请求参数**

```json
{
    "text": "mini gisun",
    "options": {
        "include_morphology": true,
        "include_examples": true
    }
}
```

### 4. 资源管理

#### GET /resources/status

获取资源状态。

**响应**

```json
{
    "dictionary": {
        "version": "2.1.0",
        "entry_count": 12500,
        "last_updated": "2025-02-19T08:00:00Z"
    },
    "grammar_rules": {
        "version": "1.5.0",
        "rule_count": 350
    },
    "models": {
        "mt5-base": {
            "version": "1.2.0",
            "size": "1.2GB"
        }
    }
}
```

### 5. 系统状态

#### GET /health

健康检查。

**响应**

```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "metrics": {
        "requests_total": 15000,
        "requests_per_minute": 25,
        "average_latency": 0.15
    }
}
```

## 错误处理

所有端点使用统一的错误响应格式：

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {
            "param": "text",
            "reason": "参数不能为空"
        },
        "request_id": "req_abc123"
    }
}
```

### 错误代码

- `INVALID_INPUT`: 输入参数无效
- `RESOURCE_NOT_FOUND`: 资源不存在
- `RATE_LIMIT_EXCEEDED`: 超过访问限制
- `UNAUTHORIZED`: 未授权或授权失败
- `INTERNAL_ERROR`: 内部服务器错误

## 访问控制

### 认证

1. 获取 API 密钥：
   - 访问管理控制台创建密钥
   - 每个密钥都有唯一的权限范围

2. 使用 Bearer Token 认证：
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -X POST https://api.mcp-translation.org/v1/translate
```

### 访问限制

1. 速率限制：
   - 基础套餐：100 请求/分钟
   - 专业套餐：1000 请求/分钟
   - 企业套餐：无限制

2. 限制头部：
   - `X-RateLimit-Limit`: 总限制
   - `X-RateLimit-Remaining`: 剩余配额
   - `X-RateLimit-Reset`: 重置时间

### 安全要求

1. 所有请求必须使用 HTTPS
2. API 密钥定期轮换
3. 敏感操作需要额外验证

## 监控和指标

### Prometheus 指标

访问 `/metrics` 端点获取 Prometheus 格式的指标。

### 应用指标

- `mcp_requests_total`: 总请求数
- `mcp_request_duration_seconds`: 请求响应时间
- `mcp_errors_total`: 错误数
- `mcp_cache_hit_ratio`: 缓存命中率

## 版本控制

当前 API 版本：v1

将来的版本更新将通过新的 URL 前缀发布，如 `/v2/*`。

## 支持

- 文档：[docs.mcp-translation.org](https://docs.mcp-translation.org)
- 问题反馈：[GitHub Issues](https://github.com/your-org/mcp-translation-server/issues)
- 邮件支持：support@mcp-translation.org
