from datetime import datetime
from . import db

class Examination(db.Model):
    """
    Examination Model:
    Represents an institutional examination event linked to an academic course.
    
    Contains time windows for:
    1. Examiner Slot Creation (start & end)
    2. Student Slot Booking (start & end)
    """
    __tablename__ = 'examinations'

    # Primary key examination identifier
    exam_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key referencing the parent course
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    
    # Title of the examination
    examination_name = db.Column(db.String(200), nullable=False)
    
    # Examination type: 'Viva', 'Practical', 'Project Demo', 'Assessment'
    examination_type = db.Column(db.String(50), nullable=False)
    
    # Estimated duration per candidate in minutes (default 30 min)
    duration = db.Column(db.Integer, nullable=False, default=30)
    
    # Total maximum obtainable marks for this examination
    maximum_marks = db.Column(db.Float, nullable=False, default=100.0)
    
    # Timeline window during which examiners can create and edit time slots (Rule 1)
    slot_creation_start = db.Column(db.DateTime, nullable=False)
    slot_creation_end = db.Column(db.DateTime, nullable=False)
    
    # Timeline window during which students can book or cancel seats (Rule 2)
    slot_booking_start = db.Column(db.DateTime, nullable=False)
    slot_booking_end = db.Column(db.DateTime, nullable=False)
    
    # Status lifecycle: 'Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed'
    status = db.Column(db.String(30), nullable=False, default='Draft')

    # Relational associations
    # Parent course reference
    course = db.relationship('Course', back_populates='examinations')
    
    # Rubric criteria defined for multi-parameter evaluation
    rubrics = db.relationship('Rubric', back_populates='examination', cascade='all, delete-orphan')
    
    # Time slots scheduled under this examination
    slots = db.relationship('ExaminationSlot', back_populates='examination', cascade='all, delete-orphan')

    def is_slot_creation_period(self, check_time=None):
        """
        Business Rule 1: Checks if current timestamp falls within the authorized
        slot creation period for examiners.
        """
        if self.status in ['Draft', 'Completed', 'Closed']:
            return False
        t = check_time or datetime.now()
        return self.slot_creation_start <= t <= self.slot_creation_end

    def is_slot_booking_period(self, check_time=None):
        """
        Business Rule 2: Checks if current timestamp falls within the active
        student booking window.
        """
        if self.status in ['Draft', 'Completed', 'Closed']:
            return False
        t = check_time or datetime.now()
        return self.slot_booking_start <= t <= self.slot_booking_end

    def has_booking_started(self, check_time=None):
        """Checks if student booking has started, after which slots are locked from modification."""
        t = check_time or datetime.now()
        return t >= self.slot_booking_start

    def total_rubric_marks(self):
        """Calculates cumulative maximum marks across all defined rubric criteria."""
        return sum(r.maximum_marks for r in self.rubrics)

    def total_rubric_weightage(self):
        """Calculates cumulative weightage percentage across all defined rubrics."""
        return sum(r.weightage for r in self.rubrics)

    def __repr__(self):
        return f'<Examination {self.examination_name} ({self.examination_type})>'
