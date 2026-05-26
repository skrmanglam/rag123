# 🆓 100% Free & Open Source Setup Guide

This guide shows you how to run the RAG Chatbot Builder **completely free** using only open-source tools. No API keys, no cloud services, no costs!

## 🎯 What You'll Use (All FREE)

- **LLM**: Ollama (runs locally)
- **Embeddings**: sentence-transformers (runs locally)
- **Vector DB**: Qdrant (runs locally via Docker)
- **Metadata DB**: SQLite (built-in)
- **UI**: Streamlit (open source)
- **API**: FastAPI (open source)

**Total Cost: $0.00** ✨

## 📋 Prerequisites

- Python 3.8+
- Docker
- 8GB+ RAM (16GB recommended for larger models)
- ~10GB disk space for models

## 🚀 Step-by-Step Setup

### 1. Install Ollama (2 minutes)

Ollama lets you run LLMs locally for free!

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [https://ollama.ai/download](https://ollama.ai/download)

**Verify installation:**
```bash
ollama --version
```

### 2. Download a Free LLM Model (3-5 minutes)

Choose one based on your hardware:

**Recommended for most users (3.2GB):**
```bash
ollama pull llama3.2
```

**Smaller/faster option (1.9GB):**
```bash
ollama pull phi3
```

**Larger/better quality (4.7GB):**
```bash
ollama pull mistral
```

**See all available models:**
```bash
ollama list
```

### 3. Install Python Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

### 4. Start Qdrant Vector Database (30 seconds)

```bash
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:6333/
```

### 5. Configure for Free Usage (30 seconds)

The default configuration in `config/settings.yaml` is already set to use Ollama!

```yaml
llm:
  provider: "ollama"  # FREE option
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3.2"  # or "phi3", "mistral", etc.
```

No API keys needed! 🎉

### 6. Start the Application (1 minute)

**Terminal 1 - FastAPI:**
```bash
python main_api.py
```

**Terminal 2 - Streamlit:**
```bash
streamlit run app_streamlit.py
```

### 7. Create Your First Free Chatbot! (2 minutes)

1. Open `http://localhost:8501`
2. Create a bot (no API key required!)
3. Upload documents
4. Start chatting - all processing happens locally!

## 🎨 Available Free Models

### Small & Fast (Good for laptops)
- **phi3** (1.9GB) - Microsoft's efficient model
- **gemma2:2b** (1.6GB) - Google's compact model

### Balanced (Recommended)
- **llama3.2** (3.2GB) - Meta's latest, great quality
- **mistral** (4.7GB) - Excellent performance

### Large & Powerful (Need 16GB+ RAM)
- **llama3.1:8b** (4.7GB) - Better reasoning
- **mixtral** (26GB) - Best quality

### Switch models anytime:
```bash
# Download new model
ollama pull mistral

# Update config/settings.yaml
llm:
  ollama:
    model: "mistral"

# Restart the app
```

## 💡 Performance Tips

### For Better Speed:
1. Use smaller models (phi3, gemma2:2b)
2. Reduce `max_tokens` in config
3. Use fewer chunks (`top_k: 3`)

### For Better Quality:
1. Use larger models (llama3.1:8b, mixtral)
2. Increase `top_k` to 8-10
3. Lower temperature (0.1)

### For Low RAM:
```bash
# Use quantized models
ollama pull llama3.2:q4_0  # 4-bit quantization
```

## 🔧 Troubleshooting

### "Ollama connection refused"

**Check if Ollama is running:**
```bash
ollama list
```

**If not running, start it:**
```bash
ollama serve
```

### "Model not found"

**Pull the model:**
```bash
ollama pull llama3.2
```

### "Out of memory"

**Use a smaller model:**
```bash
ollama pull phi3
```

Then update `config/settings.yaml`:
```yaml
llm:
  ollama:
    model: "phi3"
```

### Slow responses

**Normal for first query** - model loads into memory
**Subsequent queries** - should be faster

**Speed up:**
- Use smaller model
- Reduce max_tokens
- Keep Ollama running in background

## 📊 Comparison: Free vs Paid

| Feature | Free (Ollama) | Paid (OpenAI) |
|---------|---------------|---------------|
| Cost | $0 | ~$0.002/1K tokens |
| Privacy | 100% local | Sent to cloud |
| Speed | Depends on hardware | Fast |
| Quality | Good-Excellent | Excellent |
| Setup | 5 minutes | 1 minute |
| Internet | Not required | Required |

## 🌟 Advantages of Free Setup

✅ **Zero cost** - No API fees ever
✅ **Complete privacy** - Data never leaves your machine
✅ **No rate limits** - Use as much as you want
✅ **Works offline** - No internet needed after setup
✅ **Full control** - Choose any model, customize anything
✅ **No vendor lock-in** - Switch models anytime

## 🎓 Advanced: Using Other Free LLM Providers

### LM Studio (GUI for local models)
1. Download from [lmstudio.ai](https://lmstudio.ai)
2. Load a model
3. Start local server
4. Update config:
```yaml
llm:
  provider: "openai_compatible"
  openai_compatible:
    base_url: "http://localhost:1234/v1"
    model: "local-model"
```

### vLLM (High-performance inference)
```bash
# Install vLLM
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.2-3B

# Update config to use openai_compatible provider
```

### GPT4All (Another local option)
Similar to Ollama, download from [gpt4all.io](https://gpt4all.io)

## 📈 Scaling Your Free Setup

### Multiple Users
- Run on a server with good CPU/GPU
- Use larger models for better quality
- Consider quantized models for efficiency

### Production Use
- Use Docker for deployment
- Set up reverse proxy (nginx)
- Monitor with Prometheus/Grafana (also free!)

### GPU Acceleration
If you have an NVIDIA GPU:
```bash
# Ollama automatically uses GPU if available
# Check with:
ollama run llama3.2 --verbose
```

## 🎉 You're All Set!

You now have a **completely free, private, and powerful** RAG chatbot system running locally!

**Next steps:**
- Upload your documents
- Create specialized bots
- Experiment with different models
- Share with your team (all free!)

## 🤝 Community Models

Explore thousands of free models at:
- [Ollama Library](https://ollama.ai/library)
- [Hugging Face](https://huggingface.co/models)

## 📚 Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [sentence-transformers](https://www.sbert.net/)

---

**Remember: This entire setup costs $0 and runs 100% locally! 🎉**