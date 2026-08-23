# Judge Demo Guide

This guide walks judges through demonstrating all 8 features of the Razorpay Agent Catalog backend.

---

## 🎯 What This Demo Shows

### Problem Statement
Build a backend where an AI agent can:
1. Search a product catalog
2. Reason about purchases
3. Execute test-mode Razorpay transactions
4. **With every money-touching action explainable, bounded in code (not just prompted), and logged**

### Solution
A FastAPI backend with:
- ✅ Gemini AI agent for reasoning
- ✅ Guardrails in CODE (stock checks, budget checks)
- ✅ Complete audit trail
- ✅ Safe, reversible test-mode Razorpay integration

---

## 📋 Demo Flow (10 minutes)

### Part 1: Show the Data (2 min)

**Terminal 1:** Show the seeded products
```bash
cd razorpay-agent-catalog
python -c "
from database import SessionLocal, init_db
from sqlalchemy import text

init_db()
db = SessionLocal()
products = db.execute(text('SELECT id, name, price, stock FROM products LIMIT 5')).fetchall()
print('Sample Products:')
for p in products:
    print(f'  ID {p[0]}: {p[1]} - ₹{p[2]}, Stock: {p[3]}')
db.close()
"
```

Expected output:
```
Sample Products:
  ID 1: Premium Cotton T-Shirt - ₹499.0, Stock: 25
  ID 2: Wireless Bluetooth Headphones - ₹3999.0, Stock: 5
  ID 3: Stainless Steel Water Bottle - ₹799.0, Stock: 45
  ID 4: Running Shoes - Pro Edition - ₹4999.0, Stock: 0
  ID 7: Smart Watch Fitness Tracker - ₹5999.0, Stock: 2
```

**Point out:** Product 4 has stock=0 (for out-of-stock demo), Product 7 is expensive (for budget demo)

---

### Part 2: Show the Guardrails Work (3 min)

**Terminal 1:** Run the guardrails test
```bash
python test_guardrails.py
```

Expected output:
```
✅ Correctly blocked non-existent product
✅ Correctly blocked out-of-stock product
✅ Correctly blocked purchase exceeding budget
✅ Correctly blocked quantity exceeding stock
✅ Guardrails passed, would call Razorpay API with valid keys
```

**What judges see:**
- Guardrails are IN CODE (`razorpay_service.py`)
- Not just prompting the AI
- Every block prevents a Razorpay API call
- Clear, testable safety

---

### Part 3: Show the Failure Cases (2 min)

**Terminal 1:** Run the failure demo
```bash
python demo_failures.py
```

Expected output:
```
[CASE 1] Out of Stock Product
  Status: blocked
  Message: Product 'Running Shoes - Pro Edition' is out of stock
  ✅ Correctly BLOCKED - No call to Razorpay API
  📋 Audit Log Entry Created: ...

[CASE 2] Budget Constraint Exceeded
  Status: blocked
  Message: Purchase blocked: Total price ₹5999.00 exceeds budget ₹4000.00
  ✅ Correctly BLOCKED - Budget check enforced in code

[CASE 3] Quantity Exceeds Available Stock
  Status: blocked
  Message: Only 45 units of 'Stainless Steel Water Bottle' available, but 100 requested
  ✅ Correctly BLOCKED - Quantity validation enforced
```

**What judges see:**
- Real failure cases (not fabricated)
- Clear explanations
- NO Razorpay calls for failures
- Every failure is logged

---

### Part 4: Show the Audit Trail (2 min)

**Terminal 1:** View audit logs
```bash
python -c "
from database import SessionLocal, init_db
from audit import get_audit_logs

init_db()
db = SessionLocal()
logs = get_audit_logs(db, limit=10)
print(f'Total audit entries: {len(logs)}\n')
for i, log in enumerate(logs[:5], 1):
    print(f'{i}. {log.action_type.upper()}')
    print(f'   Status: {log.status}')
    print(f'   Reason: {log.output_data.get(\"message\", \"N/A\")}')
db.close()
"
```

