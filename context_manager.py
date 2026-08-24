"""Session management with in-memory conversation history."""
from typing import Dict, List, Any, Optional

# In-memory storage for conversations (sufficient for demo/hackathon)
# Structure: { session_id: { "messages": [...], "last_shown_products": [...], "selected_product": {...}, "address": "..." } }
conversations: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str) -> Dict[str, Any]:
    """Get or create a session."""
    if session_id not in conversations:
        conversations[session_id] = {
            "messages": [],
            "last_shown_products": [],
            "selected_product": None,
            "selected_color": None,
            "selected_size": None,
            "address": None,
            "payment_method": None,
            "booking_stage": "initial"  # initial, asking_color, asking_size, asking_address, asking_payment, confirmed
        }
    return conversations[session_id]


def add_message(session_id: str, role: str, content: str) -> None:
    """Add a message to conversation history."""
    session = get_session(session_id)
    session["messages"].append({"role": role, "content": content})


def update_last_shown_products(session_id: str, products: List[Dict[str, Any]]) -> None:
    """Update the last shown products for a session."""
    session = get_session(session_id)
    session["last_shown_products"] = [
        {
            "index": i + 1,
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
        }
        for i, p in enumerate(products)
    ]


def get_last_shown_products(session_id: str) -> List[Dict[str, Any]]:
    """Get last shown products."""
    session = get_session(session_id)
    return session["last_shown_products"]


def get_conversation_history(session_id: str) -> List[Dict[str, str]]:
    """Get full conversation history."""
    session = get_session(session_id)
    return session["messages"]


def resolve_product_reference(user_message: str, last_shown_products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Resolve product references like "first", "second", "that one", "it", "the last one".
    
    Returns the product dict if found, None otherwise.
    """
    if not last_shown_products:
        return None
    
    user_lower = user_message.lower().strip()
    
    # Ordinal patterns: "first", "second", "third", etc.
    ordinals = {
        "first": 0,
        "second": 1,
        "third": 2,
        "fourth": 3,
        "fifth": 4,
        "sixth": 5,
        "seventh": 6,
        "eighth": 7,
        "ninth": 8,
        "tenth": 9,
    }
    
    for ordinal, index in ordinals.items():
        if ordinal in user_lower:
            if index < len(last_shown_products):
                return last_shown_products[index]
    
    # Numeric patterns: "#1", "#2", "1.", "2.", etc.
    import re
    numbers = re.findall(r"#?(\d+)", user_message)
    if numbers:
        idx = int(numbers[0]) - 1  # Convert to 0-based index
        if 0 <= idx < len(last_shown_products):
            return last_shown_products[idx]
    
    # Relative patterns: "last", "latest", "previous", "that one", "it"
    relative_patterns = ["last", "latest", "previous"]
    for pattern in relative_patterns:
        if pattern in user_lower:
            return last_shown_products[-1]  # Return last product
    
    # Generic patterns: "that", "it", "this one"
    generic_patterns = ["that one", "that", "it", "this one", "this"]
    for pattern in generic_patterns:
        if pattern in user_lower:
            if len(last_shown_products) == 1:
                return last_shown_products[0]
            # If multiple products, return the first (most likely what they mean)
            return last_shown_products[0]
    
    return None


def set_selected_product(session_id: str, product_id: int, product_name: str) -> None:
    """Track which product user is considering."""
    session = get_session(session_id)
    session["selected_product"] = {
        "id": product_id,
        "name": product_name,
        "color": None,
        "size": None
    }
    session["awaiting_confirmation"] = False


def set_product_variant(session_id: str, color: Optional[str] = None, size: Optional[str] = None) -> None:
    """Store selected color/size for product."""
    session = get_session(session_id)
    if session["selected_product"]:
        if color:
            session["selected_product"]["color"] = color
        if size:
            session["selected_product"]["size"] = size


def set_address(session_id: str, address: str) -> None:
    """Store delivery address."""
    session = get_session(session_id)
    session["address"] = address


def set_awaiting_confirmation(session_id: str, waiting: bool) -> None:
    """Mark if we're waiting for user confirmation before booking."""
    session = get_session(session_id)
    session["awaiting_confirmation"] = waiting


def get_selected_product(session_id: str) -> Optional[Dict[str, Any]]:
    """Get the product user is currently considering."""
    session = get_session(session_id)
    return session["selected_product"]


def get_address(session_id: str) -> Optional[str]:
    """Get stored address."""
    session = get_session(session_id)
    return session["address"]


def is_awaiting_confirmation(session_id: str) -> bool:
    """Check if waiting for confirmation."""
    session = get_session(session_id)
    return session["awaiting_confirmation"]

