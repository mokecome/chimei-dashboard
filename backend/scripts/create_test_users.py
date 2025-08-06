#!/usr/bin/env python3
"""
創建測試用戶數據腳本
"""
import sys
import os
from datetime import datetime

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
import uuid

def create_test_users():
    """創建測試用戶數據"""
    
    # 創建數據庫連接
    db = SessionLocal()
    
    try:
        # 檢查是否已有測試用戶（除了admin）
        existing_users = db.query(User).filter(User.email != "admin@chimei.com").count()
        if existing_users > 0:
            print(f"✅ 數據庫中已有 {existing_users} 個非admin用戶")
            return
        
        # 測試用戶數據
        test_users = [
            {
                "email": "manager01@chimei.com",
                "name": "經理王小明",
                "password": "manager123",
                "role": UserRole.MANAGER,
                "is_active": True
            },
            {
                "email": "manager02@chimei.com", 
                "name": "經理李小華",
                "password": "manager123",
                "role": UserRole.MANAGER,
                "is_active": True
            },
            {
                "email": "operator01@chimei.com",
                "name": "操作員張小芳",
                "password": "operator123", 
                "role": UserRole.OPERATOR,
                "is_active": True
            },
            {
                "email": "operator02@chimei.com",
                "name": "操作員陳小強",
                "password": "operator123",
                "role": UserRole.OPERATOR,
                "is_active": True
            },
            {
                "email": "operator03@chimei.com",
                "name": "操作員林小美",
                "password": "operator123",
                "role": UserRole.OPERATOR,
                "is_active": False  # 停用用戶
            },
            {
                "email": "viewer01@chimei.com",
                "name": "觀看者劉小君",
                "password": "viewer123",
                "role": UserRole.VIEWER,
                "is_active": True
            },
            {
                "email": "viewer02@chimei.com",
                "name": "觀看者黃小龍",
                "password": "viewer123", 
                "role": UserRole.VIEWER,
                "is_active": True
            }
        ]
        
        created_count = 0
        
        for user_data in test_users:
            # 檢查郵箱是否已存在
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                print(f"⚠️ 用戶 {user_data['email']} 已存在，跳過")
                continue
            
            # 創建新用戶
            user = User(
                id=str(uuid.uuid4()),
                email=user_data["email"],
                name=user_data["name"],
                password=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(user)
            created_count += 1
            print(f"✅ 創建用戶: {user_data['name']} ({user_data['email']}) - {user_data['role'].value}")
        
        # 提交更改
        db.commit()
        print(f"\n🎉 成功創建 {created_count} 個測試用戶！")
        
        # 顯示所有用戶統計
        total_users = db.query(User).count()
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        manager_count = db.query(User).filter(User.role == UserRole.MANAGER).count()
        operator_count = db.query(User).filter(User.role == UserRole.OPERATOR).count()
        viewer_count = db.query(User).filter(User.role == UserRole.VIEWER).count()
        active_count = db.query(User).filter(User.is_active == True).count()
        
        print(f"\n📊 用戶統計:")
        print(f"   總用戶數: {total_users}")
        print(f"   管理員: {admin_count}")
        print(f"   經理: {manager_count}")
        print(f"   操作員: {operator_count}")
        print(f"   觀看者: {viewer_count}")
        print(f"   活躍用戶: {active_count}")
        
    except Exception as e:
        print(f"❌ 創建測試用戶失敗: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 開始創建測試用戶數據...")
    create_test_users()
    print("✨ 測試用戶數據創建完成！")