"""FastAPI backend with Gemini agent reasoning."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import json
import uuid
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from database import init_db, get_db, Product, AuditLog
from schemas import ChatRequest, ChatResponse, CreateOrderRequest, VerifyPaymentRequest
from search import search_products as db_search_products, check_product_stock, get_product_price
from audit import log_action, get_audit_logs
from razorpay_service import RazorpayGuardedClient, get_razorpay_client
from context_manager import (
    get_last_shown_products as get_last_shown_products_for_session,
    update_last_shown_products,
    resolve_product_reference as resolve_ref,
    get_session
)

# Import Razorpay for payment verification
import razorpay
import hmac
import hashlib

# Load environment variables
load_dotenv()

# Initialize database
init_db()

# Initialize FastAPI
app = FastAPI(title="Razorpay Agent Catalog")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None

try:
    if GEMINI_API_KEY and GEMINI_API_KEY != "test_gemini_key_for_local_dev":
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("[OK] Gemini API initialized successfully")
    else:
        print("[WARN] Gemini API key not configured. Using mock responses for demo.")
except Exception as e:
    print(f"[WARN] Failed to initialize Gemini API: {e}. Using mock responses for demo.")

# ==================== MOCK RESPONSE HELPER ====================
def get_last_shown_products(db: Session, session_id: str) -> List[Dict]:
    """Get last shown products for this session."""
    return get_last_shown_products_for_session(session_id)


def update_shown_products(db: Session, session_id: str, products: List[Product], query: str = None) -> None:
    """Update shown products for this session."""
    update_last_shown_products(session_id, products)


def resolve_product_reference(db: Session, session_id: str, user_message: str) -> Optional[Product]:
    """
    Resolve product references like "first", "second", "that one", "it", "last".
    Returns the Product object if found, None otherwise.
    """
    last_products = get_last_shown_products(db, session_id)
    product_dict = resolve_ref(user_message, last_products)
    
    if product_dict:
        # Look up the actual product from the database
        return db.query(Product).filter(Product.id == product_dict["id"]).first()
    return None


def get_mock_agent_response(user_message: str, db: Session, session_id: str) -> tuple[str, list]:
    """
    Generate a mock agent response with proper intent detection and conversation context.
    
    Features:
    - Product reference resolution (second, that one, it)
    - Fuzzy keyword matching for typo tolerance
    - Contextual confirmations (yes, buy, ok)
    - Better off-topic vs shopping distinction
    """
    user_lower = user_message.lower().strip()
    tool_calls = []
    
    # ===== SIMPLE CONFIRMATIONS (Yes/OK/Buy) =====
    # If user just says "yes", "ok", "buy" without context, buy first shown product
    simple_confirmations = ["yes", "ok", "okay", "sure", "go", "buy"]
    last_products = get_last_shown_products(db, session_id)
    
    if user_lower in simple_confirmations and last_products and len(last_products) > 0:
        first_product_info = last_products[0]
        first_product = db.query(Product).filter(Product.id == first_product_info["id"]).first()
        
        if first_product and first_product.stock > 0:
            tool_calls = ["check_stock", "initiate_purchase"]
            
            log_action(
                db=db,
                action_type="check_stock",
                status="success",
                input_data={"product_id": first_product.id},
                output_data={"in_stock": True, "quantity": first_product.stock},
                user_message=user_message
            )
            
            log_action(
                db=db,
                action_type="purchase_attempt",
                status="success",
                input_data={"product_id": first_product.id, "quantity": 1},
                output_data={"order_id": "order_test_123", "status": "pending"},
                razorpay_order_id="order_test_123",
                user_message=user_message
            )
            
            return (
                f"Great! Order created for **{first_product.name}** (₹{first_product.price}). "
                f"Status: Pending payment.",
                tool_calls
            )
    
    # ===== TRY TO RESOLVE POSITIONAL REFERENCES =====
    resolved_product = resolve_product_reference(db, session_id, user_message)
    if resolved_product:
        if resolved_product.stock <= 0:
            log_action(
                db=db,
                action_type="purchase_attempt",
                status="blocked",
                input_data={"product_id": resolved_product.id, "reason": "out_of_stock"},
                output_data={"message": f"{resolved_product.name} is out of stock"},
                user_message=user_message
            )
            return (
                f"Sorry, **{resolved_product.name}** is currently out of stock. "
                f"Would you like to buy something else?",
                []
            )
        
        tool_calls = ["check_stock", "initiate_purchase"]
        
        log_action(
            db=db,
            action_type="check_stock",
            status="success",
            input_data={"product_id": resolved_product.id},
            output_data={"in_stock": True, "quantity": resolved_product.stock},
            user_message=user_message
        )
        
        log_action(
            db=db,
            action_type="purchase_attempt",
            status="success",
            input_data={"product_id": resolved_product.id, "quantity": 1},
            output_data={"order_id": "order_test_123", "status": "pending"},
            razorpay_order_id="order_test_123",
            user_message=user_message
        )
        
        return (
            f"Great! Order created for **{resolved_product.name}** (₹{resolved_product.price}). "
            f"Status: Pending payment.",
            tool_calls
        )
    
    # ===== FUZZY KEYWORD MATCHING (Typo Tolerance) =====
    def matches_keyword_fuzzy(text, keywords, min_length=2):
        """Check if text contains keyword with fuzzy matching for typos."""
        words = text.split()
        for word in words:
            for keyword in keywords:
                if keyword in word or word in keyword:
                    return True
                # Fuzzy match: count matching characters
                if len(keyword) >= min_length:
                    matches = sum(1 for c in keyword if c in word)
                    if matches >= len(keyword) - 1:  # Allow 1 char difference
                        return True
        return False
    
    # ===== INTENT DETECTION =====
    # Shopping intents - these SHOULD trigger search
    shopping_keywords = [
        "find", "search", "show", "what", "have", "available", 
        "looking", "want", "need", "price", "cost", "like",
        "product", "item", "recommend", "suggest", "browse", "all",
        "shirt", "shoe", "headphone", "watch", "bottle", "tea", "mat",
        "cable", "keyboard", "speaker", "bag", "plant", "toothbrush",
        "sunscreen", "pants", "trouser"
    ]
    is_shopping_intent = matches_keyword_fuzzy(user_lower, shopping_keywords, min_length=2)
    
    # Off-topic keywords - should NOT search
    off_topic_keywords = [
        "who", "about", "application", "company", "help", 
        "hello", "hi", "hey", "thanks", "thank", "how",
        "razorpay", "work", "contact", "support", "return",
        "refund", "warranty", "shipping", "delivery", "payment",
        "security", "privacy", "terms"
    ]
    is_off_topic = matches_keyword_fuzzy(user_lower, off_topic_keywords, min_length=2)
    
    # ===== HANDLE PURCHASES =====
    purchase_keywords = [
        "buy", "purchase", "checkout", "order", "add to cart", "want to buy", "i'll take",
        "first one", "that one", "take it", "get it", "ill buy", "let me buy",
        "give me", "can i buy", "i want that", "i'll buy", "send me", "add it",
        "second one", "third one", "fourth one", "fifth one", "sixth one",
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh"
    ]
    is_purchase = any(keyword in user_lower for keyword in purchase_keywords)
    
    if is_purchase and not resolved_product:
        log_action(
            db=db,
            action_type="chat",
            status="success",
            input_data={"message": user_message, "intent": "unclear_purchase"},
            output_data={"response": "clarification_needed"},
            user_message=user_message
        )
        
        return (
            "I want to help you buy something! Please tell me which product:\n\n"
            "- A specific name (e.g., 'Buy the T-Shirt')\n"
            "- A position (e.g., 'Buy the first one' or 'Buy #2')\n"
            "- Or search first (e.g., 'Show me shoes') then I can help you buy\n\n"
            "What would you like?",
            []
        )
    
    # ===== HANDLE OFF-TOPIC MESSAGES - NO SEARCH =====
    if is_off_topic and not is_shopping_intent:
        log_action(
            db=db,
            action_type="chat",
            status="success",
            input_data={"message": user_message, "intent": "off_topic"},
            output_data={"response": "conversational"},
            user_message=user_message
        )
        
        if "hello" in user_lower or "hi" in user_lower or "hey" in user_lower:
            return ("Hi! I'm your shopping assistant. What would you like to find?", [])
        elif "thanks" in user_lower or "thank" in user_lower:
            return ("You're welcome! Anything else I can help with?", [])
        elif "about" in user_lower or "application" in user_lower:
            return (
                "I'm an AI Shopping Agent that helps you find and purchase products. "
                "I can search products, check prices, and help with orders. What would you like to buy?",
                []
            )
        elif "help" in user_lower:
            return (
                "I can help you:\n1. Search for products (e.g., 'Show me shirts')\n"
                "2. Check prices\n3. Buy products (e.g., 'I want to buy it')\n\n"
                "What would you like?",
                []
            )
        elif "color" in user_lower or "colour" in user_lower or "image" in user_lower or "photo" in user_lower:
            if last_products:
                first_prod = last_products[0]
                return (
                    f"For **{first_prod['name']}** (₹{first_prod['price']}):\n"
                    f"This is from our available inventory. Would you like to:\n"
                    f"- Buy this product? Say 'yes' or 'first one'\n"
                    f"- Search for something else?\n\n"
                    f"What would you like?",
                    []
                )
            return ("I can help with that! Which product would you like to know more about?", [])
        else:
            return ("That's interesting! How can I help you shop today?", [])
    
    # ===== HANDLE SHOPPING QUERIES - SEARCH =====
    if is_shopping_intent:
        tool_calls = ["search_products"]
        
        stop_words = ["what", "show", "find", "me", "i", "want", "can", "you", "please", 
                      "looking", "for", "search", "a", "the", "do", "have", "is", "are",
                      "any", "some", "all", "get", "give", "tell", "see", "ll", "peoducts",
                      "shiw", "colpour", "image", "which"]
        
        query_words = []
        for word in user_message.lower().split():
            clean_word = word.strip('.,!?;:')
            if clean_word and clean_word not in stop_words and len(clean_word) > 2:
                query_words.append(clean_word)
        
        if not query_words:
            query = ""
        else:
            query = " ".join(query_words)
        
        products = db_search_products(db, query) if query else db.query(Product).limit(10).all()
        
        log_action(
            db=db,
            action_type="search",
            status="success",
            input_data={"query": query if query else "browse_all", "user_input": user_message},
            output_data={"results_count": len(products)},
            user_message=user_message
        )
        
        if products:
            update_shown_products(db, session_id, products, query if query else "browse_all")
        
        if not products:
            all_products = db.query(Product).limit(10).all()
            if all_products:
                update_shown_products(db, session_id, all_products, "fallback_browse")
                return (
                    f"No exact matches for '{query}', but here are some items:\n\n"
                    + format_product_list(all_products),
                    tool_calls
                )
            return ("No products found.", tool_calls)
        
        product_text = f"I found {len(products)} items:\n\n"
        product_text += format_product_list(products[:10])
        
        return (product_text, tool_calls)
    
    # ===== DEFAULT: Unclear message =====
    log_action(
        db=db,
        action_type="chat",
        status="success",
        input_data={"message": user_message, "intent": "unclear"},
        output_data={"response": "clarification_needed"},
        user_message=user_message
    )
    
    return (
        "I can help! Try one of these:\n\n"
        "🔍 **Search**: 'Show me shirts' or 'Find blue shoes'\n"
        "🛒 **Buy**: 'I want to buy the first one' or 'Buy that shirt'\n"
        "❓ **Ask**: 'How much is the headphones?'\n\n"
        "What would you like?",
        []
    )


def format_product_list(products: list) -> str:
    """Format a list of products for display."""
    text = ""
    for idx, product in enumerate(products, 1):
        stock_status = "In Stock" if product.stock > 0 else "Out of Stock"
        text += f"{idx}. **{product.name}** - ₹{product.price}\n   {stock_status} ({product.stock} available)\n\n"
    
    text += "Would you like to buy any of these, or should I search for something else?"
    return text


# ==================== TOOL DEFINITIONS ====================
# These will be passed to Gemini for function calling

TOOL_DEFINITIONS = [
    {
        "name": "search_products",
        "description": "Search the product catalog by keyword and optional filters",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'blue shirt', 'running shoes')"
                },
                "max_price": {
                    "type": "number",
                    "description": "Optional maximum price in INR (e.g., 5000)"
                },
                "size": {
                    "type": "string",
                    "description": "Optional size filter (e.g., 'M', 'L', '1L')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_stock",
        "description": "Check if a product is in stock",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "Product ID to check stock for"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "get_price",
        "description": "Get the price of a product",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "Product ID to get price for"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "initiate_purchase",
        "description": "Initiate a purchase (create Razorpay order). Must have checked stock first!",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "Product ID to purchase"
                },
                "quantity": {
                    "type": "integer",
                    "description": "Quantity to purchase"
                }
            },
            "required": ["product_id", "quantity"]
        }
    }
]

# ==================== TOOL IMPLEMENTATIONS ====================

def tool_search_products(
    db: Session,
    query: str,
    max_price: Optional[float] = None,
    size: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute search_products tool."""
    products = db_search_products(db, query, max_price, size)
    
    result = {
        "query": query,
        "results_count": len(products),
        "max_price_filter": max_price,
        "size_filter": size,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description[:100] + "..." if len(p.description) > 100 else p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.category,
            }
            for p in products
        ]
    }
    
    return result


