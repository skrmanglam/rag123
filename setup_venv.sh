#!/bin/bash


# Setup script for creating a virtual environment and installing dependencies


echo "=================================="
echo "RAG Chatbot Builder - Setup"
echo "=================================="
echo ""


# Check if venv already exists
if [ -d "venv" ]; then
   echo "⚠️  Virtual environment 'venv' already exists!"
   read -p "Do you want to recreate it? (y/n) " -n 1 -r
   echo ""
   if [[ $REPLY =~ ^[Yy]$ ]]; then
       echo "Removing existing venv..."
       rm -rf venv
   else
       echo "Using existing venv..."
       source venv/bin/activate
       echo "✅ Virtual environment activated"
       exit 0
   fi
fi


# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv


if [ $? -ne 0 ]; then
   echo "❌ Failed to create virtual environment"
   echo "Make sure python3-venv is installed:"
   echo "  Ubuntu/Debian: sudo apt install python3-venv"
   echo "  macOS: Should be included with Python"
   exit 1
fi


echo "✅ Virtual environment created"
echo ""


# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate


echo "✅ Virtual environment activated"
echo ""


# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip


echo ""


# Install requirements
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt


if [ $? -ne 0 ]; then
   echo "❌ Failed to install dependencies"
   exit 1
fi


echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Virtual environment is ready at: ./venv"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate when done:"
echo "  deactivate"
echo ""
echo "Next steps:"
echo "1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
echo "2. Pull a model: ollama pull llama3.2"
echo "3. Start Qdrant: docker-compose up -d"
echo "4. Run the app: python main_api.py"
echo "=================================="