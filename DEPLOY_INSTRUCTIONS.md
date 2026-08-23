# Deployment Instructions

## For Judges/Local Testing

### Quick Demo (5 minutes)

```bash
# 1. Clone
git clone https://github.com/monikanimmana/Agent-Readable-Catalog.git
cd Agent-Readable-Catalog

# 2. Setup
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

# 3. Get API Keys (Free)
# Razorpay: https://dashboard.razorpay.com/app/keys (test mode)
# Gemini: https://makersuite.google.com/app/apikey

# 4. Configure
cp .env.example .env
# Edit .env and paste your keys

# 5. Seed Database
python seed.py

# 6. View Guardrails in Action
python test_guardrails.py

# 7. View Failure Cases
python demo_failures.py

# 8. Run Server (for API testing)
python main.py
# Then in another terminal:
# curl http://localhost:8000/audit-log
```

---

## Key Demo Commands

### Show Data
```bash
python -c "
from database import SessionLocal, init_db
from sqlalchemy import text
init_db()
db = SessionLocal()
result = db.execute(text('SELECT id, name, price, stock FROM products LIMIT 5')).fetchall()
for row in result:
    print(f'  {row[0]}: {row[1]} - ₹{row[2]}, Stock: {row[3]}')
db.close()
"
```

### Show Guardrails
```bash
python test_guardrails.py
```

### Show Failures
```bash
python demo_failures.py
```

### Show Audit Trail
```bash
python -c "
from database import SessionLocal, init_db
from audit import get_audit_logs
init_db()
db = SessionLocal()
logs = get_audit_logs(db, limit=5)
for log in logs:
    print(f'{log.action_type}: {log.status}')
db.close()
"
```

### Start API Server
```bash
python main.py
```

Then in another terminal:
```bash
# Search products
curl "http://localhost:8000/search?query=shirt&max_price=1000"

# View audit log
curl "http://localhost:8000/audit-log"

# Chat with agent (requires real Gemini key)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want a blue shirt", "budget": 500}'
```

---

## Troubleshooting

### Error: "GEMINI_API_KEY not found"
→ Create .env file and add your Gemini API key

### Error: "Authentication failed" (Razorpay)
→ This is expected with placeholder keys, use real test keys from dashboard

### Error: "database is locked"
→ Delete catalog.db and run python seed.py again

### Module not found errors
→ Make sure venv is activated:
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

---

## Project Structure

```
Agent-Readable-Catalog/
├── main.py                          # FastAPI server + Gemini agent
├── database.py                      # SQLAlchemy models
├── schemas.py                       # Pydantic models
├── search.py                        # Product search
├── audit.py                         # Audit logging
├── razorpay_service.py              # Razorpay + guardrails
├── seed.py                          # Seed database
│
├── requirements.txt                 # Dependencies
├── .env.example                     # Config template
├── .gitignore                       # Git ignore
│
├── README.md                        # Full documentation
├── QUICK_START.md                   # Setup guide
├── FEATURES_COMPLETED.md            # Feature checklist
├── JUDGE_DEMO.md                    # Demo walkthrough
├── PROJECT_SUMMARY.md               # Project overview
├── DEPLOY_INSTRUCTIONS.md           # This file
│
├── test_search.py                   # Search tests
├── test_guardrails.py               # Guardrail tests
├── demo_failures.py                 # Failure demo
└── test_api.py                      # API tests
```

---

## File Tour for Judges

### 1. Core Application
- **main.py** - FastAPI + Gemini agent (tool definitions at lines 75-130)
- **razorpay_service.py** - Guardrails in code (lines 60-130)
- **database.py** - SQLAlchemy models (Product, AuditLog)

### 2. Guardrails (Critical)
Show: `razorpay_service.py`
- Lines 69-79: Product existence check
- Lines 82-95: Stock check (MANDATORY)
- Lines 97-112: Quantity validation
- Lines 115-130: Budget constraint check

### 3. Audit Trail
Show: `main.py` lines 208-224 (GET /audit-log endpoint)
Show: `audit.py` (log_action, get_audit_logs functions)

### 4. Tests
Show: `test_guardrails.py` (5 test cases)
Show: `demo_failures.py` (3 failure scenarios)
Show: `test_search.py` (search functionality)

---

## What's In the Repository

