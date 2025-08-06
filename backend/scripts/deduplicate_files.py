#!/usr/bin/env python3
"""
資料庫去重腳本 - 根據檔案名稱去除重複檔案
Database deduplication script - Remove duplicate files based on filename
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models.file import VoiceFile
from app.models.analysis import VoiceAnalysis
from app.config import settings
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_duplicate_files(db_session):
    """
    查找重複的檔案（根據original_filename）
    Returns: List of dictionaries containing duplicate file info
    """
    query = text("""
        SELECT 
            original_filename,
            COUNT(*) as count,
            GROUP_CONCAT(id) as file_ids,
            GROUP_CONCAT(created_at) as created_dates
        FROM voice_files 
        GROUP BY original_filename 
        HAVING COUNT(*) > 1
        ORDER BY original_filename
    """)
    
    result = db_session.execute(query).fetchall()
    
    duplicates = []
    for row in result:
        file_ids = row.file_ids.split(',')
        created_dates = row.created_dates.split(',')
        
        # 組合檔案資訊
        files_info = []
        for i, file_id in enumerate(file_ids):
            files_info.append({
                'id': file_id,
                'created_at': created_dates[i]
            })
        
        duplicates.append({
            'filename': row.original_filename,
            'count': row.count,
            'files': files_info
        })
    
    return duplicates


def get_files_to_keep_and_delete(duplicates):
    """
    決定要保留和刪除的檔案
    策略：保留最早上傳的檔案
    """
    files_to_delete = []
    files_to_keep = []
    
    for dup_group in duplicates:
        # 按創建時間排序，保留最早的
        sorted_files = sorted(dup_group['files'], key=lambda x: x['created_at'])
        
        keep_file = sorted_files[0]  # 保留最早的
        delete_files = sorted_files[1:]  # 刪除其餘的
        
        files_to_keep.append({
            'filename': dup_group['filename'],
            'file_id': keep_file['id'],
            'created_at': keep_file['created_at']
        })
        
        for file_to_del in delete_files:
            files_to_delete.append({
                'filename': dup_group['filename'],
                'file_id': file_to_del['id'],
                'created_at': file_to_del['created_at']
            })
    
    return files_to_keep, files_to_delete


def delete_duplicate_files(db_session, files_to_delete, dry_run=True):
    """
    刪除重複檔案及其相關分析資料
    """
    deleted_count = 0
    
    for file_info in files_to_delete:
        try:
            file_id = file_info['file_id']
            filename = file_info['filename']
            
            if dry_run:
                logger.info(f"[DRY RUN] 會刪除檔案: {filename} (ID: {file_id})")
            else:
                # 查找檔案記錄
                file_obj = db_session.query(VoiceFile).filter(VoiceFile.id == file_id).first()
                if not file_obj:
                    logger.warning(f"檔案記錄不存在: {file_id}")
                    continue
                
                # 刪除實體檔案
                if os.path.exists(file_obj.file_path):
                    try:
                        os.remove(file_obj.file_path)
                        logger.info(f"已刪除實體檔案: {file_obj.file_path}")
                    except Exception as e:
                        logger.warning(f"刪除實體檔案失敗: {file_obj.file_path}, 錯誤: {e}")
                
                # 刪除相關分析記錄（由於設定了cascade，會自動刪除）
                analysis = db_session.query(VoiceAnalysis).filter(VoiceAnalysis.file_id == file_id).first()
                if analysis:
                    db_session.delete(analysis)
                    logger.info(f"刪除分析記錄: {file_id}")
                
                # 刪除檔案記錄
                db_session.delete(file_obj)
                logger.info(f"刪除檔案記錄: {filename} (ID: {file_id})")
                
                deleted_count += 1
                
        except Exception as e:
            logger.error(f"刪除檔案時出錯: {file_info}, 錯誤: {e}")
            continue
    
    if not dry_run:
        try:
            db_session.commit()
            logger.info(f"成功刪除 {deleted_count} 個重複檔案")
        except Exception as e:
            db_session.rollback()
            logger.error(f"提交更改時出錯: {e}")
            raise
    else:
        logger.info(f"[DRY RUN] 總共會刪除 {len(files_to_delete)} 個重複檔案")
    
    return deleted_count


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description='資料庫去重腳本')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='只顯示會刪除的檔案，不實際執行刪除 (預設: True)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='實際執行刪除操作')
    parser.add_argument('--force', action='store_true', default=False,
                       help='跳過確認，直接執行刪除 (危險！)')
    
    args = parser.parse_args()
    
    # 如果指定了 --execute，則關閉 dry_run
    if args.execute:
        dry_run = False
    else:
        dry_run = args.dry_run
    
    if dry_run:
        logger.info("=== 執行模式: DRY RUN (預覽模式) ===")
        logger.info("使用 --execute 參數來實際執行刪除操作")
    else:
        logger.info("=== 執行模式: 實際刪除 ===")
        if not args.force:
            try:
                response = input("確定要執行實際刪除操作嗎？這將永久刪除重複檔案 (y/N): ")
                if response.lower() != 'y':
                    logger.info("操作已取消")
                    return
            except EOFError:
                logger.info("無法獲取用戶輸入，操作已取消。使用 --force 參數跳過確認")
                return
        else:
            logger.info("使用 --force 參數，跳過確認步驟")
    
    # 建立資料庫連接
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    try:
        logger.info("開始查找重複檔案...")
        
        # 1. 查找重複檔案
        duplicates = find_duplicate_files(db_session)
        
        if not duplicates:
            logger.info("沒有發現重複檔案")
            return
        
        logger.info(f"發現 {len(duplicates)} 組重複檔案:")
        
        total_duplicates = 0
        for dup in duplicates:
            logger.info(f"  - {dup['filename']}: {dup['count']} 個重複")
            total_duplicates += dup['count'] - 1  # 減1因為要保留一個
        
        logger.info(f"總共需要刪除 {total_duplicates} 個重複檔案")
        
        # 2. 決定保留和刪除的檔案
        files_to_keep, files_to_delete = get_files_to_keep_and_delete(duplicates)
        
        logger.info(f"\n保留檔案策略: 保留最早上傳的檔案")
        logger.info(f"將保留 {len(files_to_keep)} 個檔案")
        logger.info(f"將刪除 {len(files_to_delete)} 個檔案")
        
        # 3. 顯示詳細資訊
        if len(files_to_delete) > 0:
            logger.info(f"\n要刪除的檔案:")
            for file_info in files_to_delete:
                logger.info(f"  - {file_info['filename']} (ID: {file_info['file_id']}, 上傳時間: {file_info['created_at']})")
        
        # 4. 執行刪除
        deleted_count = delete_duplicate_files(db_session, files_to_delete, dry_run=dry_run)
        
        if not dry_run:
            logger.info(f"\n去重完成！成功刪除 {deleted_count} 個重複檔案")
        else:
            logger.info(f"\n[DRY RUN] 預覽完成！使用 --execute 來實際執行刪除")
        
    except Exception as e:
        logger.error(f"執行過程中出錯: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    main()