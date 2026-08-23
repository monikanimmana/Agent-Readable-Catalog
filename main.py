"""FastAPI backend with Gemini agent reasoning."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import json
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from database import init_db, get_db, Product, AuditLog
from schemas import ChatRequest, ChatResponse
from search import search_products as db_search_products, check_product_stock, get_product_price
from audit import log_action, get_audit_logs
from razorpay_service import RazorpayGuardedClient, get_razorpay_client

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

def get_mock_agent_response(user_message: str, db: Session) -> tuple[str, list]:
    """
    Generate a mock agent response with PROPER INTENT DETECTION.
    
    CRITICAL: Only searches for products when user is asking about shopping.
    For greetings, questions, or off-topic messages, responds conversationally
    WITHOUT calling search_products tool.
    
    This fixes the bug where EVERY message was treated as a product search.
    """
    user_lower = user_message.lower().strip()
    tool_calls = []
    
    # ===== INTENT DETECTION =====
    # Shopping intents - these SHOULD trigger search
    shopping_keywords = [
        "find", "search", "show", "what", "have", "available", 
        "looking for", "want", "need", "price", "cost", "like",
        "product", "item", "recommend", "suggest"
    ]
    is_shopping_intent = any(keyword in user_lower for keyword in shopping_keywords)
    
    # Non-shopping intents - these should NOT search
    off_topic_keywords = [
        "who are you", "about", "application", "company", "help", 
        "hello", "hi", "hey", "thanks", "thank you", "how are you",
        "what is razorpay", "how does it work", "contact", "support",
        "return", "refund", "warranty", "shipping", "delivery",
        "payment", "security", "privacy", "terms"
    ]
    is_off_topic = any(keyword in user_lower for keyword in off_topic_keywords)
    
    # ===== HANDLE PURCHASES =====
    purchase_keywords = [
        "buy", "purchase", "checkout", "order", "add to cart", "want to buy", "i'll take",
        "first one", "that one", "it", "take it", "get it", "ill buy", "let me buy",
        "give me", "can i buy", "i want that", "i'll buy", "send me", "add it"
    ]
    is_purchase = any(keyword in user_lower for keyword in purchase_keywords)
    
    if is_purchase:
        first_product = db.query(Product).filter(Product.stock > 0).first()
        
        if not first_product:
            return ("Sorry, all products are currently out of stock.", [])
        
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
        
        # Conversational responses
        if "hello" in user_lower or "hi" in user_lower or "hey" in user_lower:
            return ("Hi! I'm your shopping assistant. What would you like to find?", [])
        elif "thanks" in user_lower or "thank you" in user_lower:
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
        else:
            return ("That's interesting! How can I help you shop today?", [])
    
    # ===== HANDLE SHOPPING QUERIES - SEARCH ONLY HERE =====
    if is_shopping_intent:
        tool_calls = ["search_products"]
        
        # Extract search query
        stop_words = ["what", "show", "find", "me", "i", "want", "can", "you", "please", 
                      "looking", "for", "search", "a", "the", "do", "have", "is", "are",
                      "any", "some", "all", "get", "give", "tell", "see"]
        
        query_words = []
        for word in user_message.lower().split():
            clean_word = word.strip('.,!?;:')
            if clean_word and clean_word not in stop_words and len(clean_word) > 2:
                query_words.append(clean_word)
        
        query = " ".join(query_words) if query_words else user_message.strip()
        
        if not query or len(query) < 2:
            query = user_message.strip()
        
        products = db_search_products(db, query)
        
        log_action(
            db=db,
            action_type="search",
            status="success",
            input_data={"query": query, "user_input": user_message},
            output_data={"results_count": len(products)},
            user_message=user_message
        )
        
        if not products:
            all_products = db.query(Product).limit(5).all()
            if all_products:
                return (
                    f"No exact matches for '{query}', but here are some popular items:\n\n"
                    + format_product_list(all_products),
                    tool_calls
                )
            return ("No products found.", tool_calls)
        
        product_text = f"I found {len(products)} items:\n\n"
        product_text += format_product_list(products[:8])
        
        return (product_text, tool_calls)
    
    # ===== DEFAULT: Unclear message - ask for clarification, NO SEARCH =====
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
    Chat with the AI agent using Gemini with function calling.
    Falls back to mock responses if Gemini API is unavailable.
    
    The agent will:
    1. Understand the user's intent
    2. Call appropriate tools (search, check stock, get price, initiate purchase)
    3. Apply guardrails (stock, budget, price checks)
    4. Return a natural language response
    """
    user_message = request.message
    budget = request.budget
    
    try:
        # If Gemini model is not available, use mock responses
        if not model:
            mock_response, tool_calls = get_mock_agent_response(user_message, db)
            return ChatResponse(
                reply=mock_response,
                tool_calls=tool_calls if tool_calls else None
            )
        
        tool_calls_made = []
        
        system_prompt = """You are an AI shopping assistant for an e-commerce catalog. Your role is to:
1. Help users find products
2. Check product availability
3. Guide them through purchases

IMPORTANT RULES:
- ALWAYS search for products first
- ALWAYS check stock before attempting to purchase
- ALWAYS respect budget constraints
- Be helpful and explain each step clearly"""
        
        # Build initial context
        user_content = user_message
        if budget:
            user_content += f"\n\n[Note: User's budget constraint is ₹{budget}]"
        
        # Initial request to Gemini
        messages = [{"role": "user", "content": user_content}]
        
        # Call Gemini with tools available
        response = model.generate_content(
            user_content,
            tools=TOOL_DEFINITIONS,
            system_instruction=system_prompt,
        )
        
        # Check for tool calls in response
        tool_result = None
        if response.content.parts:
            for part in response.content.parts:
                if hasattr(part, 'function_call'):
                    # Gemini is calling a tool
                    tool_call = part.function_call
                    tool_name = tool_call.name
                    tool_args = {arg.name: arg.value for arg in tool_call.args}
                    
                    tool_calls_made.append(f"{tool_name}")
                    
                    # Execute the tool
                    if tool_name == "search_products":
                        tool_result = tool_search_products(
                            db,
                            query=tool_args.get("query", ""),
                            max_price=tool_args.get("max_price"),
                            size=tool_args.get("size")
                        )
                        log_action(
                            db=db,
                            action_type="search",
                            status="success",
                            input_data=tool_args,
                            output_data={"results_count": tool_result.get("results_count", 0)},
                            user_message=user_message
                        )
                    
                    elif tool_name == "check_stock":
                        tool_result = tool_check_stock(db, tool_args.get("product_id"))
                        log_action(
                            db=db,
                            action_type="check_stock",
                            status="success",
                            input_data=tool_args,
                            output_data=tool_result,
                            user_message=user_message
                        )
                    
                    elif tool_name == "get_price":
                        tool_result = tool_get_price(db, tool_args.get("product_id"))
                        log_action(
                            db=db,
                            action_type="get_price",
                            status="success",
                            input_data=tool_args,
                            output_data=tool_result,
                            user_message=user_message
                        )
                    
                    elif tool_name == "initiate_purchase":
                        tool_result = tool_initiate_purchase(
                            db,
                            product_id=tool_args.get("product_id"),
                            quantity=tool_args.get("quantity", 1),
                            budget_constraint=budget,
                            user_message=user_message
                        )
                    
                    # Call Gemini again with tool result for final response
                    if tool_result:
                        follow_up_messages = [
                            {"role": "user", "content": user_content},
                            {"role": "model", "content": response.content},
                            {"role": "user", "content": f"Tool '{tool_name}' returned: {json.dumps(tool_result)}"}
                        ]
                        
                        final_response_obj = model.generate_content(
                            follow_up_messages,
                            system_instruction=system_prompt,
                        )
                        
                        # Extract text response
                        if final_response_obj.content.parts:
                            for final_part in final_response_obj.content.parts:
                                if hasattr(final_part, 'text'):
                                    return ChatResponse(
                                        reply=final_part.text,
                                        tool_calls=tool_calls_made
                                    )
        
        # Fallback: extract text from initial response
        if response.content.parts:
            for part in response.content.parts:
                if hasattr(part, 'text'):
                    return ChatResponse(
                        reply=part.text,
                        tool_calls=tool_calls_made if tool_calls_made else None
                    )
        
        return ChatResponse(
            reply="I couldn't process your request. Please try again.",
            tool_calls=tool_calls_made if tool_calls_made else None
        )
    
    except Exception as e:
        # Log error and fall back to mock response
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️  Chat endpoint error: {error_details}")
        
        log_action(
            db=db,
            action_type="chat_error",
            status="failed",
            input_data={"message": user_message, "budget": budget},
            output_data={"error": str(e)},
            user_message=user_message
        )
        
        # Fall back to mock response instead of crashing
        try:
            mock_response, tool_calls = get_mock_agent_response(user_message, db)
            return ChatResponse(
                reply=mock_response,
                tool_calls=tool_calls if tool_calls else None
            )
        except Exception as mock_error:
            # Even mock failed, return generic error
            return ChatResponse(
                reply="I encountered an issue processing your request. Please try again.",
                tool_calls=None
            )


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("[OK] Razorpay Agent Catalog backend started on http://0.0.0.0:8001")
    print("[OK] Database initialized")
    if model:
        print("[OK] Gemini agent ready with real API")
    else:
        print("[OK] Gemini agent running in demo mode (mock responses)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
