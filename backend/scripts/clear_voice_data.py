#!/usr/bin/env python3
"""
清空語音檔案和分析數據的腳本
"""
import os
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine
from app.models import VoiceFile, VoiceAnalysis
from sqlalchemy import text
import shutil

def clear_voice_data():
    """清空所有語音檔案和分析數據"""
    db = SessionLocal()
    
    try:
        # 1. 刪除所有分析結果
        analysis_count = db.query(VoiceAnalysis).count()
        db.query(VoiceAnalysis).delete()
        print(f"已刪除 {analysis_count} 個分析結果")
        
        # 2. 刪除所有語音檔案記錄
        file_count = db.query(VoiceFile).count()
        db.query(VoiceFile).delete()
        print(f"已刪除 {file_count} 個語音檔案記錄")
        
        # 3. 提交變更
        db.commit()
        
        # 4. 清空實際的檔案存儲目錄
        storage_path = Path(__file__).parent.parent / "storage" / "uploads"
        if storage_path.exists():
            # 刪除所有檔案但保留目錄結構
            for item in storage_path.iterdir():
                if item.is_file():
                    item.unlink()
                    print(f"已刪除檔案: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"已刪除目錄: {item.name}")
        
        print("\n✅ 成功清空所有語音檔案和分析數據！")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 清空數據時發生錯誤: {str(e)}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    response = input("確定要清空所有語音檔案和分析數據嗎？這個操作無法復原！(yes/no): ")
    if response.lower() == 'yes':
        clear_voice_data()
    else:
        print("已取消操作")