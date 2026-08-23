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
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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
    
    The agent will:
    1. Understand the user's intent
    2. Call appropriate tools (search, check stock, get price, initiate purchase)
    3. Apply guardrails (stock, budget, price checks)
    4. Return a natural language response
    """
    user_message = request.message
    budget = request.budget
    
    try:
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
        # Log error
        log_action(
            db=db,
            action_type="chat_error",
            status="failed",
            input_data={"message": user_message, "budget": budget},
            output_data={"error": str(e)},
            user_message=user_message
        )
        
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("✅ Razorpay Agent Catalog backend started")
    print("📚 Database initialized")
    print("🤖 Gemini agent ready")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
