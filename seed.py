"""Seed the database with realistic products."""
from database import SessionLocal, init_db, Product
from datetime import datetime

# Initialize database
init_db()
db = SessionLocal()

# Sample products spanning multiple categories with varied stock levels
SEED_PRODUCTS = [
    {
        "name": "Premium Cotton T-Shirt",
        "description": "Comfortable 100% organic cotton t-shirt, perfect for daily wear",
        "price": 499.0,
        "stock": 25,
        "category": "Apparel",
        "variants": {
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "colors": ["White", "Black", "Navy Blue", "Grey"]
        }
    },
    {
        "name": "Wireless Bluetooth Headphones",
        "description": "Noise-cancelling wireless headphones with 30-hour battery life",
        "price": 3999.0,
        "stock": 5,
        "category": "Electronics",
        "variants": {
            "colors": ["Black", "Silver", "Rose Gold"],
            "sizes": ["One Size"]
        }
    },
    {
        "name": "Stainless Steel Water Bottle",
        "description": "Keeps drinks cold for 24 hours or hot for 12 hours. BPA-free.",
        "price": 799.0,
        "stock": 45,
        "category": "Accessories",
        "variants": {
            "sizes": ["500ml", "750ml", "1L"],
            "colors": ["Silver", "Black", "Blue"]
        }
    },
    {
        "name": "Running Shoes - Pro Edition",
        "description": "Lightweight, breathable running shoes with advanced cushioning",
        "price": 4999.0,
        "stock": 0,
        "category": "Footwear",
        "variants": {
            "sizes": ["6", "7", "8", "9", "10", "11", "12"],
            "colors": ["White/Black", "Blue/Orange"]
        }
    },
    {
        "name": "Organic Green Tea (25 bags)",
        "description": "Premium organic green tea from Darjeeling, antioxidant-rich",
        "price": 349.0,
        "stock": 120,
        "category": "Beverages",
        "variants": {
            "types": ["Classic", "Jasmine", "Honey Lemon"],
            "sizes": ["25 bags"]
        }
    },
    {
        "name": "Yoga Mat - Premium Non-Slip",
        "description": "6mm thick yoga mat with non-slip surface, eco-friendly TPE material",
        "price": 1299.0,
        "stock": 18,
        "category": "Sports",
        "variants": {
            "colors": ["Purple", "Black", "Green", "Pink"],
            "sizes": ["173cm x 61cm"]
        }
    },
    {
        "name": "Smart Watch Fitness Tracker",
        "description": "Monitor heart rate, sleep, steps, calories. Water-resistant up to 50m",
        "price": 5999.0,
        "stock": 2,
        "category": "Electronics",
        "variants": {
            "colors": ["Black", "Silver", "Gold"],
            "sizes": ["One Size"]
        }
    },
    {
        "name": "Bamboo Cutting Board Set",
        "description": "Set of 3 bamboo cutting boards with storage case",
        "price": 899.0,
        "stock": 34,
        "category": "Kitchen",
        "variants": {
            "sizes": ["Set of 3"],
            "colors": ["Natural Bamboo"]
        }
    },
    {
        "name": "USB-C Fast Charging Cable",
        "description": "Durable 2m USB-C to USB-C cable, 100W fast charging support",
        "price": 299.0,
        "stock": 200,
        "category": "Electronics",
        "variants": {
            "lengths": ["1m", "2m", "3m"],
            "colors": ["Black", "White"]
        }
    },
    {
        "name": "Portable Solar Power Bank",
        "description": "20000mAh solar-powered portable charger with dual USB ports",
        "price": 2499.0,
        "stock": 11,
        "category": "Electronics",
        "variants": {
            "colors": ["Black", "Green"],
            "sizes": ["One Size"]
        }
    },
    {
        "name": "Adjustable Dumbbell Set",
        "description": "5-25kg adjustable dumbbells with stand, perfect for home gym",
        "price": 8999.0,
        "stock": 6,
        "category": "Sports",
        "variants": {
            "colors": ["Black"],
            "sizes": ["5-25kg"]
        }
    },
    {
        "name": "Natural Bamboo Toothbrush (Pack of 4)",
        "description": "Eco-friendly bamboo toothbrushes with soft bristles",
        "price": 199.0,
        "stock": 67,
        "category": "Personal Care",
        "variants": {
            "colors": ["Natural"],
            "packs": ["4-pack"]
        }
    },
    {
        "name": "Leather Messenger Bag",
        "description": "Premium genuine leather messenger bag, perfect for office or travel",
        "price": 6999.0,
        "stock": 8,
        "category": "Bags",
        "variants": {
            "colors": ["Brown", "Black", "Tan"],
            "sizes": ["One Size"]
        }
    },
    {
        "name": "Indoor Plant - Monstera",
        "description": "Beautiful Monstera Deliciosa plant with ceramic pot included",
        "price": 1599.0,
        "stock": 12,
        "category": "Plants",
        "variants": {
            "sizes": ["Small", "Medium", "Large"],
            "pots": ["Ceramic - White", "Ceramic - Terracotta"]
        }
    },
    {
        "name": "Noise-Cancelling Earplugs",
        "description": "Reusable noise-cancelling earplugs, perfect for travel and focus",
        "price": 1299.0,
        "stock": 0,
        "category": "Accessories",
        "variants": {
            "sizes": ["S", "M", "L"],
            "colors": ["Transparent"]
        }
    },
    {
        "name": "Mechanical Keyboard - RGB",
        "description": "Mechanical gaming keyboard with RGB lighting and hot-swap switches",
        "price": 7499.0,
        "stock": 3,
        "category": "Electronics",
        "variants": {
            "colors": ["Black"],
            "switches": ["Blue", "Brown", "Red"]
        }
    },
    {
        "name": "Sunscreen SPF 50+ Spray",
        "description": "Broad-spectrum water-resistant sunscreen, reef-safe formula",
        "price": 599.0,
        "stock": 55,
        "category": "Personal Care",
        "variants": {
            "sizes": ["200ml", "400ml"],
            "types": ["Spray", "Lotion"]
        }
    },
    {
        "name": "Bluetooth Speaker - Portable",
        "description": "Waterproof portable Bluetooth speaker with 12-hour battery",
        "price": 2299.0,
        "stock": 9,
        "category": "Electronics",
        "variants": {
            "colors": ["Black", "Blue", "Red"],
            "sizes": ["One Size"]
        }
    },
]

# Clear existing products
db.query(Product).delete()
db.commit()

# Insert seed products
for product_data in SEED_PRODUCTS:
    product = Product(**product_data)
    db.add(product)

db.commit()
print(f"✅ Seeded {len(SEED_PRODUCTS)} products into the database")
db.close()
