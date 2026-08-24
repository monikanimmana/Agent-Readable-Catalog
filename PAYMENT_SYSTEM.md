# Payment System Documentation

## How Our App Handles Payments

### 1. **Payment Flow Overview**

```
Customer Books Order
    ↓
Agent Collects Details (Product, Color, Size, Address, Payment Method)
    ↓
Payment Method Selection:
    ├─ Online Payment → Create Razorpay Order
    └─ Cash on Delivery → Skip payment, Confirm booking
    ↓
Payment Processing:
    ├─ Online: Send to Razorpay → Customer makes payment → Verify signature → Confirm
    └─ COD: Direct confirmation (payment collected at delivery)
    ↓
Order Confirmed with tracking
```

### 2. **Two Payment Methods**

#### **Method 1: Online Payment (Razorpay)**
- Customer chooses "Online Payment" or "1"
- App creates Razorpay order with product details
- Order sent to Razorpay with:
  - Amount (in paise)
  - Currency (INR)
  - Product info (name, quantity)
- Payment link shared with customer
- Customer enters card/payment details
- Razorpay processes payment
- Payment signature verified by backend
- Order confirmed

#### **Method 2: Cash on Delivery (COD)**
- Customer chooses "COD" or "2"
- NO payment processing
- Order confirmed immediately
- Payment collected at delivery

### 3. **Razorpay Integration**

#### **Test Mode Setup**

Our app runs in **Razorpay Test Mode** (safe for development):

```
Test API Keys (in .env):
RAZORPAY_KEY_ID=rzp_test_YOUR_TEST_KEY_ID
RAZORPAY_KEY_SECRET=rzp_test_YOUR_TEST_KEY_SECRET
```

**Get Test Keys:**
1. Go to https://dashboard.razorpay.com/app/keys
2. Make sure you're in **Test Mode** (toggle at top-left)
3. Copy Test Key ID and Secret
4. Add to `.env` file

#### **Test Payment Cards**

```
✅ SUCCESS Card:
   Number: 4111 1111 1111 1111
   Expiry: Any future date (12/25)
   CVV: Any 3 digits (123)
   
❌ DECLINE Card:
   Number: 4222 2222 2222 2222
   Expiry: Any future date
   CVV: Any 3 digits
```

### 4. **Current Implementation**

#### **Smart Agent Booking Flow:**

```python
def reason_about_intent():
    # ... (product selection, color, size, address)
    
    # STAGE 4: Payment Method Selection
    if booking_stage == "asking_payment":
        if "online" in user_lower or user_lower == "1":
            payment_method = "Online Payment"
            # Trigger create_razorpay_order()
        elif "cod" in user_lower or user_lower == "2":
            payment_method = "Cash on Delivery"
            # Skip Razorpay, go to confirmation
        
        # Show confirmation
        return order_confirmed_response
```

#### **Backend Order Creation:**

```python
# In main.py - chat_endpoint()
if response_text contains "ORDER CONFIRMED":
    # Call Razorpay service if Online Payment
    if payment_method == "Online Payment":
        razorpay_client = get_razorpay_client()
        order = razorpay_client.initiate_purchase(
            db=db,
            product_id=product_id,
            quantity=1
        )
        # Returns: {"order_id": "order_xxx", "status": "success"}
    
    # Log to audit trail
    log_action(
        action_type="payment_initiated",
        payment_method=payment_method,
        razorpay_order_id=order_id
    )
```

### 5. **Payment Confirmation Process**

#### **Online Payment (Razorpay):**

```
1. Order Created
   Backend creates order with Razorpay
   Amount: ₹699 × 100 = 69900 paise
   
2. Payment Link Sent
   Frontend receives order_id
   Shows payment button/link to customer
   
3. Customer Pays
   Enters card details in Razorpay checkout
   Razorpay processes transaction
   
4. Signature Verification
   Razorpay sends signature in response
   Backend verifies: verify_payment_signature()
   Ensures payment is legitimate (not tampered)
   
5. Status Update
   ✅ Payment Confirmed → Order confirmed
   ❌ Payment Failed → Order cancelled
   ❌ Signature Invalid → Fraud detected
```

