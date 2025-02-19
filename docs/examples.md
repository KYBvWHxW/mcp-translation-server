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

### 1. Parallel Processing

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

### 2. Batch Processing with Context

```python
# Batch translation with context
batch_data = [
    {'text': 'amba moo i baru', 'context': 'direction'},
    {'text': 'amba boo', 'context': 'building'},
    {'text': 'amba niyalma', 'context': 'person'}
]

response = requests.post('http://localhost:8080/batch_translate',
                        json={'texts': batch_data})

for result in response.json()['translations']:
    print(f"Original: {result['original']}")
    print(f"Translation: {result['translation']}")
    print(f"Context: {result['context']}\n")
```

### 3. Caching Strategy

```python
from datetime import datetime

def translate_with_cache(text, context=None):
    # Add timestamp for cache control
    cache_key = f"{text}:{context}:{datetime.now().strftime('%Y%m%d')}"
    
    response = requests.post('http://localhost:8080/translate',
                           json={
                               'text': text,
                               'context': context,
                               'cache_key': cache_key
                           },
                           headers={'Cache-Control': 'max-age=3600'})
    return response.json()

# First call will be cached
result1 = translate_with_cache('amba moo', 'nature')

# Second call will use cache
result2 = translate_with_cache('amba moo', 'nature')
```

## Real-world Usage Examples

### 1. Document Translation

```python
def translate_document(file_path):
    # Read document content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into paragraphs
    paragraphs = content.split('\n\n')
    
    # Translate each paragraph with context
    translations = []
    for i, para in enumerate(paragraphs):
        response = requests.post('http://localhost:8080/translate',
                               json={
                                   'text': para,
                                   'context': f'paragraph_{i}',
                                   'preserve_format': True
                               })
        translations.append(response.json()['translation'])
    
    # Combine translations
    return '\n\n'.join(translations)

# Usage
translated_doc = translate_document('manchu_text.txt')
with open('translated_doc.txt', 'w', encoding='utf-8') as f:
    f.write(translated_doc)
```

### 2. Interactive Translation

```python
import tkinter as tk
from tkinter import ttk

class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Manchu Translator')
        
        # Input area
        self.input_text = tk.Text(root, height=5)
        self.input_text.pack(padx=10, pady=5)
        
        # Context selection
        self.context = ttk.Combobox(root, 
                                   values=['general', 'historical',
                                          'literary', 'technical'])
        self.context.set('general')
        self.context.pack(pady=5)
        
        # Translate button
        self.translate_btn = tk.Button(root, 
                                      text='Translate',
                                      command=self.translate)
        self.translate_btn.pack(pady=5)
        
        # Output area
        self.output_text = tk.Text(root, height=5)
        self.output_text.pack(padx=10, pady=5)
    
    def translate(self):
        text = self.input_text.get('1.0', tk.END).strip()
        context = self.context.get()
        
        response = requests.post('http://localhost:8080/translate',
                               json={
                                   'text': text,
                                   'context': context
                               })
        
        result = response.json()
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert('1.0', result['translation'])

# Run the app
root = tk.Tk()
app = TranslationApp(root)
root.mainloop()
```

### 3. API Integration Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = 'manchu'
    target_lang: str = 'chinese'
    context: str = None

@app.post('/translate')
async def translate(request: TranslationRequest):
    try:
        # Call MCP Translation Server
        response = requests.post(
            'http://localhost:8080/translate',
            json={
                'text': request.text,
                'context': request.context
            }
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Add additional processing if needed
        return {
            'success': True,
            'translation': result['translation'],
            'source': request.text,
            'metadata': {
                'source_lang': request.source_lang,
                'target_lang': request.target_lang,
                'context': request.context
            }
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500,
                          detail=str(e))
```
