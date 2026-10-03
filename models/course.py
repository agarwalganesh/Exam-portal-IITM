from . import db

class Course(db.Model):
    __tablename__ = 'courses'

    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'inactive'

    # Relationships
    examinations = db.relationship('Examination', back_populates='course', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.course_code}: {self.course_name}>'