#### **Cash on Delivery (COD):**

```
1. Customer Selects COD
   No payment processing
   
2. Order Confirmed
   Order ID generated
   Delivery address saved
   
3. At Delivery
   Driver collects cash from customer
   Payment recorded in system
```

### 6. **Guardrails (Safety Checks)**

Our system has **3 in-code guardrails** (not just prompts):

```python
# Guardrail 1: Product exists
if not product:
    return {"status": "blocked", "message": "Product not found"}

# Guardrail 2: Stock available
if not in_stock:
    return {"status": "blocked", "message": "Out of stock"}

# Guardrail 3: Budget constraint
if total_price > budget:
    return {"status": "blocked", "message": "Exceeds budget"}
```

Every blocked action is logged with status="blocked".

### 7. **Audit Trail Logging**

Every payment action is logged:

```json
{
  "timestamp": "2026-08-24 07:45:00",
  "action_type": "payment_initiated",
  "status": "success",
  "razorpay_order_id": "order_LqXjyj34P5iQJX",
  "input_data": {
    "product_id": 1,
    "quantity": 1,
    "total_price": 699.0,
    "payment_method": "Online Payment"
  },
  "output_data": {
    "order_id": "order_LqXjyj34P5iQJX",
    "amount": 69900,
    "status": "pending"
  }
}
```

### 8. **Current Demo Mode**

**Currently (without real Razorpay keys):**

```
✅ Order ID is generated locally
✅ Payment details stored in audit log
✅ Mock order confirmation shown
⚠️ Actual payment NOT processed (demo mode)
```

To enable real payments:
1. Get Razorpay test keys
2. Add to `.env`:
   ```
   RAZORPAY_KEY_ID=rzp_test_YOUR_KEY
   RAZORPAY_KEY_SECRET=rzp_test_YOUR_SECRET
   ```
3. Restart backend
4. Real payments will be processed

### 9. **Payment Flow Diagram**

```
Customer: "I want this dress"
    ↓
Agent: [Asks Color] → "Floral"
    ↓
Agent: [Asks Size] → "M"
    ↓
Agent: [Asks Address] → "123 Main St"
    ↓
Agent: [Asks Payment] → "1" (Online)
    ↓
Backend: Create Razorpay Order
    ├─ Amount: ₹699
    ├─ Product: Dress
    ├─ Order ID: order_xyz
    ↓
Frontend: Show Payment Button
    [PAY ₹699 WITH RAZORPAY]
    ↓
Customer: Clicks → Razorpay Checkout Opens
    ├─ Card: 4111 1111 1111 1111
    ├─ Expiry: 12/25
    ├─ CVV: 123
    ↓
Razorpay: Process Payment ✅ Success
    └─ Sends signature + payment_id
    ↓
Backend: Verify Signature
    ├─ Valid? → ✅ Order Confirmed
    └─ Invalid? → ❌ Fraud Alert
    ↓
Customer: Sees "Order Confirmed"
    ├─ Order ID: ORD-session123
    ├─ Amount: ₹699
    ├─ Delivery: 3-5 days
    ↓
Audit Log: Records all steps
```

### 10. **Next Steps to Enable Real Payments**

1. **Create Razorpay Account**
   - Go to https://razorpay.com
   - Sign up with email
   
2. **Get Test Keys**
   - Login → Dashboard → Settings → API Keys
   - Copy Test Key ID and Secret
   
3. **Update .env**
   ```
   RAZORPAY_KEY_ID=rzp_test_xxxxx
   RAZORPAY_KEY_SECRET=xxxxx
   ```
   
4. **Restart Backend**
   ```
   python main.py
   ```
   
5. **Test Payment**
   - Complete booking flow
   - Use card: 4111 1111 1111 1111
   - Payment will be processed in test mode
   
6. **Production Setup**
   - Switch to Live keys
   - All payments will be real
   - Customer will see real payment processing
