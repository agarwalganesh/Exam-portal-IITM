from . import db

class Rubric(db.Model):
    __tablename__ = 'rubrics'

    rubric_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.exam_id', ondelete='CASCADE'), nullable=False)
    criterion_name = db.Column(db.String(200), nullable=False)
    maximum_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, nullable=False, default=100.0)  # e.g., weightage percentage or factor
    description = db.Column(db.Text, nullable=True)

    # Relationships
    examination = db.relationship('Examination', back_populates='rubrics')
    evaluations = db.relationship('Evaluation', back_populates='rubric', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Rubric {self.criterion_name} (Max: {self.maximum_marks})>'
