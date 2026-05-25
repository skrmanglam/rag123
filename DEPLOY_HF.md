# Deploy to Hugging Face Spaces (Docker)

One container runs **Qdrant + FastAPI + static UI** on port **7860**.

## Prerequisites

1. [Hugging Face](https://huggingface.co) account
2. Create a **Docker** Space (e.g. `yourname/ragbot`)
3. [OpenRouter](https://openrouter.ai) API key for the LLM

## Space secrets

In the Space **Settings → Repository secrets**, add:

| Secret | Description |
|--------|-------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |

## Deploy

```bash
git remote add space https://huggingface.co/spaces/YOURNAME/SPACENAME
git push space main
```

Or connect the Space to this GitHub repo in the HF UI.

## Local Docker test

```bash
docker build -t rag123-hf .
docker run --rm -p 7860:7860 -e OPENROUTER_API_KEY=sk-or-... rag123-hf
```

The last argument **`rag123-hf`** is the image name (required). First startup can take 1–2 minutes while the embedding model loads.

Open http://localhost:7860

## Notes

- **Cold start**: free Spaces sleep after inactivity (~30s wake).
- **No persistence**: Qdrant data, SQLite, and uploads reset when the Space restarts.
- **LLM**: `config/settings.yaml` uses OpenRouter via `openai_compatible`.
- **UI**: served from `static/` at `/` (no separate Netlify deploy).
