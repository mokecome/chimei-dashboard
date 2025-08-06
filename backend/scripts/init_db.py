"""
Database initialization script.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import create_tables, drop_tables, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.models.label import ProductLabel, FeedbackCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with tables and default data."""
    logger.info("Initializing database...")
    
    # Create tables
    create_tables()
    logger.info("Database tables created")
    
    # Create default admin user
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@chimei.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@chimei.com",
                password=get_password_hash("admin123"),
                name="系統管理員",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created: admin@chimei.com / admin123")
        
        # Create default product labels
        default_products = [
            "水餃", "包子", "蒸餃", "鍋貼", "湯圓", "餛飩",
            "蔥油餅", "春捲", "蘿蔔糕", "年糕", "芝麻湯圓",
            "花生湯圓", "紅豆湯圓", "抹茶湯圓", "巧克力湯圓", "無"
        ]
        
        for product_name in default_products:
            existing = db.query(ProductLabel).filter(ProductLabel.name == product_name).first()
            if not existing:
                product_label = ProductLabel(
                    name=product_name,
                    description=f"{product_name}產品",
                    is_active=True,
                    created_by=admin_user.id
                )
                db.add(product_label)
        
        # Create default feedback categories
        default_categories = [
            "產品規格", "調理方式", "通路物流", "包裝問題", 
            "口味回饋", "保存方式", "營養成分", "過敏資訊",
            "客服諮詢", "退換貨", "促銷活動", "其他"
        ]
        
        for category_name in default_categories:
            existing = db.query(FeedbackCategory).filter(FeedbackCategory.name == category_name).first()
            if not existing:
                feedback_category = FeedbackCategory(
                    name=category_name,
                    description=f"{category_name}相關回饋",
                    is_active=True,
                    created_by=admin_user.id
                )
                db.add(feedback_category)
        
        db.commit()
        logger.info("Default data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating default data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """Reset database by dropping and recreating all tables."""
    logger.warning("Resetting database - all data will be lost!")
    
    # Drop all tables
    drop_tables()
    logger.info("All tables dropped")
    
    # Recreate tables and default data
    init_database()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument("--reset", action="store_true", help="Reset database (WARNING: deletes all data)")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        init_database()
    
    logger.info("Database initialization completed")