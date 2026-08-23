"""Product search and retrieval layer."""
from sqlalchemy.orm import Session
from database import Product
from typing import List, Optional


def search_products(
    db: Session,
    query: str,
    max_price: Optional[float] = None,
    size: Optional[str] = None,
) -> List[Product]:
    """
    Search products by keyword and optional filters.
    
    Simple keyword matching on name and description.
    Filters by max_price and size if provided.
    
    Args:
        db: Database session
        query: Search query (keyword matching)
        max_price: Optional maximum price filter (INR)
        size: Optional size filter (looks in variants)
    
    Returns:
        List of matching products
    """
    from sqlalchemy import or_
    
    # Start with all products
    search_query = db.query(Product)
    
    # Keyword search on name and description (case-insensitive)
    if query and query.strip():
        keywords = query.strip().lower().split()
        
        # For each keyword, search with OR logic within that keyword
        # But AND logic between keywords (all keywords must match)
        for keyword in keywords:
            # Create variations: singular and plural
            variations = [keyword]
            if keyword.endswith('s') and len(keyword) > 1:
                variations.append(keyword[:-1])  # singular
            elif not keyword.endswith('s'):
                variations.append(keyword + 's')  # plural
            
            # Search using OR for all variations of this keyword
            keyword_filter = or_(
                Product.name.ilike(f"%{variations[0]}%"),
                Product.description.ilike(f"%{variations[0]}%"),
                Product.category.ilike(f"%{variations[0]}%")
            )
            
            # Add other variations with OR
            for var in variations[1:]:
                keyword_filter = or_(
                    keyword_filter,
                    Product.name.ilike(f"%{var}%"),
                    Product.description.ilike(f"%{var}%"),
                    Product.category.ilike(f"%{var}%")
                )
            
            search_query = search_query.filter(keyword_filter)
    
    # Price filter
    if max_price is not None:
        search_query = search_query.filter(Product.price <= max_price)
    
    results = search_query.all()
    
    # Size filter (post-query since it's in JSON)
    if size and size.strip():
        size_lower = size.strip().lower()
        filtered_results = []
        for product in results:
            if product.variants:
                # Check all variant arrays for the size
                variants_str = str(product.variants).lower()
                if size_lower in variants_str:
                    filtered_results.append(product)
            else:
                filtered_results.append(product)
        results = filtered_results
    
    return results


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Get a product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def check_product_stock(db: Session, product_id: int) -> dict:
    """
    Check stock for a product.
    
    Args:
        db: Database session
        product_id: Product ID
    
    Returns:
        Dict with in_stock bool and quantity
    """
    product = get_product_by_id(db, product_id)
    if not product:
        return {"in_stock": False, "quantity": 0, "found": False}
    
    return {
        "in_stock": product.stock > 0,
        "quantity": product.stock,
        "found": True,
        "product_name": product.name
    }


def get_product_price(db: Session, product_id: int) -> dict:
    """
    Get price for a product.
    
    Args:
        db: Database session
        product_id: Product ID
    
    Returns:
        Dict with price in INR
    """
    product = get_product_by_id(db, product_id)
    if not product:
        return {"price": None, "found": False}
    
    return {
        "price": product.price,
        "found": True,
        "product_name": product.name,
        "product_id": product_id
    }
