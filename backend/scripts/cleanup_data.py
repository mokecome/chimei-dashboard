"""
Database cleanup script - removes all data except user accounts and permissions.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.models.file import VoiceFile
from app.models.analysis import VoiceAnalysis
from app.models.label import ProductLabel, FeedbackCategory
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_database():
    """Clean up database while preserving user accounts and permissions."""
    logger.info("Starting database cleanup...")
    
    db = SessionLocal()
    try:
        # 1. 刪除分析結果
        analysis_count = db.query(VoiceAnalysis).count()
        if analysis_count > 0:
            db.query(VoiceAnalysis).delete()
            logger.info(f"Deleted {analysis_count} analysis records")
        
        # 2. 刪除檔案記錄（注意：分析記錄會因為外鍵關係自動刪除）
        file_count = db.query(VoiceFile).count()
        if file_count > 0:
            db.query(VoiceFile).delete()
            logger.info(f"Deleted {file_count} file records")
        
        # 3. 保留用戶創建的標籤，但可以選擇性清理
        # 這裡我們保留所有標籤，如果您想清理，可以取消註釋下面的代碼
        
        # # 刪除產品標籤
        # product_count = db.query(ProductLabel).count()
        # if product_count > 0:
        #     db.query(ProductLabel).delete()
        #     logger.info(f"Deleted {product_count} product labels")
        
        # # 刪除回饋分類
        # category_count = db.query(FeedbackCategory).count()
        # if category_count > 0:
        #     db.query(FeedbackCategory).delete()
        #     logger.info(f"Deleted {category_count} feedback categories")
        
        db.commit()
        logger.info("Database cleanup completed successfully")
        
        # 顯示保留的用戶帳戶
        users = db.query(User).all()
        logger.info(f"Preserved {len(users)} user accounts:")
        for user in users:
            logger.info(f"  - {user.email} ({user.name}) - {user.role}")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def cleanup_uploaded_files():
    """Clean up uploaded files from storage directory."""
    storage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "uploads")
    
    if os.path.exists(storage_path):
        try:
            # 計算檔案數量
            file_count = len([f for f in os.listdir(storage_path) if os.path.isfile(os.path.join(storage_path, f))])
            
            # 清空目錄
            shutil.rmtree(storage_path)
            os.makedirs(storage_path, exist_ok=True)
            
            logger.info(f"Cleaned up {file_count} uploaded files from storage")
        except Exception as e:
            logger.error(f"Error cleaning up uploaded files: {e}")
    else:
        logger.info("Upload storage directory does not exist")


def reinitialize_default_data():
    """Reinitialize default product labels and feedback categories."""
    logger.info("Reinitializing default data...")
    
    db = SessionLocal()
    try:
        # 獲取管理員用戶
        admin_user = db.query(User).filter(User.email == "admin@chimei.com").first()
        if not admin_user:
            logger.error("Admin user not found! Cannot create default data.")
            return
        
        # 創建預設產品標籤
        default_products = [
            "水餃", "包子", "蒸餃", "鍋貼", "湯圓", "餛飩",
            "蔥油餅", "春捲", "蘿蔔糕", "年糕", "芝麻湯圓",
            "花生湯圓", "紅豆湯圓", "抹茶湯圓", "巧克力湯圓"
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
        
        # 創建預設回饋分類
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
        logger.info("Default labels and categories recreated")
        
    except Exception as e:
        logger.error(f"Error reinitializing default data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database cleanup script")
    parser.add_argument("--full", action="store_true", help="Also clean up uploaded files")
    parser.add_argument("--reinit", action="store_true", help="Reinitialize default labels and categories")
    
    args = parser.parse_args()
    
    # 執行資料庫清理
    cleanup_database()
    
    # 清理上傳的檔案（如果指定）
    if args.full:
        cleanup_uploaded_files()
    
    # 重新初始化預設資料（如果指定）
    if args.reinit:
        reinitialize_default_data()
    
    logger.info("Cleanup completed successfully!")
    logger.info("User accounts and permissions have been preserved.")