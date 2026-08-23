"""Audit logging for all actions."""
from sqlalchemy.orm import Session
from database import AuditLog
from typing import Dict, Any, Optional, List
from datetime import datetime


def log_action(
    db: Session,
    action_type: str,
    status: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    razorpay_order_id: Optional[str] = None,
    user_message: Optional[str] = None,
) -> AuditLog:
    """
    Log an action to the audit trail.
    
    Args:
        db: Database session
        action_type: Type of action (search, check_stock, initiate_purchase, payment_success, payment_failed, blocked)
        status: Status (success, failed, blocked)
        input_data: Input parameters as dict
        output_data: Output/result as dict
        razorpay_order_id: Optional Razorpay order ID
        user_message: Optional user's original message/intent
    
    Returns:
        The created AuditLog entry
    """
    log_entry = AuditLog(
        action_type=action_type,
        status=status,
        input_data=input_data,
        output_data=output_data,
        razorpay_order_id=razorpay_order_id,
        user_message=user_message,
        timestamp=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_audit_logs(
    db: Session,
    action_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[AuditLog]:
    """
    Retrieve audit logs, most recent first.
    
    Args:
        db: Database session
        action_type: Optional filter by action type
        status: Optional filter by status
        limit: Max number of results
    
    Returns:
        List of audit log entries
    """
    query = db.query(AuditLog)
    
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    if status:
        query = query.filter(AuditLog.status == status)
    
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_audit_log_by_order_id(db: Session, order_id: str) -> Optional[AuditLog]:
    """Get audit log entry by Razorpay order ID."""
    return db.query(AuditLog).filter(AuditLog.razorpay_order_id == order_id).first()
