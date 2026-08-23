"""Database models and setup."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Get database URL from env, default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./catalog.db")

# Create engine with appropriate settings for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    """Product catalog model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    price = Column(Float)  # Price in INR
    stock = Column(Integer)
    category = Column(String, index=True)
    variants = Column(JSON)  # {"sizes": ["S", "M", "L"], "colors": ["red", "blue"]}
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for all actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action_type = Column(String, index=True)  # search, check_stock, initiate_purchase, payment_success, payment_failed, blocked
    input_data = Column(JSON)  # Input parameters
    output_data = Column(JSON)  # Output/result
    razorpay_order_id = Column(String, nullable=True, index=True)
    status = Column(String, index=True)  # success, failed, blocked
    user_message = Column(String, nullable=True)  # The user's original intent


class ConversationContext(Base):
    """Store conversation context for resolving references like 'second', 'that one', etc."""
    __tablename__ = "conversation_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # Client session identifier
    last_shown_products = Column(JSON)  # List of products with indices: [{"index": 1, "id": 1, "name": "...", "price": ...}, ...]
    last_search_query = Column(String, nullable=True)  # What query returned these products
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
