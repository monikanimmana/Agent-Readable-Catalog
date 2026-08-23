"""Conversation context management for tracking shown products and resolving references."""
import uuid
from sqlalchemy.orm import Session
from database import ConversationContext, Product
from typing import List, Optional, Dict, Any


def generate_session_id() -> str:
    """Generate a unique session ID for a new conversation."""
    return str(uuid.uuid4())


def get_or_create_session(db: Session, session_id: Optional[str] = None) -> str:
    """Get existing session or create a new one."""
    if not session_id:
        session_id = generate_session_id()
    
    # Ensure the session exists in the database
    ctx = db.query(ConversationContext).filter(
        ConversationContext.session_id == session_id
    ).first()
    
    if not ctx:
        ctx = ConversationContext(session_id=session_id, last_shown_products=None)
        db.add(ctx)
        db.commit()
    
    return session_id


def update_shown_products(
    db: Session,
    session_id: str,
    products: List[Product],
    search_query: str
) -> None:
    """Update the conversation context with the products that were just shown."""
    # Format products with indices
    shown_products = [
        {
            "index": i + 1,
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "category": product.category
        }
        for i, product in enumerate(products)
    ]
    
    ctx = db.query(ConversationContext).filter(
        ConversationContext.session_id == session_id
    ).first()
    
    if ctx:
        ctx.last_shown_products = shown_products
        ctx.last_search_query = search_query
        db.commit()


def get_last_shown_products(db: Session, session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get the products that were last shown in this conversation."""
    ctx = db.query(ConversationContext).filter(
        ConversationContext.session_id == session_id
    ).first()
    
    if ctx:
        return ctx.last_shown_products
    return None


def resolve_product_reference(
    db: Session,
    session_id: str,
    user_message: str
) -> Optional[Product]:
    """
    Try to resolve a product reference like 'second', 'that one', 'the first product', etc.
    
    Returns the Product object if found, None otherwise.
    """
    user_lower = user_message.lower().strip()
    last_products = get_last_shown_products(db, session_id)
    
    if not last_products:
        return None
    
    # Map ordinal words to indices
    ordinal_map = {
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
        "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
        "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5,
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "#1": 1, "#2": 2, "#3": 3, "#4": 4, "#5": 5
    }
    
    # Check for ordinal references
    for ordinal, index in ordinal_map.items():
        if ordinal in user_lower:
            # Find the product with this index
            for prod_info in last_products:
                if prod_info["index"] == index:
                    return db.query(Product).filter(Product.id == prod_info["id"]).first()
    
    # Check for "that one", "it", "this one", "the last one"
    if any(phrase in user_lower for phrase in ["that one", "that", "it", "this one", "the last one"]):
        # Get the last product from the list
        if last_products:
            last_prod_info = last_products[-1]
            return db.query(Product).filter(Product.id == last_prod_info["id"]).first()
    
    # Check for product name match
    for prod_info in last_products:
        product_name_lower = prod_info["name"].lower()
        if product_name_lower in user_lower or product_name_lower.split()[0] in user_lower:
            return db.query(Product).filter(Product.id == prod_info["id"]).first()
    
    return None


def build_context_for_prompt(db: Session, session_id: str) -> str:
    """
    Build context string to pass to Gemini with information about the last shown products.
    Used in the system prompt to help the agent resolve references.
    """
    last_products = get_last_shown_products(db, session_id)
    
    if not last_products:
        return ""
    
    context = "\n\nRecent product list shown to user:\n"
    for prod in last_products:
        status = "✓ In Stock" if prod["stock"] > 0 else "✗ Out of Stock"
        context += f"{prod['index']}. {prod['name']} (₹{prod['price']}) - {status}\n"
    
    context += "\nIf user refers to items by position (1st, 2nd, third, 'that one', 'it'), resolve to the correct product from above."
    
    return context
