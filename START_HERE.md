# 🚀 START HERE - Razorpay Agent Catalog

Welcome to the Razorpay Agent Catalog hackathon project!

This document helps you navigate the repository and understand what's been built.

---

## 📋 Quick Navigation

### 👤 I am a Judge/Evaluator
**Start here:** [`JUDGE_DEMO.md`](JUDGE_DEMO.md)
- ⏱️ 10-minute complete demo walkthrough
- 📝 Talking points and timing
- 🔍 Key files to review
- 💡 Answers to likely questions

Then check:
- [`COMPLETION_REPORT.md`](COMPLETION_REPORT.md) - What was built & delivered
- [`FEATURES_COMPLETED.md`](FEATURES_COMPLETED.md) - Feature checklist with code references

### 👨‍💻 I am a Developer  
**Start here:** [`QUICK_START.md`](QUICK_START.md)
- 5-minute setup guide
- How to run tests
- Demo scenarios

Then check:
- [`README.md`](README.md) - Complete technical documentation
- [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) - Architecture overview

### 🔧 I want to Deploy
**Start here:** [`DEPLOY_INSTRUCTIONS.md`](DEPLOY_INSTRUCTIONS.md)
- Setup instructions
- Test commands
- Troubleshooting

### 📚 I want to Understand Everything
Read in this order:
1. [`START_HERE.md`](START_HERE.md) - This file
2. [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) - Architecture
3. [`README.md`](README.md) - Full docs
4. [`FEATURES_COMPLETED.md`](FEATURES_COMPLETED.md) - Feature details
5. [`COMPLETION_REPORT.md`](COMPLETION_REPORT.md) - What was delivered

---

## ⚡ 5-Minute Quick Demo

```bash
# 1. Clone (30 sec)
git clone https://github.com/monikanimmana/Agent-Readable-Catalog.git
cd Agent-Readable-Catalog

# 2. Setup (2 min)
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
python seed.py

# 3. Show Guardrails (1 min)
python test_guardrails.py

# 4. Show Failures (1 min)
python demo_failures.py

# 5. Show Audit Trail (30 sec)
python main.py &  # Start server in background
curl http://localhost:8000/audit-log
```

---

## 🎯 What Was Built

### The Challenge
Build a backend where an AI agent can:
1. Search a product catalog
2. Reason about purchases
3. Execute real (test-mode) Razorpay transactions
4. **With every money-touching action explainable, bounded in code (not just prompted), and logged**

### The Solution
✅ FastAPI backend with Gemini AI agent  
✅ Guardrails in CODE (stock, budget, quantity checks)  
✅ Complete audit trail (every action logged)  
✅ Graceful failure handling  
✅ Real Razorpay integration (test mode)  

### 8 Features Implemented
| # | Feature | Status |
|---|---------|--------|
| 1 | Data Models + Seed (18 products) | ✅ |
| 2 | Search/Retrieval Layer | ✅ |
| 3 | Agent Tools (Gemini) | ✅ |
| 4 | Guardrails (Code-Based) | ✅ |
| 5 | Gemini Agent Loop | ✅ |
| 6 | Razorpay Integration | ✅ |
| 7 | Failure Case Handling | ✅ |
| 8 | Audit Trail Endpoint | ✅ |

---

## 🔐 Core Innovation: In-Code Guardrails

**This is what judges will evaluate:**

All safety checks are in CODE, not prompts:

```python
# In razorpay_service.py (lines 60-130)

# Guardrail 1: Product must exist
if not product:
    log_action(db, status="blocked", ...)
    return {"status": "blocked"}

# Guardrail 2: Stock must be available
if not stock_check["in_stock"]:
    log_action(db, status="blocked", ...)
    return {"status": "blocked"}

# Guardrail 3: Quantity must not exceed stock
if quantity > stock_check["quantity"]:
    log_action(db, status="blocked", ...)
    return {"status": "blocked"}

# Guardrail 4: Budget constraint must be respected
if budget_constraint and total_price > budget_constraint:
    log_action(db, status="blocked", ...)
    return {"status": "blocked"}
```

**Every blocked action is logged** ✅

---

## 📁 Repository Structure

```
razorpay-agent-catalog/
│
├── 📄 START_HERE.md              ← You are here
│
├── 🚀 QUICK START
│   ├── QUICK_START.md            (5-minute setup)
│   ├── DEPLOY_INSTRUCTIONS.md    (Deployment guide)
│   └── JUDGE_DEMO.md             (Demo walkthrough)
│
├── 📚 DOCUMENTATION
│   ├── README.md                 (Complete technical docs)
│   ├── PROJECT_SUMMARY.md        (Architecture overview)
│   ├── FEATURES_COMPLETED.md     (Feature checklist)
│   └── COMPLETION_REPORT.md      (Project summary)
│
├── 💻 SOURCE CODE
│   ├── main.py                   (FastAPI + Gemini)
│   ├── razorpay_service.py       (GUARDRAILS + Razorpay)
│   ├── database.py               (SQLAlchemy models)
│   ├── search.py                 (Product search)
│   ├── audit.py                  (Audit logging)
│   ├── schemas.py                (Pydantic models)
│   ├── seed.py                   (Database seeding)
│   └── requirements.txt           (Python packages)
│
├── ✅ TESTS
│   ├── test_guardrails.py        (5 guardrail tests)
│   ├── demo_failures.py          (3 failure scenarios)
│   ├── test_search.py            (Search tests)
│   └── test_api.py               (API tests)
│
├── ⚙️ CONFIG
│   ├── .env.example              (Environment template)
│   └── .gitignore                (Git ignore)
│
└── 📋 README                      (Project overview)
```

