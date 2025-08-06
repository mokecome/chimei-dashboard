#!/usr/bin/env python3
"""
專案清理和維護腳本
"""
import os
import sys
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.file import VoiceFile, FileStatus
from app.models.analysis import VoiceAnalysis


def clean_python_cache(dry_run=False):
    """清理 Python 快取文件"""
    print("🧹 清理 Python 快取...")
    count = 0
    
    for root, dirs, files in os.walk('.'):
        # 刪除 __pycache__ 目錄
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            if not dry_run:
                shutil.rmtree(cache_path)
            print(f"  刪除: {cache_path}")
            count += 1
            
        # 刪除 .pyc 文件
        for file in files:
            if file.endswith(('.pyc', '.pyo', '.pyd')):
                file_path = os.path.join(root, file)
                if not dry_run:
                    os.remove(file_path)
                print(f"  刪除: {file_path}")
                count += 1
    
    print(f"✅ 清理了 {count} 個快取文件/目錄")


def clean_temp_files(dry_run=False):
    """清理臨時文件"""
    print("🧹 清理臨時文件...")
    count = 0
    patterns = ['*.tmp', '*.bak', '*.backup', '*.original', '*.log']
    
    for pattern in patterns:
        for file_path in Path('.').rglob(pattern):
            if not dry_run:
                file_path.unlink()
            print(f"  刪除: {file_path}")
            count += 1
    
    print(f"✅ 清理了 {count} 個臨時文件")


def clean_orphaned_files(dry_run=False):
    """清理孤立的上傳文件（數據庫中不存在的文件）"""
    print("🧹 檢查孤立文件...")
    db = SessionLocal()
    count = 0
    
    try:
        # 獲取所有數據庫中的文件路徑
        db_files = db.query(VoiceFile.file_path).all()
        db_file_paths = {os.path.basename(f[0]) for f in db_files}
        
        # 掃描上傳目錄
        upload_dir = Path('./storage/uploads')
        if upload_dir.exists():
            for file_path in upload_dir.iterdir():
                if file_path.is_file() and file_path.name != '.gitkeep':
                    # 檢查文件是否在數據庫中
                    file_name = f"./storage/uploads/{file_path.name}"
                    if file_path.name not in db_file_paths and file_name not in db_file_paths:
                        if not dry_run:
                            file_path.unlink()
                        print(f"  刪除孤立文件: {file_path}")
                        count += 1
        
        print(f"✅ 清理了 {count} 個孤立文件")
        
    finally:
        db.close()


def clean_old_files(days=30, dry_run=False):
    """清理舊文件（可選）"""
    print(f"🧹 清理 {days} 天前的文件...")
    db = SessionLocal()
    count = 0
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 查找舊文件
        old_files = db.query(VoiceFile).filter(
            VoiceFile.created_at < cutoff_date
        ).all()
        
        for file in old_files:
            # 刪除實體文件
            if os.path.exists(file.file_path):
                if not dry_run:
                    os.remove(file.file_path)
                print(f"  刪除文件: {file.file_path}")
            
            # 刪除數據庫記錄
            if not dry_run:
                # 先刪除相關的分析記錄
                db.query(VoiceAnalysis).filter_by(file_id=file.id).delete()
                # 再刪除文件記錄
                db.delete(file)
                
            count += 1
        
        if not dry_run:
            db.commit()
            
        print(f"✅ 清理了 {count} 個舊文件")
        
    finally:
        db.close()


def show_storage_stats():
    """顯示存儲統計信息"""
    print("\n📊 存儲統計:")
    
    # 計算上傳文件夾大小
    upload_dir = Path('./storage/uploads')
    if upload_dir.exists():
        total_size = sum(f.stat().st_size for f in upload_dir.rglob('*') if f.is_file())
        file_count = len(list(upload_dir.glob('*')))
        print(f"  上傳文件夾: {file_count} 個文件, {total_size / (1024**3):.2f} GB")
    
    # 數據庫統計
    db = SessionLocal()
    try:
        total_files = db.query(VoiceFile).count()
        completed_files = db.query(VoiceFile).filter_by(status=FileStatus.COMPLETED).count()
        failed_files = db.query(VoiceFile).filter_by(status=FileStatus.FAILED).count()
        
        print(f"  數據庫記錄: {total_files} 個文件")
        print(f"  - 已完成: {completed_files}")
        print(f"  - 失敗: {failed_files}")
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='專案清理和維護腳本')
    parser.add_argument('--dry-run', action='store_true', help='只顯示將要刪除的文件，不實際刪除')
    parser.add_argument('--cache', action='store_true', help='清理 Python 快取')
    parser.add_argument('--temp', action='store_true', help='清理臨時文件')
    parser.add_argument('--orphaned', action='store_true', help='清理孤立文件')
    parser.add_argument('--old', type=int, metavar='DAYS', help='清理指定天數前的文件')
    parser.add_argument('--all', action='store_true', help='執行所有清理操作（除了清理舊文件）')
    parser.add_argument('--stats', action='store_true', help='顯示存儲統計')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("⚠️  DRY RUN 模式 - 不會實際刪除文件\n")
    
    # 如果沒有指定任何操作，顯示幫助
    if not any([args.cache, args.temp, args.orphaned, args.old, args.all, args.stats]):
        parser.print_help()
        return
    
    # 執行清理操作
    if args.all or args.cache:
        clean_python_cache(args.dry_run)
        
    if args.all or args.temp:
        clean_temp_files(args.dry_run)
        
    if args.all or args.orphaned:
        clean_orphaned_files(args.dry_run)
        
    if args.old:
        clean_old_files(args.old, args.dry_run)
    
    # 顯示統計
    if args.stats or args.all:
        show_storage_stats()
    
    print("\n✨ 清理完成！")


if __name__ == "__main__":
    main()