Expected output:
```
Total audit entries: 10+

1. INITIATE_PURCHASE
   Status: blocked
   Reason: Only 45 units of 'Stainless Steel Water Bottle' available...

2. INITIATE_PURCHASE
   Status: blocked
   Reason: Purchase blocked: Total price ₹5999.00 exceeds budget ₹4000.00

3. INITIATE_PURCHASE
   Status: blocked
   Reason: Product 'Running Shoes - Pro Edition' is out of stock
```

**What judges see:**
- Every action is logged
- Timestamps show when each happened
- Input/output captured
- Clear status (success/blocked/failed)

---

### Part 5: Show the Live API (1 min)

**Terminal 1:** Start the server
```bash
python main.py
```

Should output:
```
✅ Razorpay Agent Catalog backend started
📚 Database initialized
🤖 Gemini agent ready
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2:** Test search endpoint
```bash
curl "http://localhost:8000/search?query=shirt&max_price=1000"
```

Expected: Returns all shirts under ₹1000

**Terminal 2:** Test audit log retrieval
```bash
curl "http://localhost:8000/audit-log?limit=3"
```

Expected: JSON with last 3 audit entries

**What judges see:**
- API is running
- Endpoints respond correctly
- Data is consistent

---

## 🔍 Key Points for Judges

### 1. Non-Negotiable Requirement: In-Code Guardrails
**File to show:** `razorpay_service.py` (lines 50-130)

```python
# GUARDRAIL 1: Stock must be checked
if not stock_check["in_stock"]:
    return {"status": "blocked", "message": "Out of stock"}
    # Also logged to audit trail

# GUARDRAIL 2: Budget constraint
if budget_constraint is not None and total_price > budget_constraint:
    return {"status": "blocked", "message": "Exceeds budget"}
    # Also logged

# GUARDRAIL 3: Quantity validation
if quantity > stock_check["quantity"]:
    return {"status": "blocked", "message": "Not enough stock"}
    # Also logged
```

**Why this matters:**
- Guardrails are in CODE, not prompts
- Every blocked action is logged
- Judges can verify safety by reading code and checking audit trail
- This is what they're actually evaluating

### 2. Non-Negotiable Requirement: Audit Trail
**File to show:** Audit log data or `/audit-log` endpoint

Every entry has:
- `timestamp` - When it happened
- `action_type` - What was done (search, check_stock, initiate_purchase)
- `status` - success/blocked/failed
- `input_data` - What was requested
- `output_data` - What happened
- `user_message` - User's original intent

**Why this matters:**
- Judges can see exactly what happened
- Blocked actions are traceable
- No "hidden" failures
- Transparent decision-making

### 3. Non-Negotiable Requirement: Graceful Failure Case
**Demo:** Run `python demo_failures.py`

Shows:
- Out-of-stock product: Agent tries to buy → Guardrail blocks → Explains to user → Logged
- Budget exceeded: Agent tries to buy → Guardrail blocks → Explains to user → Logged

**Why this matters:**
- System doesn't crash on failures
- User gets clear explanations
- System can be audited for safety

---

## 📁 File Structure (for judges)

```
razorpay-agent-catalog/
├── main.py
│   ├── Lines 1-40: Setup (FastAPI, Gemini, database)
│   ├── Lines 75-130: Tool definitions (4 tools)
│   ├── Lines 149-230: Tool implementations
│   ├── Lines 232-320: Chat endpoint (agent reasoning)
│   └── Lines 208-224: Audit log endpoint
├── razorpay_service.py
│   ├── Lines 30-50: RazorpayGuardedClient init
│   ├── Lines 60-130: GUARDRAILS (3 critical checks)
│   └── Lines 140+: Razorpay API calls
├── database.py
│   ├── Product model (name, price, stock, variants)
│   └── AuditLog model (timestamp, action, status, details)
├── search.py
│   └── search_products() function
├── audit.py
│   ├── log_action() function
│   └── get_audit_logs() function
└── seed.py
    └── Seed 18 realistic products

Key Test Files:
├── test_guardrails.py - Run this to see guardrails in action
├── demo_failures.py - Run this to see failure cases
├── test_search.py - Run this to verify search works
└── test_api.py - API endpoint tests
```

---

## 🚀 Demo Script (Copy & Paste)

```bash
#!/bin/bash

echo "==============================================="
echo "Razorpay Agent Catalog - Judge Demo"
echo "==============================================="

