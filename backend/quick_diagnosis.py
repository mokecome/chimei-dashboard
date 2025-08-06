#!/usr/bin/env python3
"""快速診斷分析系統問題"""
import sys
sys.path.append('.')

import psutil
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from app.config import settings

def quick_diagnosis():
    """快速診斷系統問題"""
    print("=== 快速診斷分析系統 ===")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    issues = []
    warnings = []
    
    # 1. 系統資源檢查
    print("1. 系統資源檢查")
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/')
    
    print(f"   記憶體: {memory.percent:.1f}%", end="")
    if memory.percent > 85:
        print(" ❌ 過高")
        issues.append("記憶體使用率過高")
    elif memory.percent > 70:
        print(" ⚠️  較高")
        warnings.append("記憶體使用率較高")
    else:
        print(" ✅ 正常")
    
    print(f"   CPU: {cpu_percent:.1f}%", end="")
    if cpu_percent > 90:
        print(" ❌ 過高")
        issues.append("CPU 使用率過高")
    elif cpu_percent > 70:
        print(" ⚠️  較高")
        warnings.append("CPU 使用率較高")
    else:
        print(" ✅ 正常")
    
    disk_gb = disk.free / (1024**3)
    print(f"   磁碟: {disk_gb:.1f}GB 可用", end="")
    if disk_gb < 1:
        print(" ❌ 不足")
        issues.append("磁碟空間不足")
    elif disk_gb < 5:
        print(" ⚠️  偏低")
        warnings.append("磁碟空間偏低")
    else:
        print(" ✅ 充足")
    
    # 2. 服務狀態檢查
    print("\n2. 服務狀態檢查")
    
    # Ollama 服務
    try:
        response = requests.get('http://192.168.50.123:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            qwen_available = any(m['name'] == 'qwen3:8b' for m in models)
            if qwen_available:
                print("   Ollama + qwen3:8b: ✅ 正常")
            else:
                print("   Ollama + qwen3:8b: ❌ 模型不可用")
                issues.append("qwen3:8b 模型不可用")
        else:
            print(f"   Ollama: ❌ HTTP {response.status_code}")
            issues.append("Ollama 服務異常")
    except:
        print("   Ollama: ❌ 無法連接")
        issues.append("Ollama 服務無法連接")
    
    # 處理鎖檢查
    try:
        from app.services.analysis_service import AnalysisService
        if AnalysisService._processing:
            print(f"   處理鎖: ❌ 被占用 ({AnalysisService._processing_file_id})")
            issues.append("處理鎖被占用")
        else:
            print("   處理鎖: ✅ 正常")
    except:
        print("   處理鎖: ⚠️  無法檢查")
        warnings.append("無法檢查處理鎖狀態")
    
    # 3. 卡住檔案檢查
    print("\n3. 卡住檔案檢查")
    engine = create_engine(settings.DATABASE_URL)
    
    query = """
    SELECT 
        COUNT(*) as stuck_count,
        MAX(TIMESTAMPDIFF(MINUTE, updated_at, NOW())) as max_stuck_minutes
    FROM voice_files 
    WHERE status = 'analyzing'
    AND TIMESTAMPDIFF(MINUTE, updated_at, NOW()) > 30
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()
        stuck_count = result.stuck_count
        max_stuck = result.max_stuck_minutes or 0
    
    if stuck_count > 0:
        print(f"   卡住檔案: ❌ {stuck_count} 個 (最長 {max_stuck} 分鐘)")
        issues.append(f"{stuck_count} 個檔案卡在分析中")
    else:
        print("   卡住檔案: ✅ 無")
    
    # 4. 近期分析統計
    print("\n4. 近期分析統計")
    stats_query = """
    SELECT 
        status,
        COUNT(*) as count
    FROM voice_files
    WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY status
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(stats_query))
        recent_stats = {row.status: row.count for row in result}
    
    for status, count in recent_stats.items():
        print(f"   {status}: {count} 個")
    
    # 總結
    print("\n=== 診斷結果 ===")
    
    if issues:
        print("❌ 發現問題:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n建議執行:")
        print("   python fix_stuck_analysis.py  # 修復卡住檔案")
        print("   python auto_monitor_and_fix.py  # 自動修復")
    elif warnings:
        print("⚠️  發現警告:")
        for warning in warnings:
            print(f"   - {warning}")
        print("\n建議監控系統資源使用情況")
    else:
        print("✅ 系統運行正常")
    
    print(f"\n詳細監控日誌: /data1/ASR/backend/monitor.log")

if __name__ == "__main__":
    quick_diagnosis()