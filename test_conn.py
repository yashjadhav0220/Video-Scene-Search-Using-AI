# test_conn.py
import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

print("🔍 Attempting a handshake with Snowflake...")
try:
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
    )
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION();")
    row = cursor.fetchone()
    print(f"✅ SUCCESS! Connected cleanly. Snowflake Version: {row[0]}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ CONNECTION FAILED:\n{str(e)}")