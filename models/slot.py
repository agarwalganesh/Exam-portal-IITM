from datetime import datetime, date, time
from . import db

class ExaminationSlot(db.Model):
    """
    ExaminationSlot Model:
    Represents a specific time block created by an examiner for student evaluation.
    
    Implements core capacity tracking:
    - maximum_student_capacity: Total allowed reservations
    - available_seats: Remaining seats available for booking
    - status: 'Available', 'Full', 'Cancelled', 'Completed'
    """
    __tablename__ = 'examination_slots'

    # Primary key slot identifier
    slot_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key link to parent examination
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.exam_id', ondelete='CASCADE'), nullable=False)
    
    # Foreign key link to evaluating faculty examiner (users.id)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Scheduled calendar date for the slot
    date = db.Column(db.Date, nullable=False)
    
    # Start time of evaluation session (e.g., 10:00 AM)
    start_time = db.Column(db.Time, nullable=False)
    
    # End time of evaluation session (e.g., 10:30 AM)
    end_time = db.Column(db.Time, nullable=False)
    
    # Maximum concurrent candidate capacity (Rule 3)
    maximum_student_capacity = db.Column(db.Integer, nullable=False, default=1)
    
    # Real-time counter of available seats remaining (decrements on booking, increments on cancellation)
    available_seats = db.Column(db.Integer, nullable=False, default=1)
    
    # Slot status lifecycle: 'Available', 'Full', 'Cancelled', 'Completed'
    status = db.Column(db.String(30), nullable=False, default='Available')

    # Relational associations
    # Parent examination
    examination = db.relationship('Examination', back_populates='slots')
    
    # Assigned faculty examiner user
    examiner = db.relationship('User', back_populates='slots', foreign_keys=[examiner_id])
    
    # Student bookings scheduled for this slot
    bookings = db.relationship('Booking', back_populates='slot', cascade='all, delete-orphan')

    @property
    def is_bookable(self):
        """Returns True if the slot has available status and has at least 1 open seat."""
        return self.status == 'Available' and self.available_seats > 0

    def recalculate_seats(self):
        """
        Business Rules 3, 4, 6 & 8:
        Synchronizes available_seats and status based on current active bookings.
        
        - Counts active bookings ('Booked' and 'Completed').
        - available_seats = max(0, capacity - active_bookings).
        - If available_seats <= 0: automatically sets status = 'Full'.
        - If seats open up upon cancellation: resets status = 'Available'.
        """
        active_bookings_count = sum(1 for b in self.bookings if b.status in ['Booked', 'Completed'])
        self.available_seats = max(0, self.maximum_student_capacity - active_bookings_count)
        if self.status not in ['Cancelled', 'Completed']:
            if self.available_seats <= 0:
                self.status = 'Full'
            else:
                self.status = 'Available'

    def __repr__(self):
        return f'<Slot {self.slot_id} - Exam: {self.examination_id} on {self.date} {self.start_time}-{self.end_time}>'
