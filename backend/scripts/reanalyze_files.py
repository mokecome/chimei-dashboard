#!/usr/bin/env python3
"""
重新分析失敗的檔案
"""
import os
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import VoiceFile
from app.models.file import FileStatus
from app.services.analysis_service import AnalysisService

def reanalyze_failed_files():
    """重新分析所有失敗的檔案"""
    db = SessionLocal()
    
    try:
        # 查找所有失敗的檔案
        failed_files = db.query(VoiceFile).filter(
            VoiceFile.status == FileStatus.FAILED
        ).all()
        
        if not failed_files:
            print("沒有失敗的檔案需要重新分析")
            return
        
        print(f"找到 {len(failed_files)} 個失敗的檔案")
        
        analysis_service = AnalysisService(db)
        
        for file in failed_files:
            print(f"\n處理檔案: {file.original_filename} (ID: {file.id})")
            
            # 重新分析
            result = analysis_service.process_file_analysis(file.id)
            
            if result.get("success"):
                print(f"✅ 分析成功")
            else:
                error = result.get("error", "未知錯誤")
                print(f"❌ 分析失敗: {error}")
        
        print("\n完成重新分析")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    reanalyze_failed_files()