#!/usr/bin/env python3
"""
創建測試用戶腳本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_users():
    """創建多個測試用戶"""
    db = SessionLocal()
    
    test_users = [
        {
            "email": "test@test.com",
            "password": "test123",
            "name": "測試用戶",
            "role": UserRole.ADMIN
        },
        {
            "email": "admin@admin.com", 
            "password": "admin",
            "name": "管理員",
            "role": UserRole.ADMIN
        },
        {
            "email": "user@user.com",
            "password": "123456",
            "name": "普通用戶", 
            "role": UserRole.VIEWER
        }
    ]
    
    try:
        for user_data in test_users:
            # 檢查用戶是否已存在
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                logger.info(f"用戶 {user_data['email']} 已存在，跳過")
                continue
                
            # 創建新用戶
            new_user = User(
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                name=user_data["name"],
                role=user_data["role"],
                is_active=True
            )
            db.add(new_user)
            logger.info(f"創建用戶: {user_data['email']} / {user_data['password']}")
        
        db.commit()
        logger.info("測試用戶創建完成")
        
        # 顯示所有用戶
        users = db.query(User).all()
        logger.info("目前所有用戶:")
        for user in users:
            logger.info(f"  {user.email} ({user.role.value}) - Active: {user.is_active}")
            
    except Exception as e:
        logger.error(f"創建用戶時出錯: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()