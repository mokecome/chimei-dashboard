#!/usr/bin/env python3
"""
Initialize default data for the application.
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.label import ProductLabel, FeedbackCategory
from app.core.security import get_password_hash

def init_default_admin():
    """Create default admin user."""
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@chime.com").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            email="admin@chime.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            name="System Administrator",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Created admin user: admin@chime.com / admin123")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def init_product_labels():
    """Create default product labels."""
    db = SessionLocal()
    try:
        # Check if products exist
        existing_count = db.query(ProductLabel).count()
        if existing_count > 0:
            print(f"Product labels already exist ({existing_count} items)")
            return
        
        # Get admin user
        admin = db.query(User).filter(User.email == "admin@chime.com").first()
        if not admin:
            print("Admin user not found, creating product labels without creator")
            return
        
        # Default product labels
        products = [
            ("漢堡包", "經典牛肉漢堡"),
            ("薯條", "黃金脆薯條"),
            ("雞塊", "香酥雞塊"),
            ("飲料", "各式飲品"),
            ("沙拉", "新鮮蔬菜沙拉"),
            ("甜品", "甜點類產品"),
            ("套餐", "組合套餐"),
            ("冰淇淋", "冰淇淋類產品"),
        ]
        
        for name, desc in products:
            product = ProductLabel(
                name=name,
                description=desc,
                is_active=True,
                created_by=admin.id
            )
            db.add(product)
        
        db.commit()
        print(f"Created {len(products)} product labels")
        
    except Exception as e:
        print(f"Error creating product labels: {e}")
        db.rollback()
    finally:
        db.close()

def init_feedback_categories():
    """Create default feedback categories."""
    db = SessionLocal()
    try:
        # Check if categories exist
        existing_count = db.query(FeedbackCategory).count()
        if existing_count > 0:
            print(f"Feedback categories already exist ({existing_count} items)")
            return
        
        # Get admin user
        admin = db.query(User).filter(User.email == "admin@chime.com").first()
        if not admin:
            print("Admin user not found, creating feedback categories without creator")
            return
        
        # Default feedback categories
        categories = [
            ("服務質量", "關於服務人員態度和服務速度的反饋"),
            ("食物質量", "關於食物味道、溫度、新鮮度的反饋"),
            ("環境衛生", "關於餐廳環境、清潔度的反饋"),
            ("價格合理性", "關於產品價格是否合理的反饋"),
            ("等待時間", "關於點餐和取餐等待時間的反饋"),
            ("產品建議", "對新產品或改進產品的建議"),
            ("投訴問題", "具體的投訴和問題反映"),
            ("讚美表揚", "對服務或產品的正面評價"),
        ]
        
        for name, desc in categories:
            category = FeedbackCategory(
                name=name,
                description=desc,
                is_active=True,
                created_by=admin.id
            )
            db.add(category)
        
        db.commit()
        print(f"Created {len(categories)} feedback categories")
        
    except Exception as e:
        print(f"Error creating feedback categories: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Initialize all default data."""
    print("Initializing default data...")
    
    # Create admin user first
    init_default_admin()
    
    # Create default labels
    init_product_labels()
    init_feedback_categories()
    
    print("Default data initialization completed!")

if __name__ == "__main__":
    main()