echo -e "\n[1] Show seeded products..."
python -c "
from database import SessionLocal, init_db
from sqlalchemy import text
init_db()
db = SessionLocal()
products = db.execute(text('SELECT name, price, stock FROM products LIMIT 5')).fetchall()
for p in products:
    print(f'  {p[0]}: ₹{p[1]}, Stock: {p[3]}')
db.close()
"

echo -e "\n[2] Show guardrails in action..."
python test_guardrails.py 2>&1 | head -20

echo -e "\n[3] Show failure cases..."
python demo_failures.py 2>&1 | head -30

echo -e "\n[4] Show audit trail..."
python -c "
from database import SessionLocal
from audit import get_audit_logs
from database import init_db
init_db()
db = SessionLocal()
logs = get_audit_logs(db, limit=3)
for log in logs:
    print(f'  {log.action_type}: {log.status}')
db.close()
"

echo -e "\n[5] Start server (API will be available at http://localhost:8000)"
echo "    Run in separate terminal:"
echo "    python main.py"

echo -e "\n==============================================="
echo "✅ Demo Complete"
echo "==============================================="
```

---

## ❓ Likely Questions from Judges

### Q: "Why is this better than just prompting the AI?"
**A:** Because prompts can fail. With code guardrails:
- Stock check: Code reads database, not trusting agent
- Budget check: Code enforces maximum, agent can't override
- We have proof in the audit trail

### Q: "What if Razorpay API fails?"
**A:** Graceful:
1. Error is caught and logged
2. User sees clear error message
3. No payment is charged
4. Audit trail shows exactly what happened

### Q: "Can the agent bypass the guardrails?"
**A:** No. Guardrails are in code (`razorpay_service.py`), before Razorpay is called. Agent can't see or affect them.

### Q: "How do you know all the failures are logged?"
**A:** Check `/audit-log` endpoint - every blocked action has `status="blocked"`. Judges can count them.

### Q: "Is this production-ready?"
**A:** No, it's a hackathon demo. For production:
- Use PostgreSQL instead of SQLite
- Add Redis caching
- Implement JWT authentication
- Add rate limiting
- Deploy to cloud with monitoring

But for a 1-day hackathon, it's a perfect proof of concept.

---

## 📝 Talking Points

1. **"Bounded and Gated"** - Guardrails are in code, auditable, logged
2. **"Explainable"** - Every action logged with input/output
3. **"Real Integration"** - Actually calls Razorpay API (test mode)
4. **"Graceful Failures"** - Out-of-stock and budget scenarios work perfectly
5. **"Production Pattern"** - Architecture scales to real app

---

## ⏱️ Timing

- Part 1 (Data): 2 min
- Part 2 (Guardrails): 3 min
- Part 3 (Failures): 2 min
- Part 4 (Audit): 2 min
- Part 5 (API): 1 min
- **Total: ~10 minutes**

---

## 🎬 Show Starters

**If judges ask for a quick demo:**
```bash
# Just run these 3 commands:
python test_guardrails.py
python demo_failures.py
python -c "from database import SessionLocal; from audit import get_audit_logs; db=SessionLocal(); logs=get_audit_logs(db, limit=5); [print(f'{l.action_type}: {l.status}') for l in logs]"
```

**If they want to see the code:**
```
Show: razorpay_service.py lines 60-130 (GUARDRAILS)
Show: main.py lines 208-224 (AUDIT LOG ENDPOINT)
Show: demo_failures.py (COMPLETE FAILURE DEMONSTRATION)
```

---

## ✅ Checklist for Demo Day

- [ ] Virtual environment activated
- [ ] `.env` file created with test keys
- [ ] Database seeded (`python seed.py` run)
- [ ] Catalog.db exists (confirms seed worked)
- [ ] `python test_guardrails.py` passes
- [ ] `python demo_failures.py` produces blocked cases
- [ ] `python main.py` starts without errors
- [ ] `/search`, `/audit-log`, `/chat` endpoints ready
- [ ] README.md and QUICK_START.md reviewed
- [ ] FEATURES_COMPLETED.md shows all 8 done

---

**You're ready to impress the judges! 🚀**
