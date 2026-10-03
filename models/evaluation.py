from datetime import datetime
from . import db

class Evaluation(db.Model):
    """
    Evaluation Model:
    Stores the granular grade and feedback awarded by an examiner
    for a specific student booking and rubric criterion.
    """
    __tablename__ = 'evaluations'

    # Primary key evaluation record identifier
    evaluation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key link to student booking session
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.booking_id', ondelete='CASCADE'), nullable=False)
    
    # Foreign key link to specific rubric criterion evaluated
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.rubric_id', ondelete='CASCADE'), nullable=False)
    
    # Numerical marks awarded by the faculty examiner (must be <= rubric.maximum_marks)
    marks = db.Column(db.Float, nullable=False, default=0.0)
    
    # Qualitative critique, observations, and recommendations for improvement
    remarks = db.Column(db.Text, nullable=True)
    
    # Timestamp when evaluation was submitted or updated
    evaluated_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relational associations
    # Parent booking reference
    booking = db.relationship('Booking', back_populates='evaluations')
    
    # Evaluated rubric criterion reference
    rubric = db.relationship('Rubric', back_populates='evaluations')

    def __repr__(self):
        return f'<Evaluation {self.evaluation_id} - Booking {self.booking_id} Rubric {self.rubric_id}: {self.marks}>'
