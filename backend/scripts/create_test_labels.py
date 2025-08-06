#!/usr/bin/env python3
"""
創建測試標籤數據腳本
"""
import sys
import os
from datetime import datetime

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, SessionLocal
from app.models.label import ProductLabel, FeedbackCategory
from app.models.user import User
from sqlalchemy.orm import Session

def create_test_labels():
    """創建測試標籤數據"""
    
    # 創建數據庫連接
    db = SessionLocal()
    
    try:
        # 獲取admin用戶ID作為創建者
        admin_user = db.query(User).filter(User.email == "admin@chimei.com").first()
        if not admin_user:
            print("❌ 未找到admin用戶，請先運行 init_db.py")
            return
        
        # 檢查是否已有測試標籤
        existing_product_labels = db.query(ProductLabel).count()
        existing_feedback_categories = db.query(FeedbackCategory).count()
        
        if existing_product_labels > 0 or existing_feedback_categories > 0:
            print(f"✅ 數據庫中已有標籤數據：{existing_product_labels} 個商品標籤，{existing_feedback_categories} 個回饋分類")
            return
        
        # 測試商品標籤數據
        product_labels_data = [
            {
                "name": "手福饅頭",
                "description": "奇美手福饅頭系列產品",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "冷凍水餃",
                "description": "奇美冷凍水餃系列產品",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "冷凍包子",
                "description": "奇美冷凍包子系列產品",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "湯圓",
                "description": "奇美湯圓系列產品",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "麵條",
                "description": "奇美麵條系列產品",
                "is_active": True,
                "created_by": admin_user.id
            }
        ]
        
        # 測試回饋分類數據
        feedback_categories_data = [
            {
                "name": "通路物流",
                "description": "關於產品配送、物流、通路相關問題",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "食品口味",
                "description": "關於產品口味、味道相關反饋",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "食品保存",
                "description": "關於產品保存方式、保質期相關問題",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "營業時間",
                "description": "關於店面營業時間、服務時間相關問題",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "產品品質",
                "description": "關於產品品質、製作工藝相關反饋",
                "is_active": True,
                "created_by": admin_user.id
            },
            {
                "name": "價格優惠",
                "description": "關於產品價格、促銷活動相關詢問",
                "is_active": True,
                "created_by": admin_user.id
            }
        ]
        
        created_product_count = 0
        created_feedback_count = 0
        
        # 創建商品標籤
        for label_data in product_labels_data:
            # 檢查是否已存在
            existing_label = db.query(ProductLabel).filter(ProductLabel.name == label_data["name"]).first()
            if existing_label:
                print(f"⚠️ 商品標籤 {label_data['name']} 已存在，跳過")
                continue
            
            # 創建新標籤
            label = ProductLabel(
                name=label_data["name"],
                description=label_data["description"],
                is_active=label_data["is_active"],
                created_by=label_data["created_by"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(label)
            created_product_count += 1
            print(f"✅ 創建商品標籤: {label_data['name']}")
        
        # 創建回饋分類
        for category_data in feedback_categories_data:
            # 檢查是否已存在
            existing_category = db.query(FeedbackCategory).filter(FeedbackCategory.name == category_data["name"]).first()
            if existing_category:
                print(f"⚠️ 回饋分類 {category_data['name']} 已存在，跳過")
                continue
            
            # 創建新分類
            category = FeedbackCategory(
                name=category_data["name"],
                description=category_data["description"],
                is_active=category_data["is_active"],
                created_by=category_data["created_by"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(category)
            created_feedback_count += 1
            print(f"✅ 創建回饋分類: {category_data['name']}")
        
        # 提交更改
        db.commit()
        print(f"\n🎉 成功創建 {created_product_count} 個商品標籤和 {created_feedback_count} 個回饋分類！")
        
        # 顯示統計
        total_product_labels = db.query(ProductLabel).count()
        total_feedback_categories = db.query(FeedbackCategory).count()
        active_product_labels = db.query(ProductLabel).filter(ProductLabel.is_active == True).count()
        active_feedback_categories = db.query(FeedbackCategory).filter(FeedbackCategory.is_active == True).count()
        
        print(f"\n📊 標籤統計:")
        print(f"   商品標籤總數: {total_product_labels} (活躍: {active_product_labels})")
        print(f"   回饋分類總數: {total_feedback_categories} (活躍: {active_feedback_categories})")
        
    except Exception as e:
        print(f"❌ 創建測試標籤失敗: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 開始創建測試標籤數據...")
    create_test_labels()
    print("✨ 測試標籤數據創建完成！")