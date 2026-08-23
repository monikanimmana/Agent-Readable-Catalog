"""Razorpay integration with guardrails."""
import razorpay
import os
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from database import Product
from search import get_product_by_id, check_product_stock, get_product_price
from audit import log_action


class RazorpayGuardedClient:
    """Razorpay client with safety guardrails."""
    
    def __init__(self):
        """Initialize Razorpay client with test mode keys."""
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        
        if not self.key_id or not self.key_secret:
            raise ValueError(
                "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env"
            )
        
        # Ensure test mode keys
        if not self.key_id.startswith("rzp_test_"):
            raise ValueError("Only test mode keys (rzp_test_*) are allowed")
        
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
    
    def initiate_purchase(
        self,
        db: Session,
        product_id: int,
        quantity: int,
        budget_constraint: Optional[float] = None,
        user_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate a purchase with guardrails.
        
        GUARDRAILS ENFORCED IN CODE:
        1. Product must exist
        2. Stock must have been checked and must be available
        3. Price must not exceed budget constraint if provided
        4. Amount is converted to paise for Razorpay
        
        Args:
            db: Database session
            product_id: Product ID to purchase
            quantity: Quantity to purchase
            budget_constraint: Optional max price in INR (from user message)
            user_message: Original user intent for audit trail
        
        Returns:
            Dict with order_id, status, and message
        """
        # GUARDRAIL 1: Product must exist
        product = get_product_by_id(db, product_id)
        if not product:
            blocked_result = {
                "order_id": None,
                "status": "blocked",
                "message": f"Product {product_id} not found",
            }
            log_action(
                db=db,
                action_type="initiate_purchase",
                status="blocked",
                input_data={
                    "product_id": product_id,
                    "quantity": quantity,
                    "budget": budget_constraint
                },
                output_data=blocked_result,
                user_message=user_message
            )
            return blocked_result
        
        # GUARDRAIL 2: Stock must be available (this check is mandatory before purchase)
        stock_check = check_product_stock(db, product_id)
        if not stock_check["in_stock"]:
            blocked_result = {
                "order_id": None,
                "status": "blocked",
                "message": f"Product '{product.name}' is out of stock (0 units available)",
            }
            log_action(
                db=db,
                action_type="initiate_purchase",
                status="blocked",
                input_data={
                    "product_id": product_id,
                    "quantity": quantity,
                    "stock_available": stock_check["quantity"]
                },
                output_data=blocked_result,
                user_message=user_message
            )
            return blocked_result
        
        # Cannot purchase more than available
        if quantity > stock_check["quantity"]:
            blocked_result = {
                "order_id": None,
                "status": "blocked",
                "message": f"Only {stock_check['quantity']} units of '{product.name}' available, but {quantity} requested",
            }
            log_action(
                db=db,
                action_type="initiate_purchase",
                status="blocked",
                input_data={
                    "product_id": product_id,
                    "quantity_requested": quantity,
                    "quantity_available": stock_check["quantity"]
                },
                output_data=blocked_result,
                user_message=user_message
            )
            return blocked_result
        
        # GUARDRAIL 3: Budget constraint check (in-code, not trusting agent judgment)
        total_price = product.price * quantity
        if budget_constraint is not None and total_price > budget_constraint:
            blocked_result = {
                "order_id": None,
                "status": "blocked",
                "message": f"Purchase blocked: Total price ₹{total_price:.2f} exceeds your budget of ₹{budget_constraint:.2f}",
            }
            log_action(
                db=db,
                action_type="initiate_purchase",
                status="blocked",
                input_data={
                    "product_id": product_id,
                    "quantity": quantity,
                    "total_price": total_price,
                    "budget_constraint": budget_constraint
                },
                output_data=blocked_result,
                user_message=user_message
            )
            return blocked_result
        
        # All guardrails passed, create Razorpay order
        try:
            amount_paise = int(total_price * 100)  # Convert to paise
            
            order_data = {
                "amount": amount_paise,  # in paise
                "currency": "INR",
                "notes": {
                    "product_id": product_id,
                    "product_name": product.name,
                    "quantity": quantity,
                }
            }
            
            razorpay_order = self.client.order.create(data=order_data)
            order_id = razorpay_order["id"]
            
            success_result = {
                "order_id": order_id,
                "status": "success",
                "message": f"Order created for {quantity}x '{product.name}' at ₹{total_price:.2f}",
                "product_id": product_id,
                "quantity": quantity,
                "amount": total_price,
            }
            
            log_action(
                db=db,
                action_type="initiate_purchase",
                status="success",
                input_data={
                    "product_id": product_id,
                    "quantity": quantity,
                    "total_price": total_price,
                },
                output_data=success_result,
                razorpay_order_id=order_id,
                user_message=user_message
            )
            
            return success_result
            
        except Exception as e:
            error_result = {
                "order_id": None,
                "status": "failed",
                "message": f"Failed to create Razorpay order: {str(e)}",
            }
            log_action(
                db=db,
                action_type="initiate_purchase",
                status="failed",
                input_data={
                    "product_id": product_id,
                    "quantity": quantity,
                },
                output_data={"error": str(e)},
                user_message=user_message
            )
            return error_result


# TEST MODE PAYMENT VALIDATION
def validate_test_payment(payment_id: str, order_id: str, signature: str, client: razorpay.Client) -> bool:
    """
    Validate a test mode payment signature.
    
    For test payments, Razorpay provides these test card numbers:
    - Success: 4111 1111 1111 1111
    - Decline: 4222 2222 2222 2222
    """
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
        return True
    except razorpay.BadRequestsError:
        return False


def get_razorpay_client() -> RazorpayGuardedClient:
    """Factory function to get initialized Razorpay client."""
    return RazorpayGuardedClient()
