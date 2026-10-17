import os
import shutil

# Base directory of the project (absolute path of this directory)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_database_uri():
    """
    Determines the appropriate database URI.
    Supports:
    1. External DATABASE_URL environment variable (PostgreSQL, MySQL, etc.)
    2. Vercel serverless /tmp writable SQLite database
    3. Local instance/database.db for development
    """
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # SQLAlchemy 1.4+ expects 'postgresql://' instead of legacy 'postgres://'
        if db_url.startswith('postgres://'):
            return db_url.replace('postgres://', 'postgresql://', 1)
        return db_url

    source_db = os.path.join(BASE_DIR, 'instance', 'database.db')

    # On Vercel / AWS Lambda, the repository directory is read-only.
    # The only writable directory is /tmp.
    is_serverless = os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
    if is_serverless or not os.access(BASE_DIR, os.W_OK):
        tmp_dir = '/tmp/instance'
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_db = os.path.join(tmp_dir, 'database.db')
        if not os.path.exists(tmp_db) and os.path.exists(source_db):
            shutil.copy2(source_db, tmp_db)
        return f"sqlite:///{tmp_db.replace(os.sep, '/')}"

    return f"sqlite:///{source_db.replace(os.sep, '/')}"

class Config:
    """
    Application Configuration Class:
    Stores database connections, secret session keys, and debug flags.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'emp-secret-key-iitm-project-secure-2026')
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
