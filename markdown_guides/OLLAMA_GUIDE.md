# 🦙 Ollama Setup & Usage Guide

## Quick Answer: Do I need to run Ollama separately?

**No!** Ollama runs automatically in the background after installation. You just need to:

1. Install Ollama once
2. Pull a model once
3. That's it! It will auto-start when needed

## 📥 Installation (One-Time Setup)

### macOS
```bash
# Download and install
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from website
# https://ollama.ai/download
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows
Download installer from: https://ollama.ai/download

## 🎯 Pull a Model (One-Time)

After installation, pull a model:

```bash
# Recommended for most users (3.2GB)
ollama pull llama3.2

# Or other options:
ollama pull phi3        # Smaller, faster (1.9GB)
ollama pull mistral     # Larger, better quality (4.7GB)
```

## ✅ That's It!

**Ollama is now ready!** It will:
- ✅ Start automatically when your app makes a request
- ✅ Run in the background
- ✅ Keep the model loaded in memory for fast responses
- ✅ Auto-restart if needed

## 🔍 Checking Ollama Status

### Is Ollama installed?
```bash
ollama --version
```

### What models do I have?
```bash
ollama list
```

### Test if Ollama is working
```bash
ollama run llama3.2 "Hello, how are you?"
```

This will:
1. Start Ollama if not running
2. Load the model
3. Generate a response
4. Keep running in background

## 🚀 Using with RAG Chatbot Builder

Once Ollama is installed and you've pulled a model:

```bash
# Just start your app - Ollama will work automatically!
python main_api.py
streamlit run app_streamlit.py
```

The app will automatically connect to Ollama at `http://localhost:11434`

## 🛠️ Advanced: Manual Control (Optional)

You usually don't need this, but if you want manual control:

### Start Ollama manually
```bash
ollama serve
```

### Stop Ollama
```bash
# On macOS/Linux
pkill ollama

# On Windows
# Use Task Manager to stop "ollama" process
```

### Check if Ollama is running
```bash
curl http://localhost:11434/api/tags
```

## 🔄 Switching Models

You can switch models anytime:

```bash
# Pull a new model
ollama pull mistral

# Update config/settings.yaml
llm:
  ollama:
    model: "mistral"  # Change this

# Restart your app
```

## 💾 Model Storage

Models are stored locally:
- **macOS**: `~/.ollama/models`
- **Linux**: `~/.ollama/models`
- **Windows**: `C:\Users\<username>\.ollama\models`

## 🗑️ Removing Models

To free up space:

```bash
# List models
ollama list

# Remove a model
ollama rm llama3.2
```

## ⚡ Performance Tips

### First Request is Slow
- **Normal!** Model loads into memory (5-30 seconds)
- Subsequent requests are fast

### Keep Ollama Running
- Ollama automatically keeps models in memory
- Unloads after 5 minutes of inactivity
- Reloads automatically when needed

### Speed Up Loading
```bash
# Keep model always loaded
ollama run llama3.2 --keepalive -1
```

## 🐛 Troubleshooting

### "Connection refused to localhost:11434"

**Solution 1: Check if Ollama is installed**
```bash
ollama --version
```

**Solution 2: Start Ollama manually**
```bash
ollama serve
```

**Solution 3: Check if port is in use**
```bash
lsof -i :11434  # macOS/Linux
netstat -ano | findstr :11434  # Windows
```

### "Model not found"

**Solution: Pull the model**
```bash
ollama pull llama3.2
```

### "Out of memory"

**Solution: Use a smaller model**
```bash
ollama pull phi3  # Only 1.9GB
```

Update config:
```yaml
llm:
  ollama:
    model: "phi3"
```

## 📊 Model Comparison

| Model | Size | RAM Needed | Speed | Quality |
|-------|------|------------|-------|---------|
| phi3 | 1.9GB | 4GB | Fast | Good |
| llama3.2 | 3.2GB | 8GB | Medium | Great |
| mistral | 4.7GB | 8GB | Medium | Excellent |
| llama3.1:8b | 4.7GB | 16GB | Slower | Excellent |

## 🎓 Summary

**You DON'T need to:**
- ❌ Run `ollama serve` manually
- ❌ Keep a terminal open for Ollama
- ❌ Start/stop Ollama with your app

**You ONLY need to:**
- ✅ Install Ollama once
- ✅ Pull a model once
- ✅ Run your app - Ollama handles the rest!

## 🔗 Resources

- [Ollama Website](https://ollama.ai)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Available Models](https://ollama.ai/library)

---

**TL;DR: Install Ollama, pull a model, forget about it - it just works!** 🎉