import os
from pathlib import Path
from dotenv import load_dotenv
import snowflake.connector

# Load environment variables from .env
load_dotenv()

# App Directory Configurations
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
VIDEO_DIR = STATIC_DIR / "videos"
CHUNK_DIR = STATIC_DIR / "temp_chunks"

# Ensure all directory structures exist instantly on application import
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
CHUNK_DIR.mkdir(parents=True, exist_ok=True)

def get_snowflake_connection():
    """
    Creates and returns a live, independent cursor and connection 
    to the target Snowflake instance using system environment variables.
    """
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
    )
    return conn