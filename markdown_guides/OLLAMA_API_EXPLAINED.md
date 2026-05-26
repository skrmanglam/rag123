# 🔌 How We Call Ollama API

## Your Question

> "I did remember that I called ollama without specifying the model and it used to work via rest api calls, how are we doing it?"

## How We're Calling Ollama

We're using Ollama's **REST API** at `http://localhost:11434/api/generate`

### Our Implementation (in `core/rag_chain.py`):

```python
response = requests.post(
    f"{self.ollama_base_url}/api/generate",  # http://localhost:11434/api/generate
    json={
        "model": "phi3:mini",  # ← We MUST specify the model
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 500
        }
    }
)
```

## Why We Must Specify the Model

Ollama's API **requires** you to specify which model to use. There's no "default" model.

### Ollama API Endpoints:

1. **Generate (what we use):**
   ```bash
   POST http://localhost:11434/api/generate
   {
     "model": "phi3:mini",  # Required!
     "prompt": "Your question here"
   }
   ```

2. **Chat (alternative):**
   ```bash
   POST http://localhost:11434/api/chat
   {
     "model": "phi3:mini",  # Required!
     "messages": [...]
   }
   ```

## How to Find Your Exact Model Name

```bash
# List all installed models
ollama list

# Output example:
# NAME              ID              SIZE      MODIFIED
# phi3:mini         abc123...       2.3 GB    2 days ago
# llama3.2:latest   def456...       2.0 GB    1 week ago
```

**Use the exact NAME** (including the tag after `:`)

## Common Model Name Patterns

| What You See | What to Use in Config |
|--------------|----------------------|
| `phi3:mini` | `"phi3:mini"` |
| `phi3:latest` | `"phi3:latest"` or `"phi3"` |
| `llama3.2:latest` | `"llama3.2:latest"` or `"llama3.2"` |
| `mistral:7b` | `"mistral:7b"` |

**Note:** If you omit the tag (e.g., use `"phi3"` instead of `"phi3:mini"`), Ollama assumes `:latest`

## Your Current Setup

**Config file (`config/settings.yaml`):**
```yaml
llm:
  ollama:
    model: "phi3:mini"  # ← Fixed to match your model!
```

**How it's called in code:**
```python
# In core/rag_chain.py
model = self.llm_config.get('ollama', {}).get('model', 'llama3.2')
# model = "phi3:mini"

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": model,  # "phi3:mini"
        "prompt": "Your question..."
    }
)
```

## Testing Your Model Directly

### Via Command Line:
```bash
ollama run phi3:mini "Hello, how are you?"
```

### Via REST API (what we do):
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "phi3:mini",
  "prompt": "Hello, how are you?",
  "stream": false
}'
```

### Via Python (what our code does):
```python
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "phi3:mini",
        "prompt": "Hello, how are you?",
        "stream": False
    }
)

print(response.json()['response'])
```

## Why You Might Have Seen It Work Without Specifying Model

Possible reasons:

1. **Using `ollama run` command** - This uses the last model you ran
2. **Using a wrapper library** - Some libraries have defaults
3. **Environment variable** - Some setups use `OLLAMA_MODEL` env var
4. **Different API version** - Older versions might have had defaults

But the **official Ollama REST API** requires the model parameter.

## Our Approach vs Alternatives

### What We Do (Explicit):
```python
# Always specify model in config
model = "phi3:mini"
requests.post(url, json={"model": model, ...})
```

**Pros:**
- ✅ Clear and explicit
- ✅ Easy to switch models
- ✅ No surprises
- ✅ Works with any model

### Alternative (Environment Variable):
```bash
export OLLAMA_MODEL="phi3:mini"
# Then code could read from env
```

**Pros:**
- Can change without editing config
**Cons:**
- Less visible
- Easy to forget what's set

### Alternative (Hardcoded):
```python
# Hardcode in code
model = "phi3:mini"
```

**Pros:**
- Simple
**Cons:**
- ❌ Need to edit code to change models
- ❌ Not flexible

## Recommendation

**Use config file (what we're doing)** - Best balance of:
- Flexibility (easy to change)
- Clarity (visible in config)
- No code changes needed

## Quick Reference

### Check your model name:
```bash
ollama list
```

### Update config:
```yaml
# config/settings.yaml
llm:
  ollama:
    model: "phi3:mini"  # Use exact name from 'ollama list'
```

### Restart app:
```bash
# Stop and restart both services
python main_api.py
streamlit run app_streamlit.py
```

## Debugging

### If you get "model not found":

1. **Check exact model name:**
   ```bash
   ollama list
   ```

2. **Verify config matches:**
   ```bash
   cat config/settings.yaml | grep model
   ```

3. **Test model directly:**
   ```bash
   ollama run phi3:mini "test"
   ```

4. **Check Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

---

**TL;DR:** We call Ollama's REST API and **must** specify the model name. Use the exact name from `ollama list` in your config file.