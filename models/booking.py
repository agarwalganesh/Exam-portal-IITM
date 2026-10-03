from datetime import datetime
from . import db

class Booking(db.Model):
    __tablename__ = 'bookings'

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('examination_slots.slot_id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='Booked')  # 'Booked', 'Cancelled', 'Completed'

    # Relationships
    student = db.relationship('User', back_populates='bookings', foreign_keys=[student_id])
    slot = db.relationship('ExaminationSlot', back_populates='bookings')
    evaluations = db.relationship('Evaluation', back_populates='booking', cascade='all, delete-orphan')

    @property
    def is_evaluated(self):
        return len(self.evaluations) > 0

    @property
    def total_marks_obtained(self):
        return sum(e.marks for e in self.evaluations)

    @property
    def maximum_possible_marks(self):
        if self.slot and self.slot.examination:
            return self.slot.examination.maximum_marks
        return 0.0

    @property
    def percentage(self):
        max_m = self.maximum_possible_marks
        if max_m and max_m > 0:
            return round((self.total_marks_obtained / max_m) * 100, 2)
        return 0.0

    def __repr__(self):
        return f'<Booking {self.booking_id} - Student: {self.student_id}, Slot: {self.slot_id} ({self.status})>'
