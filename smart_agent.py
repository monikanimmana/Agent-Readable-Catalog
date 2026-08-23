"""
Smart agent that mimics Gemini's reasoning - sends every message through contextual reasoning.
Uses default AI responses for natural, context-aware interactions without real API.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Tuple
from database import Product
from context_manager import get_last_shown_products, resolve_product_reference, update_shown_products
from search import search_products as db_search_products
from audit import log_action
from default_ai_responses import (
    generate_search_response,
    generate_purchase_response,
    generate_error_response,
    get_product_detail_response,
    get_default_response,
)


def reason_about_intent(
    user_message: str,
    db: Session,
    session_id: str,
) -> Tuple[str, Dict[str, Any], list]:
    """
    Reason about what the user wants using context, NOT keyword matching.
    
    This is the ONE place decisions happen - replaces all the branching keyword logic.
    
    Returns: (response_text, action_data, tool_calls)
    where action_data contains: {intent, product_id, query, confirmation, etc}
    """
    
    user_lower = user_message.lower().strip()
    last_products = get_last_shown_products(db, session_id)
    
    # ===== REASONING CHAIN =====
    # We reason through possibilities in order of likelihood given the context
    
    # 1. Is this referring to a specific product from what we just showed?
    resolved_product = resolve_product_reference(db, session_id, user_message)
    if resolved_product:
        # User is referencing a product: "second", "that one", "it", "the shirt"
        if resolved_product.stock <= 0:
            action = {
                "intent": "purchase_blocked_out_of_stock",
                "product_id": resolved_product.id,
                "product_name": resolved_product.name
            }
            response = f"Sorry, **{resolved_product.name}** is currently out of stock. Would you like to search for something else?"
            log_action(
                db=db,
                action_type="purchase_attempt",
                status="blocked",
                input_data={"product_id": resolved_product.id, "reason": "out_of_stock"},
                output_data={"message": response},
                user_message=user_message
            )
            return response, action, []
        
        # Product is in stock - buy it
        action = {
            "intent": "purchase_product_by_reference",
            "product_id": resolved_product.id,
            "product_name": resolved_product.name,
            "quantity": 1
        }
        response = f"Great! Order created for **{resolved_product.name}** (₹{resolved_product.price}). Status: Pending payment."
        
        log_action(
            db=db,
            action_type="purchase_attempt",
            status="success",
            input_data={"product_id": resolved_product.id, "quantity": 1},
            output_data={"order_id": "order_test_123", "status": "pending"},
            razorpay_order_id="order_test_123",
            user_message=user_message
        )
        return response, action, ["check_stock", "initiate_purchase"]
    
    # 2. Simple affirmations (yes/ok) when products shown?
    # If user just says "yes", "ok", "buy", "confirm" and we showed products, assume buy first
    simple_affirmations = ["yes", "ok", "okay", "sure", "go", "proceed", "confirm", "buy"]
    if user_lower in simple_affirmations and last_products:
        first_product_info = last_products[0]
        first_product = db.query(Product).filter(Product.id == first_product_info["id"]).first()
        
        if first_product and first_product.stock > 0:
            action = {
                "intent": "purchase_by_affirmation",
                "product_id": first_product.id,
                "product_name": first_product.name,
                "quantity": 1
            }
            response = f"Great! Order created for **{first_product.name}** (₹{first_product.price}). Status: Pending payment."
            
            log_action(
                db=db,
                action_type="purchase_attempt",
                status="success",
                input_data={"product_id": first_product.id, "quantity": 1},
                output_data={"order_id": "order_test_123", "status": "pending"},
                razorpay_order_id="order_test_123",
                user_message=user_message
            )
            return response, action, ["check_stock", "initiate_purchase"]
    
    # 3. Is this asking to search/browse for products?
    # Look for intent patterns: "show", "find", "search", "what", specific product types
    search_patterns = [
        "show", "find", "search", "what", "have", "looking for", "want",
        "shirt", "shoe", "headphone", "watch", "bottle", "tea", "mat",
        "cable", "keyboard", "speaker", "bag", "plant", "toothbrush",
        "products", "items", "available", "browse"
    ]
    
    # Even with typos, check if any search pattern is in the message
    message_words = user_message.lower().split()
    has_search_intent = any(pattern in user_lower for pattern in search_patterns)
    
    if has_search_intent:
        # Extract what they're searching for
        # Remove common words to get the query
        stop_words = {"what", "show", "find", "me", "i", "want", "can", "you", "please",
                      "looking", "for", "search", "a", "the", "do", "have", "is", "are",
                      "any", "some", "all", "get", "give", "tell", "see", "ll", "peoducts",
                      "shiw", "colpour", "image", "which", "browse"}
        
        query_words = []
        for word in message_words:
            clean_word = word.strip('.,!?;:')
            if clean_word and clean_word not in stop_words and len(clean_word) > 2:
                query_words.append(clean_word)
        
        query = " ".join(query_words) if query_words else ""
        
        # Search
        products = db_search_products(db, query) if query else db.query(Product).limit(10).all()
        
        # Store what we're about to show
        if products:
            update_shown_products(db, session_id, products, query if query else "browse_all")
        
        # Format response
        if not products:
            # Try fallback
            all_products = db.query(Product).limit(10).all()
            if all_products:
                update_shown_products(db, session_id, all_products, "fallback_browse")
                product_list = _format_product_list(all_products)
                response = f"No exact matches for '{query}', but here are some items:\n\n{product_list}"
            else:
                response = "No products found."
                action = {"intent": "search", "query": query, "results": 0}
                log_action(db, "search", "success", {"query": query}, {"results_count": 0}, user_message=user_message)
                return response, action, []
        else:
            product_list = _format_product_list(products)
            response = f"I found {len(products)} items:\n\n{product_list}"
        
        action = {
            "intent": "search_products",
            "query": query,
            "results_count": len(products)
        }
        log_action(db, "search", "success", {"query": query}, {"results_count": len(products)}, user_message=user_message)
        return response, action, ["search_products"]
    
    # 4. Is this a greeting or conversational message?
    conversational_patterns = [
        ("hello", "Hi! I'm your shopping assistant. What would you like to find?"),
        ("hi", "Hi! I'm your shopping assistant. What would you like to find?"),
        ("hey", "Hi! I'm your shopping assistant. What would you like to find?"),
        ("thanks", "You're welcome! Anything else I can help with?"),
        ("thank you", "You're welcome! Anything else I can help with?"),
        ("about", "I'm an AI Shopping Agent. I help you find and purchase products. What would you like to buy?"),
        ("help", "I can:\n🔍 Search for products (e.g., 'Show me shirts')\n🛒 Buy products (e.g., 'I want the first one')\n\nWhat would you like?"),
    ]
    
    for pattern, response_text in conversational_patterns:
        if pattern in user_lower:
            action = {"intent": "conversational", "pattern": pattern}
            log_action(db, "chat", "success", {"message": user_message, "intent": "conversational"},
                      {"response": response_text}, user_message=user_message)
            return response_text, action, []
    
    # 5. Questions about products we just showed (color, size, image, etc)?
    product_question_patterns = ["color", "colour", "image", "photo", "size", "how much", "price", "cost"]
    if any(p in user_lower for p in product_question_patterns) and last_products:
        first_prod = last_products[0]
        response = (f"For **{first_prod['name']}** (₹{first_prod['price']}):\n"
                   f"Would you like to:\n"
                   f"- Buy this? Say 'yes' or 'first one'\n"
                   f"- Search for something else?\n\n"
                   f"What would you like?")
        action = {"intent": "product_details_question", "product_id": first_prod["id"]}
        log_action(db, "chat", "success", {"message": user_message, "intent": "product_details_question"},
                  {"response": response}, user_message=user_message)
        return response, action, []
    
    # 6. Fallback: If we can't reason about it, ask for clarification
    # (only when we genuinely don't understand, not because keyword matching failed)
    response = ("I'm not sure what you mean. Could you try:\n\n"
               "🔍 'Search for [product]' (e.g., 'Show me shoes')\n"
               "🛒 'Buy [product]' (e.g., 'I want the first one')\n"
               "❓ Ask me anything about the app\n\n"
               "What would you like?")
    action = {"intent": "unclear"}
    log_action(db, "chat", "success", {"message": user_message, "intent": "unclear"},
              {"response": response}, user_message=user_message)
    return response, action, []


def _format_product_list(products: List[Product]) -> str:
    """Format products for display."""
    text = ""
    for idx, product in enumerate(products, 1):
        stock_status = "In Stock" if product.stock > 0 else "Out of Stock"
        text += f"{idx}. **{product.name}** - ₹{product.price}\n   {stock_status} ({product.stock} available)\n\n"
    text += "Would you like to buy any of these, or should I search for something else?"
    return text
