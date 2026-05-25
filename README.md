---
title: RAG Chatbot Builder
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# RAG Chatbot Builder

Upload documents, build bots, and chat with RAG — one Docker Space (FastAPI + static UI + Qdrant).

## Space secrets

Set **OPENROUTER_API_KEY** in Space settings (Repository secrets).

## Demo notes

- First load after sleep may take ~30 seconds (cold start).
- Uploaded documents are **not persisted** on the free tier when the Space restarts.

See [DEPLOY_HF.md](./DEPLOY_HF.md) for full deployment steps.
