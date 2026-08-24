"""
Smart agent with proper booking flow: Product → Color/Size → Address → Payment → Confirmation
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Tuple
from database import Product
from context_manager import (
    get_last_shown_products, 
    update_last_shown_products,
    resolve_product_reference as resolve_ref,
    get_session,
    set_selected_product,
    set_product_variant,
    set_address,
    set_awaiting_confirmation,
    get_selected_product,
    get_address,
    is_awaiting_confirmation
)
from search import search_products as db_search_products
from audit import log_action


def reason_about_intent(
    user_message: str,
    db: Session,
    session_id: str,
) -> Tuple[str, Dict[str, Any], list]:
    """
    Enhanced reasoning with proper booking flow:
    Product Selection → Color Selection → Size Selection → Address → Payment Method → Confirmation
    """
    
    user_lower = user_message.lower().strip()
    last_products = get_last_shown_products(session_id)
    selected_product = get_selected_product(session_id)
    session = get_session(session_id)
    
    # Get booking state
    product_id = selected_product["id"] if selected_product else None
    color = selected_product["color"] if selected_product else None
    size = selected_product["size"] if selected_product else None
    address = get_address(session_id)
    booking_stage = session.get("booking_stage", "initial")  # initial, asking_clothing_type, asking_product, asking_color, asking_size, asking_address, asking_payment, confirmed
    
    # ===== NEW STAGE: Clothing Type Selection =====
    # After we show "1. Casual 2. Formal 3. Party", user picks one
    if booking_stage == "asking_clothing_type":
        # Get the clothing type and subtypes from the stored action
        clothing_type = session.get("current_clothing_type")
        subtypes = session.get("current_subtypes", [])
        
        if clothing_type and subtypes:
            # Check if user selected a valid subtype
            user_input_lower = user_lower
            selected_subtype = None
            
            # Try to match by name or number
            for idx, subtype in enumerate(subtypes, 1):
                if user_input_lower == str(idx) or user_input_lower == subtype.lower():
                    selected_subtype = subtype
                    break
            
            if selected_subtype:
                # Filter products of this type by the selected subtype
                products = db.query(Product).filter(
                    Product.category.ilike(f"%{clothing_type}%"),
                    Product.variants.ilike(f"%{selected_subtype}%")
                ).all()
                
                if not products:
                    # If exact variant match fails, just show all of this type
                    products = db.query(Product).filter(
                        Product.category.ilike(f"%{clothing_type}%")
                    ).all()
                
                if products:
                    update_last_shown_products(session_id, products)
                    session["booking_stage"] = "asking_product"  # Next: ask which product
                    
                    response = f"📦 Showing {len(products)} **{selected_subtype}** {clothing_type}(s):\n\n"
                    for idx, product in enumerate(products, 1):
                        stock_status = "✅" if product.stock > 0 else "❌"
                        response += f"{idx}. **{product.name}** - ₹{product.price} {stock_status}\n"
                    
                    response += "\nWhich one would you like? (Say 'first', 'second', '1', '2', or the product name)"
                    
                    action = {"intent": "subtype_selected", "category": clothing_type, "subtype": selected_subtype}
                    log_action(db, "chat", "success", {"message": user_message, "intent": "subtype_selected"},
                              {"subtype": selected_subtype}, user_message=user_message)
                    return response, action, []
            
            # If no valid selection, re-show the menu
            response = f"👕 **{clothing_type.upper()}** Types:\n\n"
            for i, subtype in enumerate(subtypes, 1):
                response += f"{i}. {subtype}\n"
            response += "\nWhich type would you prefer? (Say '1', '2', etc. or the name)"
            action = {"intent": "asking_clothing_type"}
            return response, action, []
    
    # ===== NEW STAGE: Product Selection from filtered list =====
    # After showing filtered products, user picks one
    if booking_stage == "asking_product" and last_products:
        # Try to resolve product reference (first, second, last, number, name)
        resolved_product_dict = resolve_ref(user_message, last_products)
        
        if resolved_product_dict:
            resolved_product = db.query(Product).filter(Product.id == resolved_product_dict["id"]).first()
            if resolved_product:
                set_selected_product(session_id, resolved_product.id, resolved_product.name)
                session["booking_stage"] = "asking_color"  # Start asking for color
                
                # Show product details and ask for color
                response = f"✨ **{resolved_product.name}**\n"
                response += f"💰 Price: ₹{resolved_product.price}\n"
                response += f"📦 Stock: {resolved_product.stock} available\n\n"
                
                if resolved_product.variants:
                    variants = resolved_product.variants
                    color_options = variants.get("colors", [])
                    
                    if color_options:
                        response += f"🎨 Available Colors:\n"
                        for color_opt in color_options:
                            response += f"  • {color_opt}\n"
                        response += f"\nPlease share your preferred **color**!"
                    else:
                        response += "This product is ready to book!\n"
                        session["booking_stage"] = "asking_address"
                        response += "Please provide your **delivery address**"
                
                action = {"intent": "product_selected", "product_id": resolved_product.id}
                log_action(db, "chat", "success", {"message": user_message, "intent": "product_selected"},
                          {"product_id": resolved_product.id}, user_message=user_message)
                return response, action, []
    
    # ===== BOOKING FLOW STAGES =====
    
    # STAGE 1: Color Selection (after product selected)
    if booking_stage == "asking_color" and selected_product:
        color_keywords = ["floral", "white", "black", "blue", "red", "green", "pink", "yellow", "purple", "gold", "silver", "maroon", "navy", "brown", "grey", "beige", "cream", "light", "dark", "solid"]
        
        if any(keyword in user_lower for keyword in color_keywords):
            set_product_variant(session_id, color=user_message)
            session["booking_stage"] = "asking_size"
            
            product = db.query(Product).filter(Product.id == product_id).first()
            response = f"Great! Color: **{user_message}**\n\n"
            response += "Now, what **size** would you like?\n"
            
            if product and product.variants:
                sizes = product.variants.get("sizes", [])
                if sizes:
                    response += "\n📏 Available Sizes:\n"
                    for size_opt in sizes:
                        response += f"  • {size_opt}\n"
            
            action = {"intent": "color_selected", "color": user_message}
            log_action(db, "chat", "success", {"message": user_message, "intent": "color_selected"},
                      {"color": user_message}, user_message=user_message)
            return response, action, []
        else:
            response = "Sorry, I didn't catch that color. Please choose from available colors:\n"
            product = db.query(Product).filter(Product.id == product_id).first()
            if product and product.variants:
                colors = product.variants.get("colors", [])
                for color_opt in colors:
                    response += f"  • {color_opt}\n"
            action = {"intent": "asking_color"}
            return response, action, []
    
    # STAGE 2: Size Selection (after color selected)
    if booking_stage == "asking_size" and selected_product and color:
        size_keywords = ["xs", "s", "m", "l", "xl", "xxl", "one size", "26", "28", "30", "32", "34", "36", "500ml", "750ml", "1l"]
        
        if any(keyword in user_lower for keyword in size_keywords):
            set_product_variant(session_id, size=user_message)
            session["booking_stage"] = "confirmed"  # Skip address/payment, go straight to confirmation
            
            product = db.query(Product).filter(Product.id == product_id).first()
            
            # Store order details in session for Razorpay
            session["pending_order"] = {
                "product_id": product_id,
                "product_name": product.name,
                "price": product.price,
                "color": color,
                "size": user_message
            }
            
            response = (f"✨ **Order Summary**\n\n"
                       f"📦 Product: **{product.name}**\n"
                       f"💰 Price: ₹{product.price}\n"
                       f"🎨 Color: **{color}**\n"
                       f"📏 Size: **{user_message}**\n\n"
                       f"💳 Proceeding to Razorpay payment...\n"
                       f"(Checkout popup will open)")
            
            action = {
                "intent": "order_ready_for_payment",
                "product_id": product_id,
                "product_name": product.name,
                "price": product.price
            }
            log_action(db, "chat", "success", {"message": user_message, "intent": "order_ready"},
                      {"product_id": product_id, "color": color, "size": user_message}, user_message=user_message)
            return response, action, ["initiate_purchase"]
        else:
            response = "Sorry, I didn't catch that size. Please choose from available sizes:\n"
            product = db.query(Product).filter(Product.id == product_id).first()
            if product and product.variants:
                sizes = product.variants.get("sizes", [])
                for size_opt in sizes:
                    response += f"  • {size_opt}\n"
            action = {"intent": "asking_size"}
            return response, action, []
    
    # ===== PRODUCT SELECTION FLOW =====
    
    # CLOTHING TYPE QUERIES - CHECK FIRST BEFORE GENERIC "SHOW"
    # IMPORTANT: Check t-shirt BEFORE shirt to avoid substring matching
    clothing_searches = {
        "t-shirt": ["Plain", "Graphic"],
        "shirt": ["Plain", "Party", "Formal"],
        "saree": ["Kachipuram", "Plain", "Party Wear", "Traditional"],
        "tops": ["Short Sleeve", "Long Sleeve", "Chikankari", "Traditional", "Party Wear"],
        "dress": ["Casual", "Formal", "Party"],
        "jeans": ["Slim Fit", "Skinny"],
    }
    
    for clothing_type, subtypes in clothing_searches.items():
        # Use word boundary matching to avoid substring issues
        # e.g., "t-shirt" should match "t-shirt" but not be matched by "shirt"
        if f" {clothing_type}" in f" {user_lower}" or user_lower.startswith(clothing_type) or user_lower.endswith(clothing_type):
            products = db.query(Product).filter(
                Product.category.ilike(f"%{clothing_type}%")
            ).all()
            
            if not products:
                response = f"Sorry, no {clothing_type}s available right now."
                action = {"intent": "search", "query": clothing_type, "results": 0}
                log_action(db, "search", "success", {"query": clothing_type}, {"results_count": 0}, user_message=user_message)
                return response, action, []
            
            update_last_shown_products(session_id, products)
            session["booking_stage"] = "asking_clothing_type"  # CHANGED: waiting for type selection
            session["current_clothing_type"] = clothing_type  # Store for next stage
            session["current_subtypes"] = subtypes  # Store subtypes
            
            response = f"👕 **{clothing_type.upper()}** Types:\n\n"
            for i, subtype in enumerate(subtypes, 1):
                response += f"{i}. {subtype}\n"
            response += "\nWhich type would you prefer? (Say '1', '2', etc. or the name)"
            
            action = {"intent": "asking_clothing_type", "category": clothing_type, "subtypes": subtypes}
            log_action(db, "search", "success", {"query": clothing_type}, {"results_count": len(products)}, user_message=user_message)
            return response, action, ["search_products"]
    
    # SHOW ALL / SHOW PRODUCTS (only if no specific clothing type matched)
    show_keywords = ["show all", "show", "display", "list", "browse"]
    if any(keyword in user_lower for keyword in show_keywords):
        products = db.query(Product).limit(18).all()
        if not products:
            response = "No products available."
            action = {"intent": "search", "query": "browse_all", "results": 0}
            log_action(db, "search", "success", {"query": "browse_all"}, {"results_count": 0}, user_message=user_message)
            return response, action, []
        
        update_last_shown_products(session_id, products)
        response = f"📦 Showing {len(products)} items:\n\n"
        for idx, product in enumerate(products, 1):
            stock_status = "✅" if product.stock > 0 else "❌"
            response += f"{idx}. **{product.name}** - ₹{product.price} {stock_status}\n"
        
        response += "\nWhich one interests you? (Say 'first', 'second', or the product name)"
        action = {"intent": "show_all", "results_count": len(products)}
        log_action(db, "search", "success", {"query": "browse_all"}, {"results_count": len(products)}, user_message=user_message)
        return response, action, ["search_products"]
    
    # PRODUCT SELECTION (First, Second, Last, or by number)
    resolved_product_dict = resolve_ref(user_message, last_products)
    if resolved_product_dict:
        resolved_product = db.query(Product).filter(Product.id == resolved_product_dict["id"]).first()
        if resolved_product:
            set_selected_product(session_id, resolved_product.id, resolved_product.name)
            session["booking_stage"] = "asking_color"  # Start asking for color
            
            # Show product details and ask for color
            response = f"✨ **{resolved_product.name}**\n"
            response += f"💰 Price: ₹{resolved_product.price}\n"
            response += f"📦 Stock: {resolved_product.stock} available\n\n"
            
            if resolved_product.variants:
                variants = resolved_product.variants
                color_options = variants.get("colors", [])
                
                if color_options:
                    response += f"🎨 Available Colors:\n"
                    for color_opt in color_options:
                        response += f"  • {color_opt}\n"
                    response += f"\nPlease share your preferred **color**!"
                else:
                    response += "This product is ready to book!\n"
                    session["booking_stage"] = "asking_address"
                    response += "Please provide your **delivery address**"
            
            action = {"intent": "product_selected", "product_id": resolved_product.id}
            log_action(db, "chat", "success", {"message": user_message, "intent": "product_selected"},
                      {"product_id": resolved_product.id}, user_message=user_message)
            return response, action, []
    
    # SEARCH PRODUCTS
    search_patterns = ["find", "search", "show", "looking", "want", "products", "items"]
    
    if any(pattern in user_lower for pattern in search_patterns):
        stop_words = {"what", "show", "find", "me", "i", "want", "can", "you", "looking", "for", "search", "a", "the"}
        
        query_words = []
        for word in user_message.lower().split():
            clean_word = word.strip('.,!?;:')
            if clean_word and clean_word not in stop_words and len(clean_word) > 2:
                query_words.append(clean_word)
        
        query = " ".join(query_words) if query_words else ""
        products = db_search_products(db, query) if query else db.query(Product).limit(10).all()
        
        if products:
            update_last_shown_products(session_id, products)
            session["booking_stage"] = "initial"
            response = f"🔍 Found {len(products)} item(s):\n\n"
            for idx, product in enumerate(products[:12], 1):
                stock_status = "✅" if product.stock > 0 else "❌"
                response += f"{idx}. **{product.name}** - ₹{product.price} {stock_status}\n"
            response += "\nWhich would you like? (Say 'first', 'second', or 'last')"
        else:
            response = f"Sorry, no results for '{query}'. Try another search!"
        
        action = {"intent": "search", "query": query, "results_count": len(products) if products else 0}
        log_action(db, "search", "success", {"query": query}, {"results_count": len(products) if products else 0}, user_message=user_message)
        return response, action, ["search_products"]
    
    # GREETINGS
    greetings = {
        "hello": "👋 Hi! Welcome to our store. What would you like to buy?",
        "hi": "👋 Hi there! How can I help you today?",
        "hey": "👋 Hey! What are you looking for?",
        "thanks": "😊 You're welcome! Anything else?",
        "thank you": "💝 Thanks for shopping! Need anything else?",
        "help": ("I can help you with:\n\n"
                "🔍 **Search**: 'Show me shirts' or 'Show all'\n"
                "👕 **Clothing**: 'Shirt', 'Saree', 'Dress', 'Tops', 'Jeans'\n"
                "📦 **Browse**: 'Show all' or pick 'First', 'Second'\n"
                "🛒 **Complete**: Full booking flow with color, size, address, payment\n\n"
                "What would you like?"),
    }
    
    for greeting, response_text in greetings.items():
        if greeting in user_lower:
            session["booking_stage"] = "initial"
            action = {"intent": "greeting", "type": greeting}
            log_action(db, "chat", "success", {"message": user_message, "intent": "greeting"},
                      {"greeting": greeting}, user_message=user_message)
            return response_text, action, []
    
    # DEFAULT
    response = ("I'm not sure what you need. Try:\n\n"
               "📦 **'Show all'** - browse all products\n"
               "👕 **'Show me shirts'** - search for clothing\n"
               "🎯 **'First' or 'Second'** - pick from list\n\n"
               "What would you like?")
    action = {"intent": "unclear"}
    log_action(db, "chat", "success", {"message": user_message, "intent": "unclear"},
              {"response": "clarification_needed"}, user_message=user_message)
    return response, action, []