---

## 🎯 Key Files for Judges

### 1. Understand the Guardrails (CRITICAL)
**File:** `razorpay_service.py` (lines 60-130)
- Shows in-code safety checks
- Demonstrates blocking mechanism
- Shows logging of blocked actions

### 2. See the Failures Work
**File:** `demo_failures.py` (run: `python demo_failures.py`)
- Out-of-stock scenario: BLOCKED
- Budget exceeded scenario: BLOCKED
- All failures logged in audit trail

### 3. Verify the Audit Trail
**File:** `main.py` (lines 208-224) + `audit.py`
- GET /audit-log endpoint
- Shows all logged actions
- Displays blocked actions with status="blocked"

### 4. Review the Agent
**File:** `main.py` (lines 75-130, 232-320)
- Tool definitions (4 Gemini tools)
- Agent reasoning loop
- Tool execution with guardrails

---

## 🔍 Demo the Features

### Demo 1: Show Guardrails (1 minute)
```bash
python test_guardrails.py
```
Shows:
- ✅ Blocked: Non-existent product
- ✅ Blocked: Out-of-stock product
- ✅ Blocked: Budget exceeded
- ✅ Blocked: Quantity exceeds stock

### Demo 2: Show Failures (1 minute)
```bash
python demo_failures.py
```
Shows:
- ✅ Out-of-stock case: Logged as "blocked"
- ✅ Budget case: Logged as "blocked"
- ✅ Quantity case: Logged as "blocked"

### Demo 3: Show Data (30 seconds)
```bash
python test_search.py
```
Shows:
- ✅ 18 realistic products
- ✅ Stock levels (including 0)
- ✅ Price ranges
- ✅ Search working

### Demo 4: Show API (1 minute)
```bash
python main.py
# In another terminal:
curl http://localhost:8000/audit-log
```
Shows:
- ✅ API responds
- ✅ All actions logged
- ✅ Blocks visible

---

## 📊 Test Results

All tests pass ✅

```bash
$ python test_guardrails.py
✅ Correctly blocked non-existent product
✅ Correctly blocked out-of-stock product
✅ Correctly blocked purchase exceeding budget
✅ Correctly blocked quantity exceeding stock
✅ Guardrails passed, would call Razorpay API

$ python demo_failures.py
[CASE 1] Out of Stock → BLOCKED, logged
[CASE 2] Budget Exceeded → BLOCKED, logged
[CASE 3] Quantity Too High → BLOCKED, logged
✅ DEMONSTRATION COMPLETE

$ python test_search.py
✅ Found 1 products matching "shirt" under ₹1000
✅ Found 4 products matching "water"
✅ Found 1 products matching "running shoes"
```

---

## 🎓 What You'll Learn

### From the Code
- ✅ How to build agentic AI (Gemini with tools)
- ✅ How to implement safety guardrails
- ✅ How to integrate payment APIs (Razorpay)
- ✅ How to design audit trails
- ✅ FastAPI and SQLAlchemy patterns

### From the Tests
- ✅ How to test guardrails
- ✅ How to verify failure cases
- ✅ How to check audit logging

### From the Documentation
- ✅ How to explain complex systems clearly
- ✅ How to guide users through setup
- ✅ How to write for different audiences

---

## 🚀 Get Started

### Option 1: Quick Demo (5 minutes)
```bash
git clone https://github.com/monikanimmana/Agent-Readable-Catalog.git
cd Agent-Readable-Catalog
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python test_guardrails.py
python demo_failures.py
```

### Option 2: Full Setup (10 minutes)
Follow [`QUICK_START.md`](QUICK_START.md)

### Option 3: Judge Demo (10 minutes)
Follow [`JUDGE_DEMO.md`](JUDGE_DEMO.md)

---

## ❓ Common Questions

**Q: How do guardrails prevent bypass?**
A: They're in code (`razorpay_service.py`), executed before Razorpay API is called. Agent can't see or bypass them.

**Q: Are failures really logged?**
A: Yes. Check the audit trail with `curl http://localhost:8000/audit-log` after running demo scripts.

**Q: Can this scale?**
A: Yes. Architecture is production-ready. For 1M products: switch to PostgreSQL, add Redis, use pagination.

**Q: Is Razorpay integration real?**
A: Yes. It's test mode (rzp_test_*). Real payment cards are not charged.

**Q: How long did this take?**
A: ~4-5 hours for a complete 1-day hackathon build.

---

## 📍 Important Links

- **GitHub Repository:** https://github.com/monikanimmana/Agent-Readable-Catalog
- **Quick Start:** [`QUICK_START.md`](QUICK_START.md)
- **Judge Demo:** [`JUDGE_DEMO.md`](JUDGE_DEMO.md)
- **Full Docs:** [`README.md`](README.md)

---

## ✅ Checklist for First Time

- [ ] Read this file (you are here ✓)
- [ ] Choose your path (Judge / Developer / Deployer)
- [ ] Follow the appropriate guide
- [ ] Run the demo scripts
- [ ] Review the key files
- [ ] Ask questions (see docs)

---

## 🎉 Ready?

### For Judges:
→ Go to [`JUDGE_DEMO.md`](JUDGE_DEMO.md)

### For Developers:
→ Go to [`QUICK_START.md`](QUICK_START.md)

### For Deployment:
→ Go to [`DEPLOY_INSTRUCTIONS.md`](DEPLOY_INSTRUCTIONS.md)

---

**Status: ✅ Complete & Ready**

**Last Updated:** August 23, 2026  
**Repository:** https://github.com/monikanimmana/Agent-Readable-Catalog
