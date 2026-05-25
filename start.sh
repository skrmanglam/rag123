#!/bin/bash


# Local RAG Chatbot Builder - Startup Script
# This script helps you start all required services


set -e


echo "=================================="
echo "RAG Chatbot Builder - Startup"
echo "=================================="
echo ""


# Check if .env file exists
if [ ! -f .env ]; then
   echo "⚠️  .env file not found!"
   echo "Creating .env from .env.example..."
   cp .env.example .env
   echo "✅ Created .env file"
fi


# Source .env file
if [ -f .env ]; then
   export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true
fi


# Check LLM provider from settings.yaml
LLM_PROVIDER=$(grep -A 1 "^llm:" config/settings.yaml | grep "provider:" | awk '{print $2}' | tr -d '"')


echo "LLM Provider: $LLM_PROVIDER"


# Only check for OpenAI API key if using OpenAI
if [ "$LLM_PROVIDER" = "openai" ]; then
   if [ -z "$OPENAI_API_KEY" ]; then
       echo "❌ OPENAI_API_KEY is not set!"
       echo "Please set it in .env file or export it:"
       echo "  export OPENAI_API_KEY='your-key-here'"
       exit 1
   fi
   echo "✅ OPENAI_API_KEY is set"
elif [ "$LLM_PROVIDER" = "ollama" ]; then
   echo "✅ Using Ollama (local LLM)"
   echo "   Make sure Ollama is running: ollama serve"
elif [ "$LLM_PROVIDER" = "openai_compatible" ]; then
   if [ -z "$OPENROUTER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
       echo "⚠️  OPENROUTER_API_KEY is not set (required for OpenRouter)"
   else
       echo "✅ OpenRouter / compatible API key is set"
   fi
else
   echo "✅ Using $LLM_PROVIDER"
fi
echo ""


# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
   echo "❌ Docker is not running!"
   echo "Please start Docker and try again."
   exit 1
fi


echo "✅ Docker is running"
echo ""


# Start Qdrant
echo "Starting Qdrant..."
docker-compose up -d


# Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."
for i in {1..30}; do
   if curl -s http://localhost:6333/ > /dev/null 2>&1; then
       echo "✅ Qdrant is ready"
       break
   fi
   if [ $i -eq 30 ]; then
       echo "❌ Qdrant failed to start"
       exit 1
   fi
   sleep 1
done


echo ""
echo "=================================="
echo "Activating Virtual Environment"
echo "=================================="
echo ""

# Activate standard venv
if [ -d "venv" ]; then
   echo "Activating virtual environment..."
   source venv/bin/activate
   echo "✅ Virtual environment activated"
else
   echo "❌ Virtual environment 'venv' not found!"
   echo "Please run the setup script first."
   exit 1
fi


echo ""
echo "=================================="
echo "Starting Application Services"
echo "=================================="
echo ""


# Function to cleanup on exit
cleanup() {
   echo ""
   echo "Shutting down services..."
   kill $FASTAPI_PID 2>/dev/null || true
   echo "Services stopped."
}


trap cleanup EXIT INT TERM


# Start FastAPI in background
echo "Starting FastAPI server..."
python main_api.py > fastapi.log 2>&1 &
FASTAPI_PID=$!


# Wait for FastAPI to be ready
echo "Waiting for FastAPI to be ready..."
for i in {1..30}; do
   if curl -s http://localhost:8000/health > /dev/null 2>&1; then
       echo "✅ FastAPI is ready at http://localhost:8000"
       break
   fi
   if [ $i -eq 30 ]; then
       echo "❌ FastAPI failed to start"
       echo "Check fastapi.log for errors"
       exit 1
   fi
   sleep 1
done


echo ""
echo "=================================="
echo "✅ All Services Running!"
echo "=================================="
echo ""
echo "🌐 Web UI:        http://localhost:8000"
echo "🔌 FastAPI:       http://localhost:8000"
echo "📚 API Docs:      http://localhost:8000/docs"
echo "🗄️  Qdrant:       http://localhost:6333"
echo ""
echo "Logs: tail -f fastapi.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="
echo ""


# Wait for user interrupt
wait
