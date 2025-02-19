# MCP Translation Server Usage Examples

## Basic Usage Examples

### 1. Simple Translation

```python
import requests

# Basic translation
response = requests.post('http://localhost:8080/translate', 
                       json={'text': 'mini gisun'})
print(response.json()['translation'])
```

### 2. Translation with Analysis

```python
# Translation with detailed analysis
response = requests.post('http://localhost:8080/translate', 
                       json={
                           'text': 'mini gisun',
                           'options': {
                               'include_analysis': True,
                               'include_grammar': True
                           }
                       })
result = response.json()
print(f"Translation: {result['translation']}")
print(f"Grammar Rules: {result['analysis']['grammar_rules']}")
```

### 3. Dictionary Lookup

```python
# Looking up words in dictionary
response = requests.get('http://localhost:8080/dictionary/mini')
entries = response.json()
for entry in entries['definitions']:
    print(f"Meaning: {entry['meaning']}")
    print(f"Examples: {entry['examples']}")
```

## Advanced Usage Examples

### 1. Batch Translation

```python
# Translating multiple texts
texts = ['mini gisun', 'sini gisun', 'ini gisun']
responses = []

for text in texts:
    response = requests.post('http://localhost:8080/translate',
                           json={'text': text})
    responses.append(response.json())

for text, result in zip(texts, responses):
    print(f"{text} -> {result['translation']}")
```

### 2. Grammar Analysis

```python
# Detailed grammar analysis
response = requests.post('http://localhost:8080/analyze/grammar',
                        json={'text': 'mini gisun be'})
rules = response.json()['rules']

for rule in rules:
    print(f"Rule: {rule['description']}")
    print(f"Pattern: {rule['pattern']}")
```

### 3. Using with Python Client

```python
from mcp_client import MCPClient

client = MCPClient('http://localhost:8080')

# Simple translation
translation = client.translate('mini gisun')

# With analysis
result = client.translate('mini gisun', 
                        include_analysis=True,
                        include_grammar=True)

# Dictionary lookup
word_info = client.lookup_word('mini')
```

## Error Handling Examples

```python
try:
    response = requests.post('http://localhost:8080/translate',
                           json={'text': ''})
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"Error: {e.response.json()['error']['message']}")
```

## Performance Optimization Examples

```python
from concurrent.futures import ThreadPoolExecutor
import time

def translate_text(text):
    return requests.post('http://localhost:8080/translate',
                        json={'text': text}).json()

texts = ['text1', 'text2', 'text3', 'text4', 'text5']

# Parallel translation
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(translate_text, texts))
```
