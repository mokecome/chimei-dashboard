import pymysql
from tabulate import tabulate

# 資料庫連線設定
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "chime_dashboard",
    "port": 3306,
    "charset": "utf8mb4",
}

def list_database_tables():
    connection = None
    cursor = None
    
    try:
        # 建立連接
        print("連接到資料庫...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 獲取當前資料庫名稱
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()['DATABASE()']
        print(f"\n📁 當前資料庫: {db_name}")
        print("=" * 80)
        
        # 獲取所有資料表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ 資料庫中沒有任何資料表")
            return
        
        # 收集每個表的詳細資訊
        table_info = []
        
        for table in tables:
            table_name = list(table.values())[0]
            
            # 獲取記錄數
            cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
            record_count = cursor.fetchone()['count']
            
            # 獲取表結構資訊
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_info = cursor.fetchone()[f'Create Table']
            
            # 檢查是否有索引
            cursor.execute(f"SHOW INDEX FROM `{table_name}`")
            indexes = cursor.fetchall()
            index_count = len(indexes)
            
            # 獲取表的欄位數
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            columns = cursor.fetchall()
            column_count = len(columns)
            
            # 獲取表的大小（MB）
            cursor.execute(f"""
                SELECT 
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.TABLES 
                WHERE table_schema = '{db_name}' 
                AND table_name = '{table_name}'
            """)
            size_info = cursor.fetchone()
            size_mb = size_info['size_mb'] if size_info else 0
            
            table_info.append([
                table_name,
                record_count,
                column_count,
                index_count,
                f"{size_mb} MB"
            ])
        
        # 顯示表格摘要
        print("\n📊 資料表摘要:")
        headers = ["資料表名稱", "記錄數", "欄位數", "索引數", "大小"]
        print(tabulate(table_info, headers=headers, tablefmt="grid"))
        
        # 詳細顯示每個表的結構
        print("\n\n📋 資料表詳細結構:")
        print("=" * 80)
        
        for table in tables:
            table_name = list(table.values())[0]
            print(f"\n🔍 資料表: {table_name}")
            print("-" * 60)
            
            # 獲取並顯示欄位資訊
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            columns = cursor.fetchall()
            
            column_info = []
            for col in columns:
                column_info.append([
                    col['Field'],
                    col['Type'],
                    col['Null'],
                    col['Key'],
                    col['Default'] or 'NULL',
                    col['Extra']
                ])
            
            column_headers = ["欄位名稱", "類型", "允許NULL", "鍵", "預設值", "額外資訊"]
            print(tabulate(column_info, headers=column_headers, tablefmt="simple"))
            
            # 顯示外鍵約束
            cursor.execute(f"""
                SELECT 
                    CONSTRAINT_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = '{db_name}'
                AND TABLE_NAME = '{table_name}'
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print(f"\n  外鍵約束:")
                for fk in foreign_keys:
                    print(f"    - {fk['COLUMN_NAME']} → {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']} ({fk['CONSTRAINT_NAME']})")
        
        # 顯示資料庫統計
        print("\n\n📈 資料庫統計:")
        print("=" * 80)
        
        # 總記錄數
        total_records = sum(info[1] for info in table_info)
        total_size = sum(float(info[4].replace(' MB', '')) for info in table_info)
        
        print(f"  總資料表數: {len(table_info)}")
        print(f"  總記錄數: {total_records:,}")
        print(f"  總大小: {total_size:.2f} MB")
        
    except pymysql.Error as e:
        print(f"❌ 資料庫錯誤: {e}")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
    finally:
        # 關閉連接
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    list_database_tables()