def tool_check_stock(db: Session, product_id: int) -> Dict[str, Any]:
    """Execute check_stock tool."""
    result = check_product_stock(db, product_id)
    return result


def tool_get_price(db: Session, product_id: int) -> Dict[str, Any]:
    """Execute get_price tool."""
    result = get_product_price(db, product_id)
    return result


def tool_initiate_purchase(
    db: Session,
    product_id: int,
    quantity: int,
    budget_constraint: Optional[float] = None,
    user_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute initiate_purchase tool with guardrails."""
    razorpay_client = get_razorpay_client()
    result = razorpay_client.initiate_purchase(
        db=db,
        product_id=product_id,
        quantity=quantity,
        budget_constraint=budget_constraint,
        user_message=user_message,
    )
    return result


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "razorpay-agent-catalog"}


# ==================== SEARCH ENDPOINTS ====================

@app.post("/search", response_model=Dict[str, Any])
async def search_endpoint(query: str, max_price: Optional[float] = None, db: Session = Depends(get_db)):
    """Direct search endpoint (without agent)."""
    products = db_search_products(db, query, max_price)
    
    log_action(
        db=db,
        action_type="search",
        status="success",
        input_data={"query": query, "max_price": max_price},
        output_data={"results_count": len(products)}
    )
    
    return {
        "query": query,
        "results_count": len(products),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.category,
            }
            for p in products
        ]
    }


# ==================== AUDIT LOG ENDPOINTS ====================

@app.get("/audit-log", response_model=List[Dict[str, Any]])
async def get_audit_log(
    action_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get audit trail, most recent first."""
    logs = get_audit_logs(db, action_type=action_type, status=status, limit=limit)
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action_type": log.action_type,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "razorpay_order_id": log.razorpay_order_id,
            "status": log.status,
            "user_message": log.user_message,
        }
        for log in logs
    ]


