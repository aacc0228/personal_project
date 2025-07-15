import re
from datetime import datetime, timedelta
import pyodbc

def parse_apache_log_to_azure_sql(log_file='apache_2.log'):
    # --- 1. Azure SQL 資料庫連線設定 ---
    # !!! 請務必修改為您自己的伺服器、資料庫、帳號和密碼 !!!
    server = 'ga25206sql0713.database.windows.net'
    database = 'gae252060714db'
    username = 'SQLAdmin'  # <-- 請修改為您的 SQL 登入帳號
    password = '1qaz2wsx#edc'  # <-- 請修改為您的 SQL 登入密碼

    driver = '{ODBC Driver 17 for SQL Server}'

    connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    # --- 2. 日誌篩選邏輯 ---
    today = datetime(2025, 7, 14)
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
        print(f"錯誤：找不到日誌檔案 '{log_file}'。請確認您已透過左側檔案面板上傳。")
        return

    if not unique_errors:
        print("在前一天的日誌中沒有找到符合條件的錯誤訊息。")
        return

    # --- 3. 將資料寫入 Azure SQL 資料庫 ---
    connection = None
    try:
        connection = pyodbc.connect(connection_string, timeout=30)
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
            print(f"處理完成！成功將 {cursor.rowcount} 筆日誌寫入 Azure SQL 的 'log_data' 表中。")

    except pyodbc.Error as err:
        print(f"資料庫錯誤: {err}")
        print("請檢查：1. Azure防火牆規則是否已設定 (建議使用 0.0.0.0 測試) 2. 連線資訊(帳號/密碼)是否正確。")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()

# --- 執行程式 ---
if __name__ == "__main__":
    parse_apache_log_to_azure_sql()