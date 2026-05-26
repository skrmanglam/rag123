# 🎯 Model Configuration Guide

## Quick Answer

**You need to specify which model to use** in the configuration file. The code will then call that specific model from Ollama.

## ✅ You're Already Set Up!

Since you have `phi3` running on Ollama, I've already updated your config to use it:

**File: `config/settings.yaml`**
```yaml
llm:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "phi3"  # ← Your model
```

**That's it!** The app will now use phi3 automatically.

## 🔄 How It Works

1. **You specify the model** in `config/settings.yaml`
2. **The app calls that model** via Ollama API
3. **Ollama handles the rest** (loading, inference, etc.)

## 📝 Changing Models

### Check what models you have:
```bash
ollama list
```

### To use a different model:

**Option 1: Edit config file**
```yaml
# config/settings.yaml
llm:
  ollama:
    model: "mistral"  # Change to any installed model
```

**Option 2: Pull and use a new model**
```bash
# Pull a new model
ollama pull llama3.2

# Update config
# Change model: "phi3" to model: "llama3.2"

# Restart your app
```

## 🎨 Available Models

You can use **any model** you have installed in Ollama:

### Check installed models:
```bash
ollama list
```

### Popular options:
- `phi3` - Fast, efficient (what you're using!)
- `llama3.2` - Great balance
- `mistral` - High quality
- `gemma2` - Google's model
- `codellama` - For code tasks
- `llama3.1:8b` - Larger, better reasoning

### Install a new model:
```bash
ollama pull <model-name>
```

## 🔧 Configuration Examples

### Using phi3 (your current setup):
```yaml
llm:
  provider: "ollama"
  ollama:
    model: "phi3"
```

### Using llama3.2:
```yaml
llm:
  provider: "ollama"
  ollama:
    model: "llama3.2"
```

### Using a specific version:
```yaml
llm:
  provider: "ollama"
  ollama:
    model: "llama3.2:3b"  # Specific size
```

## 🎯 Per-Bot Model Selection (Future Enhancement)

Currently, **all bots use the same model** specified in config.

If you want different bots to use different models, you could:

1. **Option A**: Change config and restart app
2. **Option B**: Modify the code to allow per-bot model selection (future feature)

## 💡 Best Practices

### For Speed:
```yaml
model: "phi3"  # Fast and efficient
```

### For Quality:
```yaml
model: "llama3.1:8b"  # Better reasoning
```

### For Code:
```yaml
model: "codellama"  # Specialized for code
```

## 🔍 Verifying Your Setup

### Check if phi3 is installed:
```bash
ollama list | grep phi3
```

### Test phi3 directly:
```bash
ollama run phi3 "Hello, how are you?"
```

### Check your config:
```bash
cat config/settings.yaml | grep -A 3 "ollama:"
```

Should show:
```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "phi3"
```

## 🚀 You're Ready!

Your setup is configured to use **phi3**. Just run:

```bash
python main_api.py
streamlit run app_streamlit.py
```

The app will automatically use phi3 for all responses!

## 🔄 Switching Models Later

Anytime you want to switch:

1. Pull new model: `ollama pull <model-name>`
2. Edit `config/settings.yaml`: Change `model: "phi3"` to `model: "<new-model>"`
3. Restart your app

## ❓ FAQ

**Q: Can I use multiple models at once?**
A: Not in the current version. All bots use the model specified in config.

**Q: Do I need to restart the app when changing models?**
A: Yes, restart both FastAPI and Streamlit.

**Q: Can I use models not from Ollama?**
A: Yes! Change `provider` to `"openai"` or `"openai_compatible"` in config.

**Q: How do I know which model is best?**
A: Try a few! phi3 is great for speed, llama3.2 for balance, mistral for quality.

## 📊 Model Comparison

| Model | Your Setup | Speed | Quality | RAM |
|-------|------------|-------|---------|-----|
| phi3 | ✅ Current | ⚡⚡⚡ | ⭐⭐⭐ | 4GB |
| llama3.2 | Available | ⚡⚡ | ⭐⭐⭐⭐ | 8GB |
| mistral | Available | ⚡⚡ | ⭐⭐⭐⭐⭐ | 8GB |

---

**TL;DR: You're all set with phi3! Just run the app and it will use your model automatically.** 🎉