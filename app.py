import os
from datetime import datetime
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User
from routes import auth_bp, admin_bp, examiner_bp, student_bp, api_bp

def create_app(config_class=Config):
    """
    Application Factory Function:
    Initializes Flask application instance, configures extensions,
    registers modular blueprints, sets up context filters, and
    performs automatic database table & default admin initialization.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure local instance folder exists for storing SQLite database if writable
    try:
        os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    except OSError:
        pass

    # 1. Initialize SQLAlchemy database with application context
    db.init_app(app)

    # 2. Initialize Flask-Login Authentication Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """User loader callback for Flask-Login to reconstruct user object from session ID."""
        return db.session.get(User, int(user_id))

    # 3. Register Modular Blueprints (Clean separation of concerns)
    app.register_blueprint(auth_bp)       # Authentication routes (login, register, logout)
    app.register_blueprint(admin_bp)      # Administrator operations (courses, exams, slots, search)
    app.register_blueprint(examiner_bp)   # Examiner operations (slots, roster, grading)
    app.register_blueprint(student_bp)    # Student operations (exam browse, booking, results)
    app.register_blueprint(api_bp)        # Read-only REST API endpoints

    # 4. Root Route Redirect
    @app.route('/')
    def index():
        """
        Root endpoint (/):
        Dynamically redirects authenticated users to their role-specific dashboard,
        or redirects unauthenticated guests to the login page.
        """
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'examiner':
                if current_user.status != 'active':
                    return redirect(url_for('auth.pending_approval'))
                return redirect(url_for('examiner.dashboard'))
            elif current_user.role == 'student':
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    # 5. Global Context Processors (Injected into all Jinja2 templates)
    @app.context_processor
    def inject_global_data():
        """Provides current year and current datetime across all templates."""
        return {
            'current_year': datetime.now().year,
            'now': datetime.now()
        }

    # 6. Jinja2 Custom Template Filters for Date & Time Formatting
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%b %d, %Y %I:%M %p'):
        """Formats datetime objects into human-readable strings (e.g., Oct 03, 2026 05:30 PM)."""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime(format)

    @app.template_filter('date_format')
    def date_format(value, format='%b %d, %Y'):
        """Formats date/datetime objects into readable date strings (e.g., Oct 03, 2026)."""
        if value is None:
            return ''
        return value.strftime(format)

    @app.template_filter('time_format')
    def time_format(value, format='%I:%M %p'):
        """Formats time objects into 12-hour AM/PM strings (e.g., 10:00 AM)."""
        if value is None:
            return ''
        return value.strftime(format)

    # 7. Automatic Database Initialization & Default Admin Account Creation
    with app.app_context():
        # Automatically create tables if they do not exist
        db.create_all()

        # Enforce Requirement 3: Admin must already exist; No admin registration
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            default_admin = User(
                name='System Administrator',
                email='admin@emp.iitm.ac.in',
                role='admin',
                status='active'
            )
            default_admin.set_password('Admin@123')
            db.session.add(default_admin)
            db.session.commit()
            print("[EMP Init] Default administrator account created: admin@emp.iitm.ac.in / Admin@123")

    return app

# Instantiate the application for WSGI / local execution
app = create_app()

if __name__ == '__main__':
    # Run development server locally on port 5000 with debug reloading
    app.run(host='127.0.0.1', port=5000, debug=True)
