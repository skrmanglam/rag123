#!/bin/bash


# Start the RAG Chatbot Web Interface
# This script starts the FastAPI server with the new HTML/JS frontend


echo "🚀 Starting RAG Chatbot Web Interface..."
echo ""
echo "The web interface will be available at:"
echo "  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""


# Start FastAPI server
python main_api.py