### Source Code (8 files)
✅ `main.py` - FastAPI server (320 lines)
✅ `database.py` - Data models (55 lines)
✅ `schemas.py` - API schemas (60 lines)
✅ `search.py` - Search logic (65 lines)
✅ `audit.py` - Audit logging (40 lines)
✅ `razorpay_service.py` - Payment + guardrails (150 lines)
✅ `seed.py` - Database seed (100 lines)
✅ `requirements.txt` - Dependencies

### Tests (4 files)
✅ `test_guardrails.py` - Guardrail verification
✅ `demo_failures.py` - Failure case demonstration
✅ `test_search.py` - Search functionality
✅ `test_api.py` - API endpoints

### Documentation (6 files)
✅ `README.md` - Complete technical docs
✅ `QUICK_START.md` - 5-minute setup
✅ `FEATURES_COMPLETED.md` - Feature checklist
✅ `JUDGE_DEMO.md` - Demo guide
✅ `PROJECT_SUMMARY.md` - Project overview
✅ `DEPLOY_INSTRUCTIONS.md` - This file

### Configuration (3 files)
✅ `.env.example` - Environment template
✅ `.gitignore` - Git ignore
✅ `requirements.txt` - Python packages

---

## All 8 Features Implemented

| # | Feature | Location | Test |
|---|---------|----------|------|
| 1 | Data Models + Seed (18 products) | database.py, seed.py | python seed.py |
| 2 | Search/Retrieval (keyword + filters) | search.py | python test_search.py |
| 3 | Agent Tools (4 Gemini tools) | main.py:75-130 | curl /chat |
| 4 | Guardrails (stock, budget, qty) | razorpay_service.py:60-130 | python test_guardrails.py |
| 5 | Gemini Agent Loop | main.py:232-320 | curl /chat |
| 6 | Razorpay Integration (test mode) | razorpay_service.py | With real keys |
| 7 | Failure Cases (out-of-stock, budget) | demo_failures.py | python demo_failures.py |
| 8 | Audit Trail Endpoint | main.py:208-224, audit.py | curl /audit-log |

---

## GitHub Repository

**URL:** https://github.com/monikanimmana/Agent-Readable-Catalog

**Branch:** main

**Commits:**
```
6f49240 📋 Project summary
dabe378 📽️ Judge demo guide
1dc19ba 📚 Documentation
cb4f366 ✨ Features 6-8: Razorpay + failures + audit
2f6aaac ✨ Feature 5: Gemini agent loop
dd48fd2 ✨ Features 3-4: Tools + guardrails
b20bfad ✨ Feature 2: Search layer
2739685 ✨ Feature 1: Data models + seed
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/search` | GET | Search products (direct) |
| `/chat` | POST | Chat with agent |
| `/audit-log` | GET | View audit trail |

---

## Performance Specifications

- **Search**: O(n) on 18 products = instant
- **Guardrails**: O(1) code checks
- **Database**: SQLite, single file
- **API**: FastAPI, async capable
- **Agent**: Synchronous ~1-2s per request

---

## Security Notes

✅ **Test Mode Only** - rzp_test_* keys only (production keys rejected)
✅ **No Hardcoding** - All secrets in .env
✅ **Code Guardrails** - Not prompt-based
✅ **Audit Trail** - All actions logged
✅ **Error Handling** - Graceful failures

---

## Next Steps (Production)

1. PostgreSQL database
2. Redis caching
3. JWT authentication
4. Rate limiting
5. Docker deployment
6. Kubernetes orchestration
7. CI/CD pipeline
8. Monitoring & alerting

---

## Questions for Judges

**Q: How do guardrails prevent agent bypass?**
A: They're in code (`razorpay_service.py`), before Razorpay API. Agent can't see or affect them.

**Q: Where are failures logged?**
A: Audit trail at `/audit-log`. Search for `status="blocked"`.

**Q: Can this scale to 1M products?**
A: Yes - switch to PostgreSQL, add Redis caching, implement pagination.

**Q: Is Razorpay integration real?**
A: Yes - it's test mode (rzp_test_*). Real cards not charged.

---

## Contact

For questions about this project, refer to:
- README.md for technical details
- JUDGE_DEMO.md for demo walkthrough
- PROJECT_SUMMARY.md for architecture overview

---

**Status: Ready for Judges Demo** ✅
