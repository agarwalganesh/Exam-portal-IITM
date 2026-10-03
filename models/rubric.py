from . import db

class Rubric(db.Model):
    """
    Rubric Model:
    Represents an individual evaluation criterion used to grade candidate performance
    (e.g., 'Code Optimization', 'Viva Verbal Articulation', 'Schema Normalization').
    """
    __tablename__ = 'rubrics'

    # Primary key rubric criterion identifier
    rubric_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key link to parent examination
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.exam_id', ondelete='CASCADE'), nullable=False)
    
    # Name or title of the grading criterion
    criterion_name = db.Column(db.String(200), nullable=False)
    
    # Maximum marks allowed for this specific criterion (marks awarded must be <= maximum_marks)
    maximum_marks = db.Column(db.Float, nullable=False)
    
    # Weightage percentage or multiplier for aggregate computation
    weightage = db.Column(db.Float, nullable=False, default=100.0)
    
    # Qualitative guidance / rubric descriptors for faculty examiners
    description = db.Column(db.Text, nullable=True)

    # Relational associations
    # Parent examination
    examination = db.relationship('Examination', back_populates='rubrics')
    
    # Individual candidate evaluations recorded under this rubric criterion
    evaluations = db.relationship('Evaluation', back_populates='rubric', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Rubric {self.criterion_name} (Max: {self.maximum_marks})>'
