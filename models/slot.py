from datetime import datetime, date, time
from . import db

class ExaminationSlot(db.Model):
    __tablename__ = 'examination_slots'

    slot_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.exam_id', ondelete='CASCADE'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    maximum_student_capacity = db.Column(db.Integer, nullable=False, default=1)
    available_seats = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(30), nullable=False, default='Available')  # 'Available', 'Full', 'Cancelled', 'Completed'

    # Relationships
    examination = db.relationship('Examination', back_populates='slots')
    examiner = db.relationship('User', back_populates='slots', foreign_keys=[examiner_id])
    bookings = db.relationship('Booking', back_populates='slot', cascade='all, delete-orphan')

    @property
    def is_bookable(self):
        return self.status == 'Available' and self.available_seats > 0

    def recalculate_seats(self):
        """Recalculate available seats based on active 'Booked' and 'Completed' bookings."""
        active_bookings_count = sum(1 for b in self.bookings if b.status in ['Booked', 'Completed'])
        self.available_seats = max(0, self.maximum_student_capacity - active_bookings_count)
        if self.status != 'Cancelled' and self.status != 'Completed':
            if self.available_seats <= 0:
                self.status = 'Full'
            else:
                self.status = 'Available'

    def __repr__(self):
        return f'<Slot {self.slot_id} - Exam: {self.examination_id} on {self.date} {self.start_time}-{self.end_time}>'
