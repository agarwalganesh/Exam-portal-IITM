from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    """
    User Model:
    Represents authenticated users in the portal across all three roles:
    'admin', 'examiner', and 'student'.
    
    Inherits from UserMixin to integrate seamlessly with Flask-Login session management.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # User roles: 'admin', 'examiner', 'student'
    role = db.Column(db.String(20), nullable=False)
    
    # User statuses:
    # 'active'   - Normal operational status (all students, approved examiners, admin)
    # 'pending'  - Newly registered examiners awaiting Admin approval
    # 'inactive' - Deactivated accounts prohibited from logging in
    status = db.Column(db.String(20), nullable=False, default='active')
    
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relational Associations
    # 1. One-to-One with ExaminerProfile (for examiners)
    examiner_profile = db.relationship('ExaminerProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    # 2. One-to-Many with ExaminationSlot (slots created/assigned to an examiner)
    slots = db.relationship('ExaminationSlot', back_populates='examiner', foreign_keys='ExaminationSlot.examiner_id', cascade='all, delete-orphan')
    
    # 3. One-to-Many with Booking (exam bookings reserved by a student)
    bookings = db.relationship('Booking', back_populates='student', foreign_keys='Booking.student_id', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashes plaintext password using PBKDF2 with salt before saving to database."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Validates provided plaintext password against the stored cryptographic hash."""
        return check_password_hash(self.password_hash, password)

    # Convenient role verification properties
    @property
    def is_admin(self):
        """Returns True if current user is an Administrator."""
        return self.role == 'admin'

    @property
    def is_examiner(self):
        """Returns True if current user is an Examiner."""
        return self.role == 'examiner'

    @property
    def is_student(self):
        """Returns True if current user is a Student."""
        return self.role == 'student'

    @property
    def is_active_user(self):
        """Returns True if user status is active."""
        return self.status == 'active'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class ExaminerProfile(db.Model):
    """
    ExaminerProfile Model:
    Stores specialized faculty information (department, contact details, approval state)
    linked to an examiner user via foreign key.
    """
    __tablename__ = 'examiner_profiles'

    # Foreign key references users.id
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_details = db.Column(db.String(150), nullable=True)
    department = db.Column(db.String(150), nullable=True)
    
    # Approval state: 'pending', 'approved', 'rejected', 'inactive'
    status = db.Column(db.String(20), nullable=False, default='pending')

    # Bidirectional relationship back to User model
    user = db.relationship('User', back_populates='examiner_profile')

    def __repr__(self):
        return f'<ExaminerProfile {self.name} - {self.department}>'
