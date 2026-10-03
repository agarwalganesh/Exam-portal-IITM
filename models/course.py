from . import db

class Course(db.Model):
    """
    Course Model:
    Represents an academic course offered by an academic department
    (e.g., CS101: Introduction to Programming).
    """
    __tablename__ = 'courses'

    # Primary key unique course identifier
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Departmental course code (e.g., CS101, CS202) - Must be unique
    course_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Official title of the course
    course_name = db.Column(db.String(200), nullable=False)
    
    # Detailed syllabus, prerequisites, and learning outcomes
    description = db.Column(db.Text, nullable=True)
    
    # Lifecycle status: 'active' (available for exams) or 'inactive' (archived)
    status = db.Column(db.String(20), nullable=False, default='active')

    # Relationships:
    # A course can contain multiple examination sessions (e.g., Viva, Practical, Project Demo)
    # Deleting a course cascades to delete all associated examinations
    examinations = db.relationship('Examination', back_populates='course', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.course_code}: {self.course_name}>'
