import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load .env located in the parent directory of the project (../.env)
project_root = Path(__file__).resolve().parents[2]  # <project_root>/SKKULS_AIAGENT
load_dotenv(project_root / '.env')

def _env(key, default):
    return os.getenv(key, default)

DB_HOST = _env('POSTGRES_HOST', 'localhost')
DB_PORT = int(_env('POSTGRES_PORT', '5432'))
DB_NAME = _env('POSTGRES_DB', 'smarthrd')
DB_USER = _env('POSTGRES_USER', 'postgres')
DB_PASSWORD = _env('POSTGRES_PASSWORD', 'postgres')

def get_connection():
    """Return a new psycopg2 connection using parameters from .env."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor,
    )

from contextlib import contextmanager

@contextmanager
def db_cursor(commit: bool = True):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        cur.close()
        conn.close()
