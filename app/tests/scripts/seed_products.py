from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.products.models import Product

def seed_products():
    db = SessionLocal()
    try:
        products = [
            Product(name="Laptop", description="High-performance laptop", price=999.99, stock=10, category="Electronics"),
            Product(name="Headphones", description="Wireless headphones", price=89.99, stock=50, category="Electronics"),
            Product(name="T-Shirt", description="Cotton t-shirt", price=19.99, stock=100, category="Clothing"),
        ]
        db.add_all(products)
        db.commit()
        print("Products seeded successfully")
    except Exception as e:
        db.rollback()
        print(f"Error seeding products: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_products()