from datetime import datetime
from . import db

class Booking(db.Model):
    """
    Booking Model:
    Represents an examination reservation made by a student for a specific slot.
    
    Supports statuses:
    - 'Booked': Active reservation
    - 'Cancelled': Released reservation (history preserved per Rule 8)
    - 'Completed': Successfully evaluated session
    """
    __tablename__ = 'bookings'

    # Primary key booking identifier
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key referencing student user (users.id)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Foreign key referencing examination slot (examination_slots.slot_id)
    slot_id = db.Column(db.Integer, db.ForeignKey('examination_slots.slot_id', ondelete='CASCADE'), nullable=False)
    
    # Timestamp when reservation was created
    booking_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    # Booking status lifecycle: 'Booked', 'Cancelled', 'Completed'
    status = db.Column(db.String(30), nullable=False, default='Booked')

    # Relational associations
    # Candidate student user
    student = db.relationship('User', back_populates='bookings', foreign_keys=[student_id])
    
    # Reserved examination time slot
    slot = db.relationship('ExaminationSlot', back_populates='bookings')
    
    # Rubric evaluations recorded for this booking session
    evaluations = db.relationship('Evaluation', back_populates='booking', cascade='all, delete-orphan')

    @property
    def is_evaluated(self):
        """Returns True if at least one rubric evaluation has been submitted."""
        return len(self.evaluations) > 0

    @property
    def total_marks_obtained(self):
        """Calculates cumulative marks scored across all rubric criteria."""
        return sum(e.marks for e in self.evaluations)

    @property
    def maximum_possible_marks(self):
        """Retrieves total maximum marks achievable for the associated examination."""
        if self.slot and self.slot.examination:
            return self.slot.examination.maximum_marks
        return 0.0

    @property
    def percentage(self):
        """Computes student percentage score rounded to two decimal places."""
        max_m = self.maximum_possible_marks
        if max_m and max_m > 0:
            return round((self.total_marks_obtained / max_m) * 100, 2)
        return 0.0

    def __repr__(self):
        return f'<Booking {self.booking_id} - Student: {self.student_id}, Slot: {self.slot_id} ({self.status})>'
