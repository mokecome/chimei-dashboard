#!/usr/bin/env python3
"""
清空並重新初始化資料庫（保留用戶權限表）
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import get_db, engine
from app.models.user import User, UserRole
from app.models.file import VoiceFile, FileStatus, FileFormat
from app.models.analysis import VoiceAnalysis, SentimentType
from app.models.label import ProductLabel, FeedbackCategory

def clean_database():
    """清空非用戶相關的表格數據"""
    print("🧹 開始清理資料庫...")
    
    db = next(get_db())
    
    try:
        # 清空分析結果表
        db.execute(text("DELETE FROM voice_analysis"))
        print("✅ 清空 voice_analysis 表")
        
        # 清空檔案表
        db.execute(text("DELETE FROM voice_files"))
        print("✅ 清空 voice_files 表")
        
        # 清空標籤表
        db.execute(text("DELETE FROM product_labels"))
        db.execute(text("DELETE FROM feedback_categories"))
        print("✅ 清空標籤表")
        
        # 重置自增ID（如果有的話）
        db.execute(text("ALTER TABLE voice_analysis AUTO_INCREMENT = 1"))
        # voice_files table uses string IDs, not auto-increment
        db.execute(text("ALTER TABLE product_labels AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE feedback_categories AUTO_INCREMENT = 1"))
        
        db.commit()
        print("✅ 資料庫清理完成")
        
    except Exception as e:
        print(f"❌ 清理資料庫時發生錯誤: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def initialize_labels():
    """初始化基本標籤數據"""
    print("📋 初始化標籤數據...")
    
    db = next(get_db())
    
    try:
        # 獲取admin用戶作為創建者
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin_user:
            print("❌ 未找到管理員用戶，跳過標籤初始化")
            return
        
        admin_id = admin_user.id
        # 產品標籤
        product_labels = [
            {"name": "水餃", "description": "各式冷凍水餃產品", "is_active": True, "created_by": admin_id},
            {"name": "湯圓", "description": "甜湯圓系列產品", "is_active": True, "created_by": admin_id},
            {"name": "包子", "description": "冷凍包子系列", "is_active": True, "created_by": admin_id},
            {"name": "春捲", "description": "冷凍春捲產品", "is_active": True, "created_by": admin_id},
            {"name": "燒餅", "description": "傳統燒餅系列", "is_active": True, "created_by": admin_id},
            {"name": "餃子", "description": "手工餃子系列", "is_active": True, "created_by": admin_id},
            {"name": "湯品", "description": "即食湯品系列", "is_active": True, "created_by": admin_id},
            {"name": "點心", "description": "各式點心產品", "is_active": True, "created_by": admin_id}
        ]
        
        for label_data in product_labels:
            product_label = ProductLabel(**label_data)
            db.add(product_label)
        
        # 反饋類別
        feedback_categories = [
            {"name": "產品諮詢", "description": "產品相關詢問", "is_active": True, "created_by": admin_id},
            {"name": "品質問題", "description": "產品品質相關問題", "is_active": True, "created_by": admin_id},
            {"name": "配送問題", "description": "配送相關問題", "is_active": True, "created_by": admin_id},
            {"name": "價格諮詢", "description": "產品價格相關詢問", "is_active": True, "created_by": admin_id},
            {"name": "售後服務", "description": "售後服務相關", "is_active": True, "created_by": admin_id},
            {"name": "投訴建議", "description": "客戶投訴與建議", "is_active": True, "created_by": admin_id},
            {"name": "優惠活動", "description": "促銷活動相關", "is_active": True, "created_by": admin_id},
            {"name": "其他", "description": "其他類型反饋", "is_active": True, "created_by": admin_id}
        ]
        
        for category_data in feedback_categories:
            feedback_category = FeedbackCategory(**category_data)
            db.add(feedback_category)
        
        db.commit()
        print("✅ 標籤數據初始化完成")
        
        # 顯示初始化的數據
        product_count = db.query(ProductLabel).count()
        category_count = db.query(FeedbackCategory).count()
        print(f"📊 初始化了 {product_count} 個產品標籤和 {category_count} 個反饋類別")
        
    except Exception as e:
        print(f"❌ 初始化標籤數據時發生錯誤: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def clean_storage_files():
    """清理上傳檔案"""
    print("🗂️ 清理上傳檔案...")
    
    upload_dir = "./storage/uploads"
    temp_dir = "./storage/temp"
    
    import shutil
    import os
    
    try:
        # 清理上傳目錄
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"  刪除檔案: {filename}")
        
        # 清理臨時目錄
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        print("✅ 檔案清理完成")
        
    except Exception as e:
        print(f"❌ 清理檔案時發生錯誤: {e}")

def show_database_status():
    """顯示資料庫狀態"""
    print("\n📊 資料庫狀態檢查:")
    
    db = next(get_db())
    
    try:
        # 用戶數量
        user_count = db.query(User).count()
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        
        # 檔案和分析數量
        file_count = db.query(VoiceFile).count()
        analysis_count = db.query(VoiceAnalysis).count()
        
        # 標籤數量
        product_label_count = db.query(ProductLabel).count()
        category_count = db.query(FeedbackCategory).count()
        
        print(f"  👤 用戶總數: {user_count} (管理員: {admin_count})")
        print(f"  📁 檔案數量: {file_count}")
        print(f"  📊 分析記錄: {analysis_count}")
        print(f"  🏷️ 產品標籤: {product_label_count}")
        print(f"  📂 反饋類別: {category_count}")
        
    except Exception as e:
        print(f"❌ 檢查資料庫狀態時發生錯誤: {e}")
    finally:
        db.close()

def main():
    """主程序"""
    print("🚀 開始清空並重新初始化資料庫")
    print("⚠️  注意：此操作將清空所有檔案和分析數據（保留用戶數據）")
    
    # 自動確認執行
    print("\n⚡ 自動執行清理和初始化操作...")
    
    try:
        # 1. 清理資料庫
        clean_database()
        
        # 2. 清理檔案
        clean_storage_files()
        
        # 3. 初始化標籤
        initialize_labels()
        
        # 4. 顯示狀態
        show_database_status()
        
        print("\n🎉 資料庫清理和初始化完成！")
        print("💡 提示：")
        print("  - 用戶帳號和權限已保留")
        print("  - 所有檔案和分析記錄已清空")
        print("  - 基本標籤數據已重新初始化")
        print("  - 可以開始重新上傳和測試")
        
    except Exception as e:
        print(f"\n💥 操作失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()