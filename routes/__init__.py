from .auth import auth_bp
from .admin import admin_bp
from .examiner import examiner_bp
from .student import student_bp
from .api import api_bp

__all__ = ['auth_bp', 'admin_bp', 'examiner_bp', 'student_bp', 'api_bp']
