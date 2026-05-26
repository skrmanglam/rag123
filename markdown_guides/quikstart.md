# 🚀 Quick Start Guide


Get your RAG chatbot running in 5 minutes!


## Prerequisites


- Python 3.8+
- Docker
- OpenAI API key


## Step-by-Step Setup


### 1. Install Dependencies (2 minutes)


```bash
pip install -r requirements.txt
```


### 2. Set OpenAI API Key (30 seconds)


```bash
# Copy the example env file
cp .env.example .env


# Edit .env and add your OpenAI API key
# Or export directly:
export OPENAI_API_KEY='sk-your-key-here'
```


### 3. Start Qdrant (30 seconds)


```bash
# Using Docker Compose (recommended)
docker-compose up -d


# Or using Docker directly
docker run -d -p 6333:6333 qdrant/qdrant
```


Verify Qdrant is running:
```bash
curl http://localhost:6333/
```


### 4. Test Your Setup (30 seconds)


```bash
python test_setup.py
```


You should see all tests pass ✅


### 5. Start the Application (1 minute)


**Terminal 1 - Start FastAPI:**
```bash
python main_api.py
```


**Terminal 2 - Start Streamlit:**
```bash
streamlit run app_streamlit.py
```


### 6. Create Your First Chatbot (1 minute)


1. Open browser at `http://localhost:8501`
2. Fill in bot details:
  - Name: "My First Bot"
  - Role: "hr_assistant"
  - Tone: "friendly"
  - Strictness: "strict"
3. Click "Create Bot"


### 7. Upload Documents (30 seconds)


1. Go to "📄 Upload Documents" tab
2. Upload a PDF, TXT, or MD file
3. Click "Process Documents"
4. Wait for processing to complete


### 8. Start Chatting! (30 seconds)


1. Go to "💬 Chat" tab
2. Ask a question about your documents
3. Get answers with citations!


## Example Usage


### Via Streamlit UI


1. Create bot: "HR Assistant"
2. Upload: `employee_handbook.pdf`
3. Ask: "What is the vacation policy?"
4. Get answer with source citations


### Via API


```bash
# Chat with your bot
curl -X POST http://localhost:8000/chat/hr_assistant \
 -H "Content-Type: application/json" \
 -d '{"question": "What is the vacation policy?"}'
```


## Troubleshooting


### "Connection refused to localhost:6333"
**Fix:** Start Qdrant
```bash
docker-compose up -d
```


### "OPENAI_API_KEY not set"
**Fix:** Set your API key
```bash
export OPENAI_API_KEY='your-key-here'
```


### "Module not found"
**Fix:** Install dependencies
```bash
pip install -r requirements.txt
```


## Next Steps


- Read the full [README.md](README.md) for detailed documentation
- Explore the API at `http://localhost:8000/docs`
- Customize settings in `config/settings.yaml`
- Try different bot configurations


## Need Help?


- Check [README.md](README.md) for detailed documentation
- Run `python test_setup.py` to diagnose issues
- Review error messages in terminal output


---


**Happy chatting! 🤖**

