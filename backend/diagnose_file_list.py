#!/usr/bin/env python3
"""
診斷檔案列表功能的腳本
"""
import os
import sys
import subprocess
from pathlib import Path

# 顏色輸出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(message, status="info"):
    colors = {
        "success": Colors.GREEN,
        "warning": Colors.YELLOW,
        "error": Colors.RED,
        "info": Colors.BLUE
    }
    color = colors.get(status, Colors.BLUE)
    print(f"{color}[{status.upper()}]{Colors.END} {message}")

def check_backend_service():
    """檢查後端服務狀態"""
    print_status("檢查後端服務狀態...", "info")
    
    try:
        # 檢查後端進程
        result = subprocess.run(['pgrep', '-f', 'run_server.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            print_status(f"後端服務正在運行 (PID: {pid})", "success")
            return True
        else:
            print_status("後端服務未運行", "warning")
            print_status("啟動命令: python run_server.py", "info")
            return False
    except Exception as e:
        print_status(f"檢查服務狀態失敗: {e}", "error")
        return False

def check_database_connection():
    """檢查資料庫連接"""
    print_status("檢查資料庫連接...", "info")
    
    try:
        # 使用 mysql 命令行工具檢查連接
        result = subprocess.run([
            'mysql', '-u', 'root', '-p123456', 
            '-e', 'SELECT COUNT(*) FROM voice_files;', 
            'chime_dashboard'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_status("資料庫連接正常", "success")
            
            # 解析檔案數量
            output_lines = result.stdout.strip().split('\n')
            if len(output_lines) >= 2:
                file_count = output_lines[1]  # 第二行是數據
                print_status(f"資料庫中共有 {file_count} 個檔案記錄", "info")
            
            # 檢查最近的檔案
            recent_result = subprocess.run([
                'mysql', '-u', 'root', '-p123456', 
                '-e', 'SELECT original_filename, status, created_at FROM voice_files ORDER BY created_at DESC LIMIT 5;', 
                'chime_dashboard'
            ], capture_output=True, text=True)
            
            if recent_result.returncode == 0:
                lines = recent_result.stdout.strip().split('\n')[1:]  # 跳過標題行
                if lines and lines[0]:  # 確保有數據
                    print_status("最近的檔案記錄:", "info")
                    for line in lines:
                        if line.strip():
                            print(f"  - {line}")
                else:
                    print_status("沒有找到任何檔案記錄", "warning")
            
            return True
        else:
            print_status(f"資料庫查詢失敗: {result.stderr}", "error")
            return False
            
    except FileNotFoundError:
        print_status("mysql 命令未找到，請確保 MySQL 客戶端已安裝", "warning")
        print_status("安裝命令: sudo apt-get install mysql-client", "info")
        return False
    except Exception as e:
        print_status(f"檢查資料庫時發生錯誤: {e}", "error")
        return False

def check_file_storage():
    """檢查檔案儲存目錄"""
    print_status("檢查檔案儲存目錄...", "info")
    
    storage_path = Path("storage/uploads")
    
    if storage_path.exists():
        print_status(f"儲存目錄存在: {storage_path.absolute()}", "success")
        
        # 檢查目錄權限
        if os.access(storage_path, os.R_OK | os.W_OK):
            print_status("目錄權限正常 (可讀寫)", "success")
        else:
            print_status("目錄權限異常", "error")
            return False
        
        # 統計檔案數量
        files = list(storage_path.glob("*"))
        print_status(f"儲存目錄中有 {len(files)} 個檔案", "info")
        
        if files:
            print_status("最近的檔案:", "info")
            for file_path in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                size = file_path.stat().st_size
                print(f"  - {file_path.name} ({size} bytes)")
        
        return True
    else:
        print_status(f"儲存目錄不存在: {storage_path.absolute()}", "error")
        print_status("建立目錄: mkdir -p storage/uploads", "info")
        return False

def check_api_schema():
    """檢查 API 回應格式"""
    print_status("檢查 API 回應格式...", "info")
    
    # 檢查 FileResponse schema
    schema_file = Path("app/schemas/file.py")
    if schema_file.exists():
        print_status("FileResponse schema 檔案存在", "success")
        
        # 讀取並檢查主要欄位
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_fields = [
            'id', 'filename', 'original_filename', 'file_format',
            'file_size', 'status', 'created_at', 'uploader_name'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        if missing_fields:
            print_status(f"缺少欄位: {', '.join(missing_fields)}", "warning")
        else:
            print_status("Schema 欄位完整", "success")
        
        return True
    else:
        print_status("FileResponse schema 檔案不存在", "error")
        return False

def check_repository_methods():
    """檢查 Repository 方法"""
    print_status("檢查 Repository 方法...", "info")
    
    repo_file = Path("app/repositories/file.py")
    if repo_file.exists():
        print_status("FileRepository 檔案存在", "success")
        
        with open(repo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            'get_multi_with_uploader',
            'count_with_filters'
        ]
        
        missing_methods = []
        for method in required_methods:
            if f"def {method}" not in content:
                missing_methods.append(method)
        
        if missing_methods:
            print_status(f"缺少方法: {', '.join(missing_methods)}", "error")
            return False
        else:
            print_status("Repository 方法完整", "success")
            return True
    else:
        print_status("FileRepository 檔案不存在", "error")
        return False

def check_dependencies():
    """檢查相依套件"""
    print_status("檢查相依套件...", "info")
    
    try:
        import fastapi
        import sqlalchemy
        print_status("主要套件導入正常", "success")
        
        # 檢查版本
        print_status(f"FastAPI 版本: {fastapi.__version__}", "info")
        print_status(f"SQLAlchemy 版本: {sqlalchemy.__version__}", "info")
        
        return True
    except ImportError as e:
        print_status(f"套件導入失敗: {e}", "error")
        return False

def provide_solutions():
    """提供解決方案"""
    print_status("\n=== 常見問題解決方案 ===", "info")
    
    solutions = [
        {
            "問題": "後端服務未運行",
            "解決方案": [
                "cd /data1/ASR/backend",
                "python run_server.py",
                "或使用: uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload"
            ]
        },
        {
            "問題": "資料庫連接失敗",
            "解決方案": [
                "檢查 MySQL 是否運行: systemctl status mysql",
                "檢查密碼: mysql -u root -p123456",
                "檢查資料庫: USE chime_dashboard; SHOW TABLES;"
            ]
        },
        {
            "問題": "儲存目錄不存在",
            "解決方案": [
                "mkdir -p storage/uploads",
                "chmod 755 storage/uploads"
            ]
        },
        {
            "問題": "權限問題",
            "解決方案": [
                "檢查用戶角色是否正確",
                "確保 Token 未過期",
                "驗證 JWT 設定"
            ]
        },
        {
            "問題": "前端呼叫失敗",
            "解決方案": [
                "檢查前端代理設定 (vite.config.ts)",
                "確保 API_BASE_URL 正確",
                "檢查 CORS 設定"
            ]
        }
    ]
    
    for solution in solutions:
        print_status(f"\n{solution['問題']}:", "warning")
        for step in solution['解決方案']:
            print(f"  - {step}")

def main():
    print_status("開始診斷檔案列表功能", "info")
    
    issues = []
    
    # 檢查各個組件
    if not check_backend_service():
        issues.append("後端服務")
    
    if not check_database_connection():
        issues.append("資料庫連接")
    
    if not check_file_storage():
        issues.append("檔案儲存")
    
    if not check_api_schema():
        issues.append("API Schema")
    
    if not check_repository_methods():
        issues.append("Repository 方法")
    
    if not check_dependencies():
        issues.append("相依套件")
    
    # 總結
    print_status("\n=== 診斷總結 ===", "info")
    
    if issues:
        print_status(f"發現 {len(issues)} 個問題:", "error")
        for issue in issues:
            print(f"  ✗ {issue}")
        
        provide_solutions()
    else:
        print_status("所有檢查都通過！", "success")
        print_status("如果檔案列表仍然失敗，請檢查:", "info")
        print_status("  1. 網路連接", "info")
        print_status("  2. 防火牆設定", "info")
        print_status("  3. 前端代理設定", "info")

if __name__ == "__main__":
    main()