"""Seed the database with realistic products - Clothing Focused."""
from database import SessionLocal, init_db, Product
from datetime import datetime

# Initialize database
init_db()
db = SessionLocal()

SEED_PRODUCTS = [
    # ===== SHIRTS (Plain, Party, Formal) =====
    {
        "name": "Plain Cotton Shirt - Blue",
        "description": "Classic plain cotton shirt for casual daily wear",
        "price": 499.0,
        "stock": 25,
        "category": "Shirt",
        "variants": {
            "type": "Plain",
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "colors": ["White", "Blue", "Black", "Grey"]
        }
    },
    {
        "name": "Party Shirt - Printed",
        "description": "Stylish printed shirt perfect for parties and gatherings",
        "price": 799.0,
        "stock": 18,
        "category": "Shirt",
        "variants": {
            "type": "Party",
            "sizes": ["S", "M", "L", "XL"],
            "colors": ["Red", "Green", "Purple", "Orange"]
        }
    },
    {
        "name": "Formal White Shirt",
        "description": "Premium formal shirt for office and formal occasions",
        "price": 1299.0,
        "stock": 15,
        "category": "Shirt",
        "variants": {
            "type": "Formal",
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "colors": ["White", "Light Blue", "Light Pink"]
        }
    },
    
    # ===== T-SHIRTS (Plain, Graphic) =====
    {
        "name": "Plain T-Shirt",
        "description": "Comfortable 100% organic cotton t-shirt, perfect for daily wear",
        "price": 399.0,
        "stock": 35,
        "category": "T-Shirt",
        "variants": {
            "type": "Plain",
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "colors": ["White", "Black", "Navy Blue", "Grey", "Red"]
        }
    },
    {
        "name": "Graphic Printed T-Shirt",
        "description": "Trendy graphic printed t-shirt with modern designs",
        "price": 599.0,
        "stock": 22,
        "category": "T-Shirt",
        "variants": {
            "type": "Graphic",
            "sizes": ["S", "M", "L", "XL"],
            "colors": ["Black", "White", "Navy"]
        }
    },

    # ===== SAREES (Kachipuram, Plain, Party, Traditional) =====
    {
        "name": "Kachipuram Silk Saree",
        "description": "Traditional Kachipuram silk saree with zari border",
        "price": 3999.0,
        "stock": 8,
        "category": "Saree",
        "variants": {
            "type": "Kachipuram",
            "sizes": ["One Size"],
            "colors": ["Gold", "Red", "Green", "Purple"]
        }
    },
    {
        "name": "Plain Cotton Saree",
        "description": "Simple yet elegant plain cotton saree for everyday wear",
        "price": 899.0,
        "stock": 20,
        "category": "Saree",
        "variants": {
            "type": "Plain",
            "sizes": ["One Size"],
            "colors": ["White", "Beige", "Grey", "Black"]
        }
    },
    {
        "name": "Party Wear Saree - Embroidered",
        "description": "Stunning embroidered party wear saree for special occasions",
        "price": 5999.0,
        "stock": 5,
        "category": "Saree",
        "variants": {
            "type": "Party Wear",
            "sizes": ["One Size"],
            "colors": ["Red", "Maroon", "Deep Blue"]
        }
    },
    {
        "name": "Traditional Handloom Saree",
        "description": "Authentic handloom saree with traditional weaving patterns",
        "price": 2499.0,
        "stock": 12,
        "category": "Saree",
        "variants": {
            "type": "Traditional",
            "sizes": ["One Size"],
            "colors": ["Maroon", "Navy", "Forest Green"]
        }
    },

    # ===== DRESS =====
    {
        "name": "Casual Summer Dress",
        "description": "Light and comfortable summer dress perfect for hot days",
        "price": 699.0,
        "stock": 16,
        "category": "Dress",
        "variants": {
            "type": "Casual",
            "sizes": ["XS", "S", "M", "L", "XL"],
            "colors": ["Floral", "Solid Blue", "Solid Pink"]
        }
    },
    {
        "name": "Formal Evening Dress",
        "description": "Elegant formal dress for parties and special events",
        "price": 2999.0,
        "stock": 9,
        "category": "Dress",
        "variants": {
            "type": "Formal",
            "sizes": ["S", "M", "L", "XL"],
            "colors": ["Black", "Navy", "Maroon"]
        }
    },

    # ===== TOPS (Short, Long, Chikankari, Traditional, Party) =====
    {
        "name": "Short Sleeve Top",
        "description": "Comfortable short sleeve top for casual wear",
        "price": 499.0,
        "stock": 24,
        "category": "Tops",
        "variants": {
            "type": "Short Sleeve",
            "sizes": ["XS", "S", "M", "L", "XL"],
            "colors": ["White", "Black", "Blue", "Green"]
        }
    },
    {
        "name": "Long Sleeve Top",
        "description": "Versatile long sleeve top, perfect for layering",
        "price": 699.0,
        "stock": 18,
        "category": "Tops",
        "variants": {
            "type": "Long Sleeve",
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "colors": ["Cream", "Black", "Maroon"]
        }
    },
    {
        "name": "Chikankari Embroidered Top",
        "description": "Traditional chikankari embroidered top with delicate work",
        "price": 1299.0,
        "stock": 11,
        "category": "Tops",
        "variants": {
            "type": "Chikankari",
            "sizes": ["S", "M", "L", "XL"],
            "colors": ["White", "Off-White", "Light Blue"]
        }
    },
    {
        "name": "Traditional Ethnic Top",
        "description": "Classic traditional top with ethnic patterns",
        "price": 899.0,
        "stock": 14,
        "category": "Tops",
        "variants": {
            "type": "Traditional",
            "sizes": ["S", "M", "L", "XL"],
            "colors": ["Maroon", "Navy", "Mustard"]
        }
    },
    {
        "name": "Party Wear Sequin Top",
        "description": "Glamorous party wear top with sequins and embellishments",
        "price": 1599.0,
        "stock": 8,
        "category": "Tops",
        "variants": {
            "type": "Party Wear",
            "sizes": ["XS", "S", "M", "L"],
            "colors": ["Black", "Red", "Gold"]
        }
    },

    # ===== JEANS =====
    {
        "name": "Slim Fit Denim Jeans",
        "description": "Classic slim fit jeans with comfortable stretch",
        "price": 1299.0,
        "stock": 20,
        "category": "Jeans",
        "variants": {
            "fit": "Slim Fit",
            "sizes": ["28", "30", "32", "34", "36"],
            "colors": ["Dark Blue", "Light Blue", "Black"]
        }
    },
    {
        "name": "Skinny Fit Blue Jeans",
        "description": "Trendy skinny fit jeans for a modern look",
        "price": 1199.0,
        "stock": 17,
        "category": "Jeans",
        "variants": {
            "fit": "Skinny",
            "sizes": ["26", "28", "30", "32"],
            "colors": ["Dark Blue", "Black", "Blue"]
        }
    },

    # ===== NON-CLOTHING ITEMS =====
    {
        "name": "Wireless Bluetooth Headphones",
        "description": "Noise-cancelling wireless headphones with 30-hour battery",
        "price": 3999.0,
        "stock": 5,
        "category": "Electronics",
        "variants": {
            "colors": ["Black", "Silver"],
            "sizes": ["One Size"]
        }
    },
    {
        "name": "Stainless Steel Water Bottle",
        "description": "Keeps drinks cold for 24 hours or hot for 12 hours",
        "price": 799.0,
        "stock": 45,
        "category": "Accessories",
        "variants": {
            "sizes": ["500ml", "750ml", "1L"],
            "colors": ["Silver", "Black", "Blue"]
        }
    },
    {
        "name": "Running Shoes Pro",
        "description": "Lightweight, breathable running shoes with cushioning",
        "price": 4999.0,
        "stock": 0,
        "category": "Footwear",
        "variants": {
            "sizes": ["6", "7", "8", "9", "10", "11"],
            "colors": ["White", "Black"]
        }
    },
    {
        "name": "Organic Green Tea",
        "description": "Premium organic green tea from Darjeeling",
        "price": 349.0,
        "stock": 120,
        "category": "Beverages",
        "variants": {
            "types": ["Classic", "Jasmine"],
            "sizes": ["25 bags"]
        }
    },
    {
        "name": "Yoga Mat Premium",
        "description": "6mm thick yoga mat with non-slip surface",
        "price": 1299.0,
        "stock": 18,
        "category": "Sports",
        "variants": {
            "colors": ["Purple", "Black", "Green"],
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
