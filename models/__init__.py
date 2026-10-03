from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User, ExaminerProfile
from .course import Course
from .examination import Examination
from .rubric import Rubric
from .slot import ExaminationSlot
from .booking import Booking
from .evaluation import Evaluation

__all__ = [
    'db',
    'User',
    'ExaminerProfile',
    'Course',
    'Examination',
    'Rubric',
    'ExaminationSlot',
    'Booking',
    'Evaluation',
]
