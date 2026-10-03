import os

# Base directory of the project (absolute path of this directory)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Application Configuration Class:
    Stores database connections, secret session keys, and debug flags.
    """
    # Secret key used for signing session cookies and flash messages securely
    SECRET_KEY = os.environ.get('SECRET_KEY', 'emp-secret-key-iitm-project-secure-2026')

    # SQLite database location (stored in instance/database.db)
    # Database URL can also be overridden using environment variables
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'database.db')}"
    )

    # Disable modification tracking to save resources and improve performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode flag for local development
    DEBUG = True
