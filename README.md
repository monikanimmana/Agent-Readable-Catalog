# Razorpay Agent Catalog - Full Stack Application

A complete full-stack hackathon project for Razorpay's "AI Growth & Agentic Commerce" track. An AI shopping agent (powered by Gemini) that talks to customers, searches products, recommends items, and completes real purchases using Razorpay's test-mode APIs — with every action explainable, bounded to real stock/price checks, and logged in a visible audit trail.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ User Chat Interface (Frontend)                          │
└────────────────────┬────────────────────────────────────┘
                     │ POST /chat
                     ▼
┌─────────────────────────────────────────────────────────┐
│ FastAPI Backend                                         │
│  ├─ Gemini Agent Reasoning Loop                        │
│  ├─ Tool Definitions (search, stock, price, purchase)  │
│  ├─ Guardrails (stock check, budget check)             │
│  └─ Razorpay Integration (test mode)                   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   ┌─────────┐          ┌──────────────┐
   │ SQLite  │          │ Razorpay API │
   │ (local) │          │ (test mode)  │
   └─────────┘          └──────────────┘
```

## Tech Stack

- **FastAPI** - Python web framework
- **Gemini API** - AI agent reasoning with function calling
- **Razorpay Python SDK** - Payment processing (test mode only)
- **SQLAlchemy** - ORM for database
- **SQLite** - Local persistence
- **Pydantic** - Request/response validation

## Features

✅ **Product Catalog** - 18 realistic products across 10+ categories  
✅ **AI Agent** - Gemini-powered reasoning with tool calling  
✅ **Guardrails** - Stock and budget checks in code (not just prompts)  
✅ **Razorpay Integration** - Test-mode orders with payment simulation  
✅ **Audit Trail** - Complete logging of all actions  
✅ **Failure Handling** - Both out-of-stock and declined payment scenarios  

## Setup

### 1. Get API Keys

#### Razorpay (Test Mode)
- Go to https://dashboard.razorpay.com/app/keys
- Copy your **Test Key ID** and **Test Key Secret**
- They should look like: `rzp_test_xxxxxxxxxxxx`

#### Gemini API
- Go to https://makersuite.google.com/app/apikey
- Create a new API key

### 2. Install Python & Dependencies

```bash
# Clone this repo
cd razorpay-agent-catalog

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys (optional for demo mode)
# RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID
# RAZORPAY_KEY_SECRET=rzp_test_YOUR_KEY_SECRET
# GEMINI_API_KEY=your_gemini_api_key
```

**Note:** The application now runs in **demo mode** without a real Gemini API key. It uses realistic mock responses that demonstrate the full functionality. To enable real Gemini AI reasoning, add a valid API key to the `.env` file.

### 4. Seed Database

```bash
python seed.py
```

Output:
```
✅ Seeded 18 products into the database
```

### 5. Run Backend

```bash
python main.py
```

The backend will start at `http://localhost:8001`

Access interactive docs: `http://localhost:8001/docs`

**Status Indicators:**
- ✅ Demo Mode (no real Gemini API): Full chat functionality with mock responses
- 🤖 Real Mode (Gemini API key configured): AI reasoning with real agent


## API Endpoints

### Health Check
```bash
GET http://localhost:8001/health
```

### Search Products (Direct)
```bash
GET http://localhost:8001/search?query=shirt&max_price=1000&size=M
```

### Chat with Agent
```bash
POST http://localhost:8001/chat
Content-Type: application/json

{
  "message": "I want to buy a blue shirt under 1000 rupees",
  "budget": 1000
}
```

### Get Audit Trail
```bash
GET http://localhost:8001/audit-log
GET http://localhost:8001/audit-log?action_type=search&status=success&limit=50
```

## Demo Scenarios

### Quick Test (Demo Mode - No API Keys Required!)

Just start the server and try:

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find me a blue shirt",
    "budget": 3000
  }'
```

Response (with mock agent):
```json
{
  "reply": "I found 3 items matching 'blue':\n\n1. **Classic Blue Shirt** - ₹1,299\nSize: M, L, XL | In Stock\n\n...",
  "tool_calls": ["search_products"]
}
```

All actions are logged to the audit trail even in demo mode!

### Scenario 1: Successful Purchase

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to buy a blue wireless headphone",
    "budget": 4500
  }'
```

Expected flow:
1. Agent searches for "wireless headphone"
2. Checks stock on product #2 (Wireless Bluetooth Headphones)
3. Gets price (₹3999)
4. Initiates purchase (within budget)
5. Razorpay order created ✅

### Scenario 2: Out of Stock

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want running shoes"
  }'
```

Expected flow:
1. Agent searches for "running shoes"
2. Finds product #4 (Running Shoes - Pro Edition)
3. Checks stock → 0 available
4. Agent explains product is out of stock ✅
5. Audit log shows "blocked" status

### Scenario 3: Budget Exceeded

```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a smart watch",
    "budget": 3000
  }'
```

Expected flow:
1. Agent searches for "smart watch"
2. Finds product #7 (Smart Watch - ₹5999)
3. Checks stock ✓
4. Gets price ✓
5. Budget check fails (₹5999 > ₹3000 budget)
6. Purchase blocked ✅

### Scenario 4: Test Payment Simulation

To test payment success/decline:

#### Success Card (Test Mode)
- Card Number: `4111 1111 1111 1111`
- Expiry: Any future date (e.g., 12/25)
- CVV: Any 3 digits

#### Decline Card (Test Mode)
- Card Number: `4222 2222 2222 2222`
- Expiry: Any future date
- CVV: Any 3 digits

## Guardrails (Bounded & Gated)

Every guardrail check is **in-code** and **logged**, never relying on prompting:

### Guardrail 1: Stock Check
```python
# In razorpay_service.py - initiate_purchase()
if not stock_check["in_stock"]:
    return {"status": "blocked", "message": "Out of stock"}
    # Also logged as audit entry with status="blocked"
