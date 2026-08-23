"""
Default AI responses for demo/testing without real Gemini API.
Provides realistic, context-aware responses for common user intents.
"""

from typing import Dict, List, Optional

# Default responses for common patterns
DEFAULT_RESPONSES = {
    # Greetings
    "greeting": [
        "Hi there! 👋 I'm your shopping assistant. What would you like to find today?",
        "Hey! Ready to shop? Just tell me what you're looking for!",
        "Hello! What can I help you find?",
    ],
    
    # Search/Browse
    "browse_all": [
        "Great! Here are our available products. Take a look and let me know if anything catches your eye!",
        "Sure! Here's what we have in stock. Want to buy any of these?",
        "Here are our top items! Any of these interest you?",
    ],
    
    # Product found
    "search_success": [
        "Perfect! I found what you're looking for. Would you like to buy any of these?",
        "Great! Here are the matching items. Ready to purchase?",
        "Found some great options! Which one interests you?",
    ],
    
    # No exact match
    "search_no_match": [
        "Hmm, I don't have an exact match for that, but here are some similar items that might work!",
        "That specific item isn't available right now, but check out these alternatives!",
        "I couldn't find an exact match, but these similar products might interest you:",
    ],
    
    # Purchase confirmation
    "purchase_success": [
        "🎉 Order confirmed! Your purchase is being processed. Thank you!",
        "Perfect! Your order has been placed. You'll receive it soon!",
        "Excellent choice! Your order is complete. Thanks for shopping!",
    ],
    
    # Out of stock
    "out_of_stock": [
        "Sorry, that item is currently out of stock. Would you like to see similar products instead?",
        "That one's sold out at the moment. Can I show you alternatives?",
        "Unfortunately, that's not available right now. Want to try something similar?",
    ],
    
    # Product info
    "product_info": [
        "This is one of our bestsellers! Available in multiple variants. Ready to buy?",
        "Great product! High quality and great reviews. Want it?",
        "This item is very popular! We have plenty in stock.",
    ],
    
    # Help/Questions
    "help": [
        "I can help you:\n🔍 Search for products (e.g., 'Show me shirts')\n🛒 Buy items (e.g., 'I want the first one')\n💰 Check prices\n\nWhat would you like?",
        "Here's what I can do:\n• Search our catalog\n• Help you find products by price or type\n• Process your purchases\n\nWhat sounds good?",
    ],
    
    # Unclear
    "unclear": [
        "I'm not quite sure what you mean. Could you try:\n🔍 'Show me [product]' - to search\n🛒 'Buy [product]' - to purchase\n\nWhat would you like?",
        "I didn't catch that. Try asking me to search for something or buy a product!",
    ],
    
    # Confirmation
    "confirm": [
        "Perfect! Let me process that for you.",
        "Got it! Just confirming...",
        "Sure thing!",
    ],
}


def get_default_response(intent: str, variant: int = 0) -> str:
    """Get a default response for an intent."""
    responses = DEFAULT_RESPONSES.get(intent, DEFAULT_RESPONSES["unclear"])
    return responses[variant % len(responses)]


# Context-aware response generators
def generate_search_response(query: str, found_count: int, is_exact_match: bool) -> str:
    """Generate search response based on results."""
    if found_count == 0:
        return get_default_response("search_no_match")
    elif is_exact_match:
        return f"Excellent! I found {found_count} item(s) matching '{query}'. Take a look!"
    else:
        return f"I found {found_count} similar item(s) to '{query}'. Any of these interest you?"


def generate_purchase_response(product_name: str, price: float, success: bool = True) -> str:
    """Generate purchase response."""
    if success:
        return f"🎉 Great! Order created for **{product_name}** (₹{price}). Status: Pending payment."
    else:
        return f"Sorry, I couldn't process the order for **{product_name}**. Please try again."


def generate_error_response(error_type: str) -> str:
    """Generate error responses."""
    errors = {
        "out_of_stock": "Sorry, that item is out of stock. Would you like to see alternatives?",
        "no_products_shown": "I haven't shown you any products yet. Let me search for something for you!",
        "unclear_purchase": "I want to help you buy something! Could you tell me which product or say 'first one', 'second', etc?",
        "invalid_reference": "I'm not sure which product you're referring to. Could you be more specific?",
    }
    return errors.get(error_type, DEFAULT_RESPONSES["unclear"][0])


# Product-specific default responses
def get_product_detail_response(product_name: str, price: float, stock: int) -> str:
    """Generate product detail response."""
    stock_status = "In Stock" if stock > 0 else "Out of Stock"
    return (
        f"**{product_name}**\n"
        f"💰 Price: ₹{price}\n"
        f"📦 Status: {stock_status} ({stock} available)\n\n"
        f"Would you like to buy this?"
    )


# Multi-turn conversation defaults
CONVERSATION_FLOWS = {
    "search_to_buy": {
        "step1_search": "What would you like to search for?",
        "step2_show": "Here are the results. Which one interests you?",
        "step3_confirm": "Ready to buy? Just say 'yes', 'first one', 'second', etc!",
    },
    "browse_to_buy": {
        "step1_browse": "Let me show you our available products...",
        "step2_select": "Pick any product you like!",
        "step3_buy": "Which one would you like to buy?",
    },
    "purchase_flow": {
        "step1_confirm": "Let me confirm your order...",
        "step2_process": "Processing your purchase...",
        "step3_success": "✅ Order created successfully!",
    },
}


# Welcome messages
WELCOME_MESSAGES = [
    "👋 Hi! I'm your shopping agent. I can help you find products, check prices, and complete purchases. What are you looking for today?",
    "Welcome! 👋 I'm here to help you shop. What would you like to find?",
    "Hello! 👋 Ready to find something great? Tell me what you're looking for!",
]


# Quick suggestions when user seems lost
QUICK_SUGGESTIONS = [
    "Try asking me to 'show me shirts' or 'find shoes'",
    "You can say 'buy the first one' or 'show me all'",
    "How about searching for something? E.g., 'show me headphones'",
    "I can search for products or help you buy. What would you like?",
]


def get_welcome_message(variant: int = 0) -> str:
    """Get welcome message."""
    return WELCOME_MESSAGES[variant % len(WELCOME_MESSAGES)]


def get_quick_suggestion(variant: int = 0) -> str:
    """Get a quick suggestion when user is unclear."""
    return QUICK_SUGGESTIONS[variant % len(QUICK_SUGGESTIONS)]
