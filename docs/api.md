# MCP Translation Server API Documentation

## Overview

The MCP Translation Server provides RESTful APIs for Manchu-Chinese translation services. This document describes the available endpoints, their parameters, and response formats.

## Base URL

```
http://localhost:8080
```

## Endpoints

### 1. Translation

#### POST /translate

Translates Manchu text to Chinese.

**Request**

```json
{
    "text": "mini gisun",
    "options": {
        "include_analysis": true,
        "include_grammar": true,
        "include_examples": true
    }
}
```

**Response**

```json
{
    "translation": "我的话",
    "analysis": {
        "morphology": [...],
        "grammar_rules": [...],
        "examples": [...]
    },
    "confidence": 0.95
}
```

### 2. Dictionary Lookup

#### GET /dictionary/{word}

Looks up a word in the dictionary.

**Response**

```json
{
    "word": "mini",
    "definitions": [
        {
            "meaning": "我的",
            "part_of_speech": "pronoun",
            "examples": [...]
        }
    ]
}
```

### 3. Grammar Analysis

#### POST /analyze/grammar

Analyzes the grammar of a given text.

**Request**

```json
{
    "text": "mini gisun"
}
```

**Response**

```json
{
    "rules": [
        {
            "id": "POSS_1",
            "description": "First person possessive",
            "matches": [...]
        }
    ]
}
```

## Error Handling

All endpoints follow the same error response format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message"
    }
}
```

Common error codes:
- `INVALID_INPUT`: Input text is invalid or empty
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

- Rate limit: 100 requests per minute per IP
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Authentication

Currently, the API is open for public access. Future versions may require authentication.
