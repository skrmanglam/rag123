# FAQ Feature Quick Start Guide

Get your FAQ cache up and running in 5 minutes!

## Prerequisites

- RAG system already set up and running
- At least one bot created
- API server running on `http://localhost:8000`

## Quick Setup (3 Steps)

### Step 1: Prepare Your FAQ CSV

Create a CSV file with your frequently asked questions. Use this format:

```csv
question_id,question,answer,category
faq_001,What is the warranty period?,Our products come with a 2-year warranty covering all manufacturing defects.,warranty
faq_002,How do I return a product?,You can return any product within 30 days of purchase for a full refund.,returns
faq_003,What are the shipping costs?,We offer free shipping on orders over $50. Standard shipping is $5.99.,shipping
```

**Format Rules:**
- First row must be headers: `question_id,question,answer,category`
- `question_id`: Unique ID (e.g., faq_001, faq_002)
- `question`: The FAQ question
- `answer`: The pre-approved answer
- `category`: Optional grouping (e.g., warranty, returns, shipping)

### Step 2: Upload FAQ to Your Bot

**Option A: Using the Upload Script (Easiest)**

```bash
python upload_faq.py customer_support_bot my_faqs.csv
```

**Option B: Using curl**

```bash
curl -X POST "http://localhost:8000/bots/customer_support_bot/faq/upload" \
  -F "file=@my_faqs.csv"
```

**Option C: Using Streamlit UI**

1. Open Streamlit app: `streamlit run app_streamlit.py`
2. Select your bot
3. Go to "❓ FAQ Management" tab
4. Follow upload instructions

### Step 3: Test It!

**Test FAQ Matching:**

```bash
curl -X POST "http://localhost:8000/bots/customer_support_bot/faq/search" \
  -H "Content-Type: application/json" \
  -d '{"question": "How long is the warranty?"}'
```

**Chat with FAQ Cache:**

```bash
curl -X POST "http://localhost:8000/chat/customer_support_bot" \
  -H "Content-Type: application/json" \
  -d '{"question": "How long is the warranty?"}'
```

**Or use Streamlit:**
1. Go to "💬 Chat" tab
2. Ask: "How long is the warranty?"
3. Get instant FAQ-powered answer!

## How It Works

```
User Question → FAQ Cache Check → Match Found? 
                                      ↓ YES (score ≥ 0.80)
                                  Return FAQ Answer (personalized by LLM)
                                      ↓ NO (score < 0.80)
                                  Search Documents (regular RAG)
```

## Sample FAQ CSV

Download or use `sample_faq.csv` included in the project:

```csv
question_id,question,answer,category
faq_001,What is the warranty period?,Our products come with a 2-year warranty covering all manufacturing defects.,warranty
faq_002,How do I return a product?,You can return any product within 30 days of purchase for a full refund.,returns
faq_003,What are the shipping costs?,We offer free shipping on orders over $50. Standard shipping is $5.99.,shipping
faq_004,How long does shipping take?,Standard shipping takes 5-7 business days. Express shipping is 2-3 days.,shipping
faq_005,What payment methods do you accept?,We accept all major credit cards, PayPal, and Apple Pay.,payment
faq_006,Can I track my order?,Yes! You'll receive a tracking number via email once your order ships.,orders
faq_007,Do you ship internationally?,Yes, we ship to over 100 countries worldwide.,shipping
faq_008,What is your price match policy?,We match any competitor's price within 30 days of purchase.,pricing
faq_009,How do I contact customer support?,Email us at support@example.com or call 1-800-SUPPORT.,support
faq_010,Can I cancel my order?,Yes, you can cancel within 24 hours of placing the order.,orders
```

## Quick Commands

### View FAQ Stats
```bash
curl http://localhost:8000/bots/customer_support_bot/faq/stats
```

### List All FAQs
```bash
curl http://localhost:8000/bots/customer_support_bot/faq
```

### Delete All FAQs
```bash
curl -X DELETE http://localhost:8000/bots/customer_support_bot/faq
```

## Configuration

Edit `config/settings.yaml` to adjust the similarity threshold:

```yaml
faq:
  similarity_threshold: 0.80  # Default: 0.80 (80% similar)
```

**Threshold Guide:**
- **0.80-0.84** (Recommended): Balanced - catches variations while staying relevant
- **0.85-0.89**: Stricter - higher confidence matches
- **0.75-0.79**: Looser - more matches, less precise
- **0.90+**: Very strict - only near-exact matches

## Troubleshooting

### FAQ Not Matching?

**Problem:** Your question doesn't match the FAQ

**Quick Fixes:**
1. Lower threshold to 0.75 in `config/settings.yaml`
2. Test with `/faq/search` endpoint to see scores
3. Rephrase FAQ question to be more generic
4. Add multiple FAQ entries for variations

### Too Many Wrong Matches?

**Problem:** Unrelated FAQs matching

**Quick Fixes:**
1. Raise threshold to 0.85 in `config/settings.yaml`
2. Make FAQ questions more specific
3. Use categories to organize FAQs

### Upload Errors?

**Problem:** CSV file rejected

**Quick Fixes:**
1. Check CSV format (must have headers)
2. Ensure UTF-8 encoding
3. Verify no duplicate question_ids
4. Check for empty required fields

## Next Steps

1. ✅ **Upload your FAQs** - Start with 5-10 common questions
2. ✅ **Test matching** - Use `/faq/search` to verify
3. ✅ **Adjust threshold** - Fine-tune based on results
4. ✅ **Monitor usage** - Check which FAQs are being matched
5. ✅ **Expand gradually** - Add more FAQs over time

## API Reference

### Upload FAQ
```http
POST /bots/{bot_id}/faq/upload
Content-Type: multipart/form-data
Body: file=@my_faqs.csv
```

### Get Stats
```http
GET /bots/{bot_id}/faq/stats
```

### List FAQs
```http
GET /bots/{bot_id}/faq
```

### Search FAQ
```http
POST /bots/{bot_id}/faq/search
Content-Type: application/json
Body: {"question": "your question", "top_k": 3}
```

### Delete FAQs
```http
DELETE /bots/{bot_id}/faq
```

### Chat (with FAQ)
```http
POST /chat/{bot_id}
Content-Type: application/json
Body: {"question": "your question"}
```

## Benefits

✅ **Instant Answers** - FAQ lookup is 10x faster than document search  
✅ **Consistent** - Pre-approved answers for common questions  
✅ **Smart** - Handles question variations with semantic matching  
✅ **Personalized** - LLM adapts answers to user's phrasing  
✅ **Fallback** - Seamlessly searches documents if no FAQ match  
✅ **Easy** - Simple CSV upload, no complex setup  

## Full Documentation

For detailed information, see:
- **[FAQ_FEATURE.md](FAQ_FEATURE.md)** - Complete feature documentation
- **[README.md](README.md)** - Main project documentation
- **[QUICKSTART.md](QUICKSTART.md)** - General setup guide

---

**Need Help?** Check the troubleshooting section or review the full documentation.

**Made with Bob** 🤖