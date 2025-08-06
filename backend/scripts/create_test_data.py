"""
Create test data for voice files and analysis.
創建語音文件和分析的測試數據
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.models.file import VoiceFile, FileStatus, FileFormat
from app.models.analysis import VoiceAnalysis, SentimentType
from app.models.label import ProductLabel, FeedbackCategory
import uuid
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_voice_files_and_analysis():
    """創建測試語音文件和分析數據"""
    db = SessionLocal()
    
    try:
        # 獲取管理員用戶
        admin_user = db.query(User).filter(User.email == "admin@chimei.com").first()
        if not admin_user:
            logger.error("Admin user not found. Please run init_db.py first.")
            return
        
        # 獲取所有產品標籤和分類
        product_labels = db.query(ProductLabel).filter(ProductLabel.is_active == True).all()
        feedback_categories = db.query(FeedbackCategory).filter(FeedbackCategory.is_active == True).all()
        
        if not product_labels or not feedback_categories:
            logger.error("No product labels or feedback categories found. Please run init_db.py first.")
            return
        
        # 測試數據模板
        test_files_data = [
            {
                "original_filename": "客服電話_001_包子問題.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1024000,
                "duration": 45.6,
                "status": FileStatus.COMPLETED,
                "transcript": "你好，我想詢問關於包子的保存方式，我買了你們的包子但是不知道要怎麼保存比較好",
                "sentiment": SentimentType.NEUTRAL,
                "product_names": ["包子"],
                "feedback_category": "保存方式",
                "feedback_summary": "客戶詢問包子保存方式"
            },
            {
                "original_filename": "客服電話_001a_包子運送.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1124000,
                "duration": 52.3,
                "status": FileStatus.COMPLETED,
                "transcript": "我訂購的包子昨天送到了，但是冷凍效果非常好，包裝也很仔細，給你們一個讚！",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["包子"],
                "feedback_category": "物流配送",
                "feedback_summary": "客戶對包子運送和包裝滿意"
            },
            {
                "original_filename": "客服電話_001b_包子口味.wav",
                "file_format": FileFormat.WAV,
                "file_size": 980000,
                "duration": 41.2,
                "status": FileStatus.COMPLETED,
                "transcript": "你們的肉包太鹹了，可以減少一點鹽分嗎？家裡老人家吃不習慣",
                "sentiment": SentimentType.NEGATIVE,
                "product_names": ["包子"],
                "feedback_category": "口味研發",
                "feedback_summary": "客戶反映肉包太鹹"
            },
            {
                "original_filename": "客服電話_009_饅頭品質.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1350000,
                "duration": 48.9,
                "status": FileStatus.COMPLETED,
                "transcript": "饅頭的品質很穩定，每次買到的都很新鮮，口感也很好",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["饅頭"],
                "feedback_category": "口味研發",
                "feedback_summary": "客戶稱讚饅頭品質穩定"
            },
            {
                "original_filename": "客服電話_010_饅頭配送.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1280000,
                "duration": 44.7,
                "status": FileStatus.COMPLETED,
                "transcript": "饅頭送來的時候有點壓扁了，希望包裝可以再加強一點",
                "sentiment": SentimentType.NEGATIVE,
                "product_names": ["饅頭"],
                "feedback_category": "物流配送",
                "feedback_summary": "客戶反映饅頭運送時被壓扁"
            },
            {
                "original_filename": "客服電話_011_饅頭促銷.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1180000,
                "duration": 38.5,
                "status": FileStatus.COMPLETED,
                "transcript": "看到你們饅頭有買一送一的活動，請問這個活動到什麼時候？",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["饅頭"],
                "feedback_category": "活動價惠",
                "feedback_summary": "客戶詢問饅頭促銷活動"
            },
            {
                "original_filename": "客服電話_012_湯包品質.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1420000,
                "duration": 56.8,
                "status": FileStatus.COMPLETED,
                "transcript": "你們的小籠湯包真的很好吃，湯汁很多，皮也很薄，家人都很喜歡",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["湯包"],
                "feedback_category": "口味研發",
                "feedback_summary": "客戶稱讚湯包品質優良"
            },
            {
                "original_filename": "客服電話_013_湯包包裝.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1350000,
                "duration": 49.2,
                "status": FileStatus.COMPLETED,
                "transcript": "湯包的冷凍包裝很好，但是微波後容易破皮，有沒有建議的加熱方式？",
                "sentiment": SentimentType.NEUTRAL,
                "product_names": ["湯包"],
                "feedback_category": "調理方式",
                "feedback_summary": "客戶詢問湯包加熱方式避免破皮"
            },
            {
                "original_filename": "客服電話_014_燒餅訂購.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1680000,
                "duration": 63.4,
                "status": FileStatus.COMPLETED,
                "transcript": "請問燒餅可以大量訂購嗎？我們早餐店想要固定進貨",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["燒餅"],
                "feedback_category": "客服諮詢",
                "feedback_summary": "早餐店詢問燒餅大量訂購"
            },
            {
                "original_filename": "客服電話_015_餡餅新品.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1520000,
                "duration": 58.7,
                "status": FileStatus.COMPLETED,
                "transcript": "聽說你們要推出新口味的餡餅，很期待！希望可以有更多素食選擇",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["餡餅"],
                "feedback_category": "口味研發",
                "feedback_summary": "客戶期待新口味餡餅和素食選擇"
            },
            {
                "original_filename": "客服電話_002_水餃評價.mp3",
                "file_format": FileFormat.MP3,
                "file_size": 2048000,
                "duration": 78.2,
                "status": FileStatus.COMPLETED,
                "transcript": "我昨天買了你們的水餃，味道真的很好吃，但是包裝有點破損，希望可以改善包裝品質",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["水餃"],
                "feedback_category": "包裝問題",
                "feedback_summary": "客戶對水餃味道滿意但包裝有破損"
            },
            {
                "original_filename": "客服電話_003_湯圓口感.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1536000,
                "duration": 62.1,
                "status": FileStatus.COMPLETED,
                "transcript": "這次買的芝麻湯圓口感跟以前不太一樣，感覺比較硬，是製作流程有改變嗎？",
                "sentiment": SentimentType.NEGATIVE,
                "product_names": ["芝麻湯圓", "湯圓"],
                "feedback_category": "口味回饋",
                "feedback_summary": "客戶反映湯圓口感變硬"
            },
            {
                "original_filename": "客服電話_004_蒸餃調理.txt",
                "file_format": FileFormat.TXT,
                "file_size": 512,
                "duration": None,
                "status": FileStatus.COMPLETED,
                "transcript": "請問蒸餃要蒸多久？用電鍋還是瓦斯爐比較好？有沒有什麼調理小技巧？",
                "sentiment": SentimentType.NEUTRAL,
                "product_names": ["蒸餃"],
                "feedback_category": "調理方式",
                "feedback_summary": "客戶諮詢蒸餃調理方法"
            },
            {
                "original_filename": "客服電話_005_鍋貼購買.mp3",
                "file_format": FileFormat.MP3,
                "file_size": 1800000,
                "duration": 55.8,
                "status": FileStatus.PROCESSING,
                "transcript": "我想要大量購買鍋貼，請問有沒有批發價格？我們公司想要訂購做員工福利",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["鍋貼"],
                "feedback_category": "客服諮詢",
                "feedback_summary": "企業客戶詢問批發價格"
            },
            {
                "original_filename": "客服電話_006_餛飩營養.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1400000,
                "duration": 43.2,
                "status": FileStatus.COMPLETED,
                "transcript": "請問餛飩的營養成分表可以提供嗎？我家小孩有過敏體質，需要確認成分",
                "sentiment": SentimentType.NEUTRAL,
                "product_names": ["餛飩"],
                "feedback_category": "營養成分",
                "feedback_summary": "客戶詢問營養成分因小孩過敏"
            },
            {
                "original_filename": "客服電話_007_春捲退換貨.mp3",
                "file_format": FileFormat.MP3,
                "file_size": 2200000,
                "duration": 89.5,
                "status": FileStatus.COMPLETED,
                "transcript": "我買的春捲有異味，可能是壞了，我想要退換貨，請問流程是什麼？",
                "sentiment": SentimentType.NEGATIVE,
                "product_names": ["春捲"],
                "feedback_category": "退換貨",
                "feedback_summary": "客戶因產品異味要求退換貨"
            },
            {
                "original_filename": "客服電話_008_年糕促銷.wav",
                "file_format": FileFormat.WAV,
                "file_size": 1100000,
                "duration": 36.7,
                "status": FileStatus.COMPLETED,
                "transcript": "看到你們年糕在做促銷活動，請問這個優惠什麼時候結束？還有其他優惠嗎？",
                "sentiment": SentimentType.POSITIVE,
                "product_names": ["年糕"],
                "feedback_category": "促銷活動",
                "feedback_summary": "客戶詢問促銷活動詳情"
            }
        ]
        
        # 創建測試文件和分析數據
        for i, file_data in enumerate(test_files_data):
            # 創建語音文件記錄
            file_id = str(uuid.uuid4())
            
            # 創建假的文件路徑（實際部署時會有真實文件）
            fake_file_path = f"./storage/uploads/{file_id}.{file_data['file_format'].value}"
            
            voice_file = VoiceFile(
                id=file_id,
                filename=f"{file_id}.{file_data['file_format'].value}",
                original_filename=file_data['original_filename'],
                file_path=fake_file_path,
                file_size=file_data['file_size'],
                file_format=file_data['file_format'],
                duration=file_data['duration'],
                status=file_data['status'],
                uploaded_by=admin_user.id,
                created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                updated_at=datetime.now() - timedelta(hours=random.randint(1, 24))
            )
            
            db.add(voice_file)
            db.flush()  # 確保文件記錄有ID
            
            # 只為已完成的文件創建分析結果
            if file_data['status'] == FileStatus.COMPLETED:
                voice_analysis = VoiceAnalysis(
                    file_id=voice_file.id,
                    transcript=file_data['transcript'],
                    sentiment=file_data['sentiment'],
                    feedback_category=file_data['feedback_category'],
                    feedback_summary=file_data['feedback_summary'],
                    product_names=file_data['product_names'],
                    analysis_time=datetime.now() - timedelta(hours=random.randint(1, 12)),
                    created_at=datetime.now() - timedelta(hours=random.randint(1, 12))
                )
                
                db.add(voice_analysis)
            
            logger.info(f"Created test file: {file_data['original_filename']}")
        
        db.commit()
        logger.info(f"Successfully created {len(test_files_data)} test voice files and analysis records")
        
        # 顯示統計信息
        total_files = db.query(VoiceFile).count()
        total_analysis = db.query(VoiceAnalysis).count()
        logger.info(f"Total files in database: {total_files}")
        logger.info(f"Total analysis records in database: {total_analysis}")
        
    except Exception as e:
        logger.error(f"Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def clear_test_data():
    """清除測試數據"""
    db = SessionLocal()
    
    try:
        # 刪除所有分析記錄
        db.query(VoiceAnalysis).delete()
        
        # 刪除所有語音文件記錄
        db.query(VoiceFile).delete()
        
        db.commit()
        logger.info("All test data cleared successfully")
        
    except Exception as e:
        logger.error(f"Error clearing test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create test data for voice files and analysis")
    parser.add_argument("--clear", action="store_true", help="Clear all test data")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_test_data()
    else:
        create_test_voice_files_and_analysis()
    
    logger.info("Test data operation completed")