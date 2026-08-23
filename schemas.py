"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProductBase(BaseModel):
    """Base product schema."""
    name: str
    description: str
    price: float
    stock: int
    category: str
    variants: Optional[Dict[str, Any]] = {}


class Product(ProductBase):
    """Product with ID."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """Search result response."""
    products: List[Product]
    query: str


class StockCheckResult(BaseModel):
    """Stock check result."""
    product_id: int
    product_name: str
    in_stock: bool
    quantity: int


class PriceResult(BaseModel):
    """Price check result."""
    product_id: int
    product_name: str
    price: float


class PurchaseInitiation(BaseModel):
    """Purchase initiation result."""
    order_id: str
    status: str  # "success", "failed", "blocked"
    message: str
    amount: float
    product_id: int
    quantity: int


class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: int
    timestamp: datetime
    action_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    razorpay_order_id: Optional[str] = None
    status: str
    user_message: Optional[str] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Chat/agent request."""
    message: str
    budget: Optional[float] = None  # Optional budget constraint in INR
    session_id: Optional[str] = None  # Client session identifier for context tracking


class ChatResponse(BaseModel):
    """Chat/agent response."""
    reply: str
    audit_entry: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[str]] = None
    session_id: Optional[str] = None  # Session ID for the client to track
