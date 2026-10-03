from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def role_required(*roles):
    """
    Role-Based Access Control (RBAC) Decorator:
    Guarantees that only authorized roles ('admin', 'examiner', 'student') can invoke protected routes.
    
    Security Checks Performed:
    1. Authentication Check: Redirects anonymous visitors to /login.
    2. Role Verification: Validates current_user.role is among authorized *roles.
    3. Examiner Approval Check: Redirects 'pending' examiners to /pending-approval page.
    4. Account Status Check: Logs out and blocks 'inactive' (deactivated) accounts.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Step 1: Ensure user is logged in
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            # Step 2: Ensure user belongs to the required role
            if current_user.role not in roles:
                flash('Unauthorized access: You do not have permission to access this resource.', 'danger')
                # Redirect user back to their respective role dashboard
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif current_user.role == 'examiner':
                    return redirect(url_for('examiner.dashboard'))
                elif current_user.role == 'student':
                    return redirect(url_for('student.dashboard'))
                return redirect(url_for('auth.login'))

            # Step 3: Prevent unapproved examiners from accessing the examiner portal
            if current_user.role == 'examiner' and current_user.status != 'active':
                flash('Your examiner registration is pending Admin approval. You cannot access the dashboard yet.', 'warning')
                return redirect(url_for('auth.pending_approval'))

            # Step 4: Prohibit deactivated users
            if current_user.status == 'inactive':
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return redirect(url_for('auth.logout'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