# ==================== AGENT CHAT ENDPOINT ====================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat endpoint with full conversation history sent to Gemini every time.
    
    This is the KEY FIX:
    1. Full message history is sent (not just latest message)
    2. Last shown products injected into system prompt
    3. Gemini makes the intent decision (not keyword gatekeeping)
    4. Session state kept in-memory (conversation + products shown)
    """
    from context_manager import (
        get_session, add_message, get_conversation_history, 
        update_last_shown_products, get_last_shown_products
    )
    
    user_message = request.message
    session_id = request.session_id or f"session_{int(__import__('time').time())}"
    
    # Get session (in-memory)
    session = get_session(session_id)
    
    # Add user message to history
    add_message(session_id, "user", user_message)
    
    try:
        # Build system prompt WITH current context injected
        system_prompt = _build_system_prompt_with_context(get_last_shown_products(session_id))
        
        # Get FULL conversation history (not just latest message)
        conversation_history = get_conversation_history(session_id)
        
        # If Gemini API is available, use it
        if model:
            response = model.generate_content(
                conversation_history,
                tools=TOOL_DEFINITIONS,
                system_instruction=system_prompt,
            )
            
            # Extract response text
            reply_text = ""
            tool_calls_made = []
            
            if response.content.parts:
                for part in response.content.parts:
                    if hasattr(part, 'text'):
                        reply_text = part.text
                    elif hasattr(part, 'function_call'):
                        tool_call = part.function_call
                        tool_name = tool_call.name
                        tool_args = {arg.name: arg.value for arg in tool_call.args}
                        tool_calls_made.append(tool_name)
                        
                        # Handle search_products - update last shown products
                        if tool_name == "search_products":
                            products = db_search_products(
                                db,
                                query=tool_args.get("query", ""),
                                max_price=tool_args.get("max_price"),
                                size=tool_args.get("size")
                            )
                            update_last_shown_products(session_id, products)
                            log_action(db, "search", "success", tool_args, {"results_count": len(products)}, user_message)
            
            # Add AI response to history for next message
            if reply_text:
                add_message(session_id, "assistant", reply_text)
            
            return ChatResponse(
                reply=reply_text or "I'm not sure how to respond to that.",
                tool_calls=tool_calls_made if tool_calls_made else None,
                session_id=session_id
            )
        
        # Fallback: Use smart reasoning if no Gemini API
        from smart_agent import reason_about_intent
        
        response_text, action_data, tool_calls = reason_about_intent(
            user_message=user_message,
            db=db,
            session_id=session_id,
        )
        
        # Add to history
        add_message(session_id, "assistant", response_text)
        
        return ChatResponse(
            reply=response_text,
            tool_calls=tool_calls if tool_calls else None,
            session_id=session_id
        )
        
    except Exception as e:
        import traceback
        print(f"⚠️  Chat error: {traceback.format_exc()}")
        
        log_action(
            db=db,
            action_type="chat_error",
            status="failed",
            input_data={"message": user_message},
            output_data={"error": str(e)},
            user_message=user_message
        )
        
        return ChatResponse(
            reply="I encountered an error. Please try again.",
            tool_calls=None,
            session_id=session_id
        )


def _build_system_prompt_with_context(last_shown_products: List[Dict]) -> str:
    """Build system prompt WITH current context injected."""
    products_context = ""
    if last_shown_products:
        products_context = "The user was just shown these products:\n"
        for p in last_shown_products:
            stock_status = "In stock" if p.get("stock", 0) > 0 else "Out of stock"
            products_context += f"{p['index']}. {p['name']} - ₹{p['price']} ({stock_status})\n"
        products_context += "\nIf the user refers to an item by position (first, second, that one, last) or confirms with 'yes', resolve it against this list.\n"
    
    return f"""You are a shopping assistant agent. You help users find and purchase products.

