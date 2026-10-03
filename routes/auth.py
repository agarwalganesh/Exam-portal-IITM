from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, ExaminerProfile

auth_bp = Blueprint('auth', __name__)

# ==========================================
# USER LOGIN CONTROLLER
# ==========================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login Route:
    Handles credential verification for Admin, Faculty Examiners, and Students.
    
    Workflows:
    - If already authenticated: Redirects directly to respective dashboard.
    - POST: Validates email, password hash, and active/pending/inactive status.
    - If examiner is 'pending': Redirects to /pending-approval screen.
    - On success: Logs user into Flask-Login session and routes by role.
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

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Basic input validation
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html', email=email)

        # Look up user in SQLite database
        user = User.query.filter_by(email=email).first()

        # Validate existence and verify password hash
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        # Check if user account was deactivated by Admin
        if user.status == 'inactive':
            flash('Your account has been deactivated. Please contact the administrator.', 'danger')
            return render_template('auth/login.html', email=email)

        # Requirement 3: Unapproved examiner must not access Examiner dashboard
        if user.role == 'examiner' and user.status == 'pending':
            login_user(user)
            flash('Your account is pending administrator approval.', 'warning')
            return redirect(url_for('auth.pending_approval'))

        # Log user in
        login_user(user)
        flash(f'Welcome back, {user.name}!', 'success')

        # Role-based dashboard dispatch
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'examiner':
            return redirect(url_for('examiner.dashboard'))
        elif user.role == 'student':
            return redirect(url_for('student.dashboard'))
        else:
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


# ==========================================
# EXAMINER REGISTRATION CONTROLLER
# ==========================================
@auth_bp.route('/register/examiner', methods=['GET', 'POST'])
def register_examiner():
    """
    Examiner Registration Route:
    Enables faculty to register for an examiner account.
    
    Requirement 3:
    - Newly registered examiners are assigned status='pending'.
    - An ExaminerProfile record is automatically generated.
    - Examiner cannot access dashboard until approved by Admin.
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', '').strip()
        contact_details = request.form.get('contact_details', '').strip()

        # Server-side validation
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not department:
            errors.append('Department is required.')

        # Check for duplicate email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('An account with this email already exists.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register_examiner.html', name=name, email=email, department=department, contact_details=contact_details)

        # Create user with 'pending' status
        new_examiner = User(
            name=name,
            email=email,
            role='examiner',
            status='pending'  # Remained pending until Admin verification
        )
        new_examiner.set_password(password)
        db.session.add(new_examiner)
        db.session.flush()  # Flushes to obtain new_examiner.id for foreign key

        # Create associated ExaminerProfile
        profile = ExaminerProfile(
            examiner_id=new_examiner.id,
            name=name,
            contact_details=contact_details,
            department=department,
            status='pending'
        )
        db.session.add(profile)
        db.session.commit()

        flash('Registration submitted successfully! Your account is pending Admin approval. You may log in once approved.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_examiner.html')


# ==========================================
# STUDENT REGISTRATION CONTROLLER
# ==========================================
@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    """
    Student Registration Route:
    Allows student candidates to register and immediately log in.
    
    Requirement 3:
    - Student status is set to 'active' immediately upon registration.
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        # Duplicate email check
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('An account with this email already exists.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register_student.html', name=name, email=email)

        # Create active student account
        new_student = User(
            name=name,
            email=email,
            role='student',
            status='active'
        )
        new_student.set_password(password)
        db.session.add(new_student)
        db.session.commit()

        flash('Student registration successful! You can now log in to access the Student Portal.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_student.html')


# ==========================================
# PENDING APPROVAL NOTICE VIEW
# ==========================================
@auth_bp.route('/pending-approval')
def pending_approval():
    """Displays a helpful informational page when an unapproved examiner logs in."""
    return render_template('auth/pending_approval.html')


# ==========================================
# USER LOGOUT CONTROLLER
# ==========================================
@auth_bp.route('/logout')
@login_required
def logout():
    """Terminates active Flask-Login user session and redirects to login."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
