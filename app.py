import os
from datetime import datetime
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager, current_user
from config import Config
from models import db, User
from routes import auth_bp, admin_bp, examiner_bp, student_bp, api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(examiner_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(api_bp)

    # Root route redirect
    @app.route('/')
    def index():
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

    # Custom template filters and context
    @app.context_processor
    def inject_global_data():
        return {
            'current_year': datetime.now().year,
            'now': datetime.now()
        }

    @app.template_filter('datetime_format')
    def datetime_format(value, format='%b %d, %Y %I:%M %p'):
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
        if value is None:
            return ''
        return value.strftime(format)

    @app.template_filter('time_format')
    def time_format(value, format='%I:%M %p'):
        if value is None:
            return ''
        return value.strftime(format)

    # Automatic DB Initialization and Default Admin Creation
    with app.app_context():
        db.create_all()
        # Create default Admin if not exists
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

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