```

### Guardrail 2: Budget Constraint
```python
# In razorpay_service.py - initiate_purchase()
if budget_constraint is not None and total_price > budget_constraint:
    return {"status": "blocked", "message": "Exceeds budget"}
    # Also logged
```

### Guardrail 3: Quantity Check
```python
# In razorpay_service.py - initiate_purchase()
if quantity > stock_check["quantity"]:
    return {"status": "blocked", "message": "Not enough stock"}
    # Also logged
```

All blocked actions create an audit trail entry with `status="blocked"` so judges can see the safety behavior in action.

## Audit Trail

Every action is logged with:
- Timestamp
- Action type (search, check_stock, get_price, initiate_purchase)
- Input parameters
- Output/result
- Status (success, failed, blocked)
- Razorpay order ID (if applicable)
- User's original message

### View Audit Trail
```bash
curl "http://localhost:8000/audit-log"
```

## File Structure

```
razorpay-agent-catalog/
├── main.py                  # FastAPI app + agent endpoint
├── database.py              # SQLAlchemy models (Product, AuditLog)
├── schemas.py               # Pydantic request/response models
├── search.py                # Product search/retrieval layer
├── audit.py                 # Audit logging functions
├── razorpay_service.py      # Razorpay integration + guardrails
├── seed.py                  # Seed database with 18 products
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Database Schema

### Products Table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    price FLOAT,
    stock INTEGER,
    category TEXT,
    variants JSON,  -- {"sizes": ["S", "M", "L"], "colors": ["red", "blue"]}
    created_at DATETIME
);
```

### Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    action_type TEXT,  -- search, check_stock, get_price, initiate_purchase, blocked, payment_failed, etc.
    input_data JSON,
    output_data JSON,
    razorpay_order_id TEXT,
    status TEXT,  -- success, failed, blocked
    user_message TEXT
);
```

## Seeded Products

The database comes pre-seeded with 18 realistic products:

1. Premium Cotton T-Shirt (₹499, stock: 25)
2. Wireless Bluetooth Headphones (₹3999, stock: 5)
3. Stainless Steel Water Bottle (₹799, stock: 45)
4. Running Shoes - Pro Edition (₹4999, stock: **0** ← out of stock demo)
5. Organic Green Tea (₹349, stock: 120)
6. Yoga Mat (₹1299, stock: 18)
7. Smart Watch Fitness Tracker (₹5999, stock: 2)
8. Bamboo Cutting Board Set (₹899, stock: 34)
9. USB-C Charging Cable (₹299, stock: 200)
10. Portable Solar Power Bank (₹2499, stock: 11)
11. Adjustable Dumbbell Set (₹8999, stock: 6)
12. Bamboo Toothbrush Pack (₹199, stock: 67)
13. Leather Messenger Bag (₹6999, stock: 8)
14. Indoor Plant - Monstera (₹1599, stock: 12)
15. Noise-Cancelling Earplugs (₹1299, stock: **0** ← out of stock demo)
16. Mechanical Keyboard RGB (₹7499, stock: 3)
17. Sunscreen SPF 50+ (₹599, stock: 55)
18. Bluetooth Speaker (₹2299, stock: 9)

## Frontend Setup

The application includes a full-featured React frontend with a dark theme UI.

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Frontend Dev Server

```bash
npm run dev
```

The frontend will start at `http://localhost:5173` (or `5174` if port 5173 is in use).

### 3. Open in Browser

Visit: `http://localhost:5173`

The frontend will automatically connect to the backend at `http://localhost:8001`.

### Frontend Features

- **Chat Interface** - Real-time chat with the AI agent
- **Activity Feed** - Live audit trail of all actions
- **User Summary** - Total orders and spending metrics
- **Orders Page** - View purchase history
- **Dark Theme** - OLED-friendly dark UI with teal accents

### Running Both Servers

```bash
# Terminal 1: Backend
cd razorpay-agent-catalog
python main.py

# Terminal 2: Frontend
cd razorpay-agent-catalog/frontend
npm run dev
```

Both servers will run simultaneously:
- Backend: `http://localhost:8001`
- Frontend: `http://localhost:5173`

## Troubleshooting

### API Key Errors
```
ValueError: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env
```
→ Check your `.env` file has the correct keys

### Database Lock
```
sqlite3.OperationalError: database is locked
```
→ Delete `catalog.db` and run `python seed.py` again

### Gemini Rate Limit
```
google.generativeai.types.BlockedPromptException
```
→ Wait a moment and try again, or check your API quota

## Performance Notes

- Keyword search is O(n) on product count (18 items = instant)
- No embeddings or semantic search (small catalog, not needed)
- SQLite is sufficient for a hackathon demo
- Razorpay calls are synchronous (no webhooks, ~1-2 second latency)

## Next Steps (Post-Hackathon)

- [ ] Add WebSocket support for real-time updates
- [ ] Implement payment confirmation webhooks
- [ ] Add multi-turn conversation memory
- [ ] Implement semantic search with embeddings
- [ ] Add JWT authentication
- [ ] Deploy to production (PostgreSQL, Redis, Stripe/PayU)
- [ ] Build frontend UI
- [ ] Add order tracking & history

## License

MIT (Hackathon Project)

## Questions?

Reach out to the team or check the inline code comments in `main.py` and `razorpay_service.py`.

---

**Happy hacking! 🚀**
