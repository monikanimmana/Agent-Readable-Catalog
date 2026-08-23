"""Session management with in-memory conversation history."""
from typing import Dict, List, Any, Optional

# In-memory storage for conversations (sufficient for demo/hackathon)
# Structure: { session_id: { "messages": [...], "last_shown_products": [...] } }
conversations: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str) -> Dict[str, Any]:
    """Get or create a session."""
    if session_id not in conversations:
        conversations[session_id] = {
            "messages": [],
            "last_shown_products": []
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