You have access to these tools:
- search_products: Search catalog by keyword
- check_stock: Check if product is available
- get_price: Get product price  
- initiate_purchase: Create order

IMPORTANT INSTRUCTIONS:
1. Only call search_products when user asks about products, prices, or shopping
2. For greetings, unclear messages, or off-topic questions, respond conversationally WITHOUT calling tools
3. If the user's message has a typo or is vague, interpret their likely intent
4. Don't force product searches - only search when user asks for it
5. Be natural and helpful, not robotic

{products_context}"""


# ==================== PAYMENT ENDPOINTS ====================

@app.post("/purchase/create-order")
async def create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    """Create a Razorpay order for payment."""
    try:
        # If no product_id in request, try to get from session
        product_id = request.product_id
        if not product_id:
            from context_manager import get_session
            session = get_session(request.session_id)
            pending_order = session.get("pending_order", {})
            product_id = pending_order.get("product_id")
        
        if not product_id:
            log_action(db, "create_order", "failed", {"session_id": request.session_id}, {"error": "No product found"})
            return {"error": "no_product", "message": "No product selected"}
        
        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            log_action(db, "create_order", "failed", {"product_id": product_id}, {"error": "Product not found"})
            return {"error": "product_not_found", "message": "Product not found"}
        
        # Check stock
        if product.stock <= 0:
            log_action(db, "create_order", "blocked", {"product_id": product_id}, {"reason": "out_of_stock"})
            return {"error": "out_of_stock", "message": f"{product.name} is out of stock"}
        
        # Create Razorpay order
        try:
            razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
            razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")
            
            print(f"[DEBUG] Key ID: {razorpay_key_id}")
            print(f"[DEBUG] Key Secret: {razorpay_key_secret[:10]}...")
            
            # Check if using fake/demo keys (only the placeholder keys)
            is_demo_key = (razorpay_key_id == "rzp_test_TESTKEY123456" or 
                          razorpay_key_secret == "rzp_test_TESTKEYSECRET123" or
                          not razorpay_key_id or not razorpay_key_secret)
            
            print(f"[DEBUG] Is demo key: {is_demo_key}")
            
            if is_demo_key:
                # Demo mode: Generate fake Razorpay order ID
                import uuid
                fake_order_id = f"order_{uuid.uuid4().hex[:12]}"
                amount_paise = int(product.price * 100)
                
                print(f"[DEMO] Using fake Razorpay order: {fake_order_id}")
                
                log_action(
                    db=db,
                    action_type="create_order",
                    status="success",
                    input_data={"product_id": product_id, "amount": product.price, "mode": "demo"},
                    output_data={"razorpay_order_id": fake_order_id, "mode": "demo"},
                    razorpay_order_id=fake_order_id
                )
                
                return {
                    "order_id": fake_order_id,
                    "amount": amount_paise,
                    "currency": "INR",
                    "key_id": razorpay_key_id,
                    "product_id": product_id,
                    "product_name": product.name,
                    "product_price": product.price,
                    "mode": "demo"
                }
            
            # Real keys: Use actual Razorpay API
            print(f"[INFO] Using real Razorpay API with key: {razorpay_key_id[:20]}...")
            razorpay_client = razorpay.Client(
                auth=(razorpay_key_id, razorpay_key_secret)
            )
            amount_paise = int(product.price * 100)
            razorpay_order = razorpay_client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"receipt_{request.session_id}_{product_id}"
            })
            
            order_id = razorpay_order["id"]
            print(f"[INFO] Razorpay order created: {order_id}")
            
            log_action(
                db=db,
                action_type="create_order",
                status="success",
                input_data={"product_id": product_id, "amount": product.price},
                output_data={"razorpay_order_id": order_id},
                razorpay_order_id=order_id
            )
            
            return {
                "order_id": order_id,
                "amount": amount_paise,
                "currency": "INR",
                "key_id": os.getenv("RAZORPAY_KEY_ID"),
                "product_id": product_id,
                "product_name": product.name,
                "product_price": product.price
            }
        except Exception as e:
            print(f"[ERROR] Razorpay order creation failed: {e}")
            log_action(db, "create_order", "failed", {"product_id": product_id}, {"error": str(e)})
            return {"error": "razorpay_error", "message": "Failed to create order"}
            
    except Exception as e:
        print(f"[ERROR] Create order endpoint error: {e}")
        return {"error": "server_error", "message": "Internal server error"}


@app.post("/purchase/verify")
async def verify_payment(request: VerifyPaymentRequest, db: Session = Depends(get_db)):
    """Verify Razorpay payment signature and confirm order."""
    try:
        razorpay_client = razorpay.Client(
            auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
        )
        
        # Verify signature
        params_dict = {
            "razorpay_order_id": request.razorpay_order_id,
            "razorpay_payment_id": request.razorpay_payment_id,
            "razorpay_signature": request.razorpay_signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Signature valid → Payment successful
            log_action(
                db=db,
                action_type="payment_verified",
                status="success",
                input_data=params_dict,
                output_data={"status": "payment_confirmed"},
                razorpay_order_id=request.razorpay_order_id
            )
            
            return {
                "status": "success",
                "message": "Payment confirmed. Your order has been placed!",
                "order_id": request.razorpay_order_id,
                "payment_id": request.razorpay_payment_id
            }
            
        except razorpay.errors.SignatureVerificationError:
            # Signature invalid → Payment failed
            log_action(
                db=db,
                action_type="payment_failed",
                status="failed",
                input_data=params_dict,
                output_data={"error": "signature_verification_failed"},
                razorpay_order_id=request.razorpay_order_id
            )
            
            return {
                "status": "failed",
                "message": "Payment verification failed. Please try again.",
                "order_id": request.razorpay_order_id
            }
            
    except Exception as e:
        print(f"[ERROR] Payment verification error: {e}")
        log_action(db, "payment_verified", "failed", {}, {"error": str(e)})
        return {"status": "error", "message": "Payment verification error"}


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("[OK] Razorpay Agent Catalog backend started on http://0.0.0.0:8001")
    print("[OK] Database initialized")
    if model:
        print("[OK] Gemini agent ready with real API")
    else:
        print("[OK] Gemini agent running in demo mode (smart reasoning)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
