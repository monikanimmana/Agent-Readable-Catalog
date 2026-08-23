# Quick Start Guide

## Prerequisites

1. **Python 3.10+**
2. **API Keys** (free to create):
   - [Razorpay Test Keys](https://dashboard.razorpay.com/app/keys)
   - [Gemini API Key](https://makersuite.google.com/app/apikey)

## Installation (5 minutes)

```bash
# 1. Clone/navigate to project
cd razorpay-agent-catalog

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup environment
cp .env.example .env
# Edit .env and add your API keys

# 6. Seed database
python seed.py

# 7. Run server
python main.py
```

The server will start at `http://localhost:8000`

## Testing

### Direct API Calls

**Search Products:**
```bash
curl "http://localhost:8000/search?query=shirt&max_price=1000"
```

**View Audit Log:**
```bash
curl "http://localhost:8000/audit-log"
```

**Chat with Agent** (requires valid Gemini API key):
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a blue wireless headphone under 4500 rupees",
    "budget": 4500
  }'
```

### Interactive API Docs

Open your browser to:
```
http://localhost:8000/docs
```

This gives you Swagger UI to test all endpoints interactively.

## Demo Scenarios

### Scenario 1: Successful Search & Purchase

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me some yoga mats"
  }'
```

Expected: Agent searches, finds 1 product, explains it.

### Scenario 2: Budget Guardrail

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a smart watch",
    "budget": 3000
  }'
```

Expected: Agent finds smart watch (₹5999), realizes it exceeds budget (₹3000), rejects purchase with clear explanation.

### Scenario 3: Out of Stock Guardrail

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want running shoes"
  }'
```

Expected: Agent finds running shoes, checks stock (0 available), blocks purchase, explains product is out of stock.

## Project Structure

```
razorpay-agent-catalog/
├── main.py                 # FastAPI server + Gemini agent
├── database.py             # SQLAlchemy models
├── schemas.py              # Pydantic models
├── search.py               # Search functionality
├── audit.py                # Audit logging
├── razorpay_service.py     # Razorpay + guardrails
├── seed.py                 # Seed database
├── requirements.txt        # Dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore
├── README.md               # Full documentation
└── QUICK_START.md          # This file
```

## Key Files for Judges

### Guardrails Demo
Check `razorpay_service.py`:
- Lines 50-100: Stock check guardrail
- Lines 102-118: Budget constraint guardrail  
- Lines 120-130: Quantity validation
- **All guardrails logged to audit trail with status="blocked"**

### Audit Trail
Run this to see all logged actions:
```bash
curl "http://localhost:8000/audit-log?limit=20"
```

Each entry shows:
- `timestamp` - When the action happened
- `action_type` - What was done (search, check_stock, initiate_purchase, etc.)
- `status` - success/failed/blocked
- `input_data` - What was requested
- `output_data` - What happened
- `user_message` - Original user intent

### Agent Tool Definitions
Check `main.py` lines 75-130:
- `search_products` - Find products
- `check_stock` - Verify availability
- `get_price` - Get pricing
- `initiate_purchase` - Create order

## Troubleshooting

### Error: "GEMINI_API_KEY not found"
→ Add your key to `.env` and restart

### Error: "Authentication failed" (Razorpay)
→ This is expected with test keys from `.env.example`
→ Add real test mode keys from your Razorpay dashboard

### Error: "database is locked"
→ Delete `catalog.db` and run `python seed.py` again

### Can't import modules?
→ Make sure virtual environment is activated:
```bash
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

## Next Steps

1. Get real Razorpay test keys from dashboard
2. Get real Gemini API key
3. Update `.env` file
4. Restart server
5. Try the chat endpoint with real agent

## Production Notes

For a real deployment, you'd want to:
- Use PostgreSQL instead of SQLite
- Add Redis for caching
- Implement proper authentication
- Add rate limiting
- Use environment-based configuration
- Add comprehensive logging
- Add error tracking (Sentry)
- Use Docker for deployment

But for a hackathon demo, SQLite + synchronous calls + simple logging is perfect!

---

**Questions?** Check `README.md` for more detailed documentation.
