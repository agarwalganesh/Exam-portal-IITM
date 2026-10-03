from datetime import datetime
from . import db

class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    evaluation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.booking_id', ondelete='CASCADE'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.rubric_id', ondelete='CASCADE'), nullable=False)
    marks = db.Column(db.Float, nullable=False, default=0.0)
    remarks = db.Column(db.Text, nullable=True)
    evaluated_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    booking = db.relationship('Booking', back_populates='evaluations')
    rubric = db.relationship('Rubric', back_populates='evaluations')

    def __repr__(self):
        return f'<Evaluation {self.evaluation_id} - Booking {self.booking_id} Rubric {self.rubric_id}: {self.marks}>'
