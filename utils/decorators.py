from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict access based on user role(s).
    Also checks if examiner or student account is active.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                flash('Unauthorized access: You do not have permission to access this resource.', 'danger')
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif current_user.role == 'examiner':
                    return redirect(url_for('examiner.dashboard'))
                elif current_user.role == 'student':
                    return redirect(url_for('student.dashboard'))
                return redirect(url_for('auth.login'))

            # Check status
            if current_user.role == 'examiner' and current_user.status != 'active':
                flash('Your examiner registration is pending Admin approval. You cannot access the dashboard yet.', 'warning')
                return redirect(url_for('auth.pending_approval'))

            if current_user.status == 'inactive':
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return redirect(url_for('auth.logout'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
