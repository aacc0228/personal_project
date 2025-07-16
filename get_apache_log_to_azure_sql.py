import re
from datetime import datetime, timedelta, date
import pyodbc
import time # 為了重試的延遲，需要 time 模組
import os   # 為了從環境變數讀取敏感資訊，需要 os 模組

def establish_db_connection(connection_string, retries=5, delay=15):
    """
    建立資料庫連線，並在遇到特定錯誤(40613)時自動重試。
    """
    last_exception = None
    for i in range(retries):
        try:
            print(f"資料庫連線嘗試: 第 {i + 1} 次...")
            # 嘗試建立連線，設定較短的連線逾時
            connection = pyodbc.connect(connection_string, timeout=30)
            print("✅ 資料庫連線成功！")
            return connection
        except pyodbc.Error as ex:
            last_exception = ex
            # 判斷是否為「資料庫無法使用/正在喚醒」的特定錯誤
            if '40613' in str(ex):
                print(f"資料庫正在喚醒 (錯誤 40613)，將在 {delay} 秒後重試...")
                time.sleep(delay)
            else:
                # 如果是其他類型的資料庫錯誤 (如帳號密碼錯誤)，直接拋出，不重試
                print(f"發生非預期的資料庫錯誤，將不會重試。")
                raise ex
    
    # 如果所有重試都失敗了，拋出最後一次的例外
    print("❌ 所有重試均失敗，無法連線至資料庫。")
    raise last_exception

def parse_apache_log_to_azure_sql(log_file='apache_2.log'):
    # --- 1. Azure SQL 資料庫連線設定 (優化後) ---
    # 最佳實踐：從環境變數讀取敏感資訊，不要寫死在程式碼中。
    # 在 GitHub Actions 中，請到 Settings > Secrets and variables > Actions 新增這些 Secrets。
    server = os.environ.get('AZURE_SQL_SERVER')
    database = os.environ.get('AZURE_SQL_DATABASE')
    username = os.environ.get('AZURE_SQL_USERNAME')
    password = os.environ.get('AZURE_SQL_PASSWORD') # 密碼強烈建議只從 Secret 讀取

    if not password:
        print("錯誤：找不到環境變數 'AZURE_SQL_PASSWORD'。請在 GitHub Secrets 中設定。")
        return

    driver = '{ODBC Driver 18 for SQL Server}'
    connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    # --- 2. 日誌篩選邏輯 (維持不變) ---
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime('[%a %b %d')

    unique_errors = {}
    error_code_pattern = re.compile(r"error code: (\d+)")
    full_date_pattern = re.compile(r"\[(.*?)\]")

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(yesterday_str) and '[:error]' in line:
                    match = error_code_pattern.search(line)
                    if match:
                        error_code = match.group(1)
                        if error_code not in unique_errors:
                            unique_errors[error_code] = line.strip()
    except FileNotFoundError:
        print(f"錯誤：找不到日誌檔案 '{log_file}'。")
        return

    if not unique_errors:
        print("在前一天的日誌中沒有找到符合條件的錯誤訊息。")
        return

    # --- 3. 將資料寫入 Azure SQL 資料庫 (套用重試邏輯) ---
    connection = None
    try:
        # 呼叫我們新的連線函式，它包含了重試邏輯
        connection = establish_db_connection(connection_string)
        
        cursor = connection.cursor()
        batch_create_time = datetime.now()
        insert_query = "INSERT INTO log_data (log_date, log_data, create_time) VALUES (?, ?, ?)"

        records_to_insert = []
        for log_line in unique_errors.values():
            date_match = full_date_pattern.match(log_line)
            if date_match:
                log_date_str = date_match.group(1)
                log_datetime_obj = datetime.strptime(log_date_str, '%a %b %d %H:%M:%S.%f %Y')
                records_to_insert.append((log_datetime_obj, log_line, batch_create_time))

        if records_to_insert:
            cursor.executemany(insert_query, records_to_insert)
            connection.commit()
            print(f"🎉 處理完成！成功將 {cursor.rowcount} 筆日誌寫入 Azure SQL 的 'log_data' 表中。")

    except pyodbc.Error as err:
        print(f"資料庫操作時發生錯誤: {err}")
    except Exception as e:
        print(f"發生未預期的錯誤: {e}")

    finally:
        # 確保連線和游標在使用後被關閉
        if connection:
            # 在較新的 pyodbc 版本中，關閉連線會自動處理游標
            connection.close()
            print("資料庫連線已關閉。")

# --- 執行程式 ---
if __name__ == "__main__":
    parse_apache_log_to_azure_sql()