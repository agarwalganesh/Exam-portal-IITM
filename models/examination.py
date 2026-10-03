from datetime import datetime
from . import db

class Examination(db.Model):
    __tablename__ = 'examinations'

    exam_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    examination_name = db.Column(db.String(200), nullable=False)
    examination_type = db.Column(db.String(50), nullable=False)  # 'Viva', 'Practical', 'Project Demo', 'Assessment'
    duration = db.Column(db.Integer, nullable=False, default=30)  # minutes
    maximum_marks = db.Column(db.Float, nullable=False, default=100.0)
    slot_creation_start = db.Column(db.DateTime, nullable=False)
    slot_creation_end = db.Column(db.DateTime, nullable=False)
    slot_booking_start = db.Column(db.DateTime, nullable=False)
    slot_booking_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='Draft')  # 'Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed'

    # Relationships
    course = db.relationship('Course', back_populates='examinations')
    rubrics = db.relationship('Rubric', back_populates='examination', cascade='all, delete-orphan')
    slots = db.relationship('ExaminationSlot', back_populates='examination', cascade='all, delete-orphan')

    def is_slot_creation_period(self, check_time=None):
        if self.status in ['Draft', 'Completed', 'Closed']:
            return False
        t = check_time or datetime.now()
        return self.slot_creation_start <= t <= self.slot_creation_end

    def is_slot_booking_period(self, check_time=None):
        if self.status in ['Draft', 'Completed', 'Closed']:
            return False
        t = check_time or datetime.now()
        return self.slot_booking_start <= t <= self.slot_booking_end

    def has_booking_started(self, check_time=None):
        t = check_time or datetime.now()
        return t >= self.slot_booking_start

    def total_rubric_marks(self):
        return sum(r.maximum_marks for r in self.rubrics)

    def total_rubric_weightage(self):
        return sum(r.weightage for r in self.rubrics)

    def __repr__(self):
        return f'<Examination {self.examination_name} ({self.examination_type})>'
