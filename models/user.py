from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'examiner', 'student'
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'pending', 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    examiner_profile = db.relationship('ExaminerProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    slots = db.relationship('ExaminationSlot', back_populates='examiner', foreign_keys='ExaminationSlot.examiner_id', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', back_populates='student', foreign_keys='Booking.student_id', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_examiner(self):
        return self.role == 'examiner'

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_active_user(self):
        return self.status == 'active'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class ExaminerProfile(db.Model):
    __tablename__ = 'examiner_profiles'

    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_details = db.Column(db.String(150), nullable=True)
    department = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected', 'inactive'

    # Relationships
    user = db.relationship('User', back_populates='examiner_profile')

    def __repr__(self):
        return f'<ExaminerProfile {self.name} - {self.department}>'
