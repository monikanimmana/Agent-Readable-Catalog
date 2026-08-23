"""Quick test of search functionality."""
from database import SessionLocal, init_db
from search import search_products

init_db()
db = SessionLocal()

# Test search
results = search_products(db, 'shirt', max_price=1000)
print(f'✅ Found {len(results)} products matching "shirt" under ₹1000')
for p in results:
    print(f'  - {p.name}: ₹{p.price}')

# Test search without filters
results2 = search_products(db, 'water')
print(f'\n✅ Found {len(results2)} products matching "water"')
for p in results2:
    print(f'  - {p.name}: ₹{p.price}')

# Test out of stock product
results3 = search_products(db, 'running shoes')
print(f'\n✅ Found {len(results3)} products matching "running shoes"')
for p in results3:
    print(f'  - {p.name}: ₹{p.price}, Stock: {p.stock}')

db.close()
