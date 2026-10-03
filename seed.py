import os
from datetime import datetime, timedelta, date, time
from app import create_app
from models import db, User, ExaminerProfile, Course, Examination, Rubric, ExaminationSlot, Booking, Evaluation

def seed_database():
    app = create_app()
    with app.app_context():
        print("[EMP Seed] Clearing existing data...")
        db.drop_all()
        db.create_all()

        now = datetime.now()

        # 1. Admin Account
        admin = User(
            name="System Administrator",
            email="admin@emp.iitm.ac.in",
            role="admin",
            status="active"
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        # 2. Examiners
        # Approved Examiner 1
        examiner1 = User(
            name="Dr. Priya Sharma",
            email="priya.sharma@emp.iitm.ac.in",
            role="examiner",
            status="active"
        )
        examiner1.set_password("Examiner@123")
        db.session.add(examiner1)
        db.session.flush()

        ep1 = ExaminerProfile(
            examiner_id=examiner1.id,
            name="Dr. Priya Sharma",
            contact_details="+91 98765 43210",
            department="Computer Science & Engineering",
            status="approved"
        )
        db.session.add(ep1)

        # Approved Examiner 2
        examiner2 = User(
            name="Prof. Rajesh Kumar",
            email="rajesh.kumar@emp.iitm.ac.in",
            role="examiner",
            status="active"
        )
        examiner2.set_password("Examiner@123")
        db.session.add(examiner2)
        db.session.flush()

        ep2 = ExaminerProfile(
            examiner_id=examiner2.id,
            name="Prof. Rajesh Kumar",
            contact_details="+91 98111 22334",
            department="Software Engineering",
            status="approved"
        )
        db.session.add(ep2)

        # Pending Examiner (to demonstrate Admin approval workflow)
        examiner3 = User(
            name="Dr. Ananya Sen",
            email="ananya.sen@emp.iitm.ac.in",
            role="examiner",
            status="pending"
        )
        examiner3.set_password("Examiner@123")
        db.session.add(examiner3)
        db.session.flush()

        ep3 = ExaminerProfile(
            examiner_id=examiner3.id,
            name="Dr. Ananya Sen",
            contact_details="+91 98450 78901",
            department="Data Science & AI",
            status="pending"
        )
        db.session.add(ep3)

        # 3. Students
        students_data = [
            ("Rahul Verma", "rahul.verma@student.iitm.ac.in"),
            ("Sneha Patel", "sneha.patel@student.iitm.ac.in"),
            ("Amit Gupta", "amit.gupta@student.iitm.ac.in"),
            ("Pooja Nair", "pooja.nair@student.iitm.ac.in"),
        ]
        created_students = []
        for s_name, s_email in students_data:
            st = User(
                name=s_name,
                email=s_email,
                role="student",
                status="active"
            )
            st.set_password("Student@123")
            db.session.add(st)
            created_students.append(st)

        db.session.flush()

        # 4. Courses
        c1 = Course(
            course_code="CS101",
            course_name="Introduction to Programming & Problem Solving",
            description="Fundamental concepts of structured programming, control flow, functions, and algorithmic thinking.",
            status="active"
        )
        c2 = Course(
            course_code="CS202",
            course_name="Data Structures and Algorithms",
            description="Linear and non-linear data structures, searching, sorting, graph traversal, and complexity analysis.",
            status="active"
        )
        c3 = Course(
            course_code="CS303",
            course_name="Database Management Systems",
            description="Relational data modeling, SQL queries, transaction management, and indexing techniques.",
            status="active"
        )
        c4 = Course(
            course_code="CS404",
            course_name="Web Application Engineering",
            description="Full-stack web application development, MVC architecture, RESTful APIs, and secure deployment.",
            status="active"
        )
        db.session.add_all([c1, c2, c3, c4])
        db.session.flush()

        # 5. Examinations
        # Exam 1: CS101 - Booking Open right now!
        exam1 = Examination(
            course_id=c1.course_id,
            examination_name="CS101 Viva Voce Assessment",
            examination_type="Viva",
            duration=30,
            maximum_marks=100.0,
            slot_creation_start=now - timedelta(days=5),
            slot_creation_end=now + timedelta(days=2),
            slot_booking_start=now - timedelta(days=2),
            slot_booking_end=now + timedelta(days=5),
            status="Booking Open"
        )

        # Exam 2: CS202 - Slot Creation Open right now!
        exam2 = Examination(
            course_id=c2.course_id,
            examination_name="CS202 Practical Lab Demonstration",
            examination_type="Practical",
            duration=45,
            maximum_marks=100.0,
            slot_creation_start=now - timedelta(days=1),
            slot_creation_end=now + timedelta(days=4),
            slot_booking_start=now + timedelta(days=5),
            slot_booking_end=now + timedelta(days=10),
            status="Slot Creation"
        )

        # Exam 3: CS303 - Completed with results and evaluations!
        exam3 = Examination(
            course_id=c3.course_id,
            examination_name="CS303 Final Project Demo & Evaluation",
            examination_type="Project Demo",
            duration=40,
            maximum_marks=100.0,
            slot_creation_start=now - timedelta(days=20),
            slot_creation_end=now - timedelta(days=15),
            slot_booking_start=now - timedelta(days=14),
            slot_booking_end=now - timedelta(days=7),
            status="Completed"
        )

        # Exam 4: CS404 - Draft status
        exam4 = Examination(
            course_id=c4.course_id,
            examination_name="CS404 Architecture & Design Assessment",
            examination_type="Assessment",
            duration=60,
            maximum_marks=100.0,
            slot_creation_start=now + timedelta(days=3),
            slot_creation_end=now + timedelta(days=8),
            slot_booking_start=now + timedelta(days=9),
            slot_booking_end=now + timedelta(days=15),
            status="Draft"
        )

        db.session.add_all([exam1, exam2, exam3, exam4])
        db.session.flush()

        # 6. Rubrics
        # Rubrics for Exam 1 (CS101)
        r1_1 = Rubric(
            examination_id=exam1.exam_id,
            criterion_name="Code Understanding & Syntax",
            maximum_marks=30.0,
            weightage=30.0,
            description="Ability to explain code snippets, variables, scope, and basic data types."
        )
        r1_2 = Rubric(
            examination_id=exam1.exam_id,
            criterion_name="Algorithmic Problem Solving",
            maximum_marks=40.0,
            weightage=40.0,
            description="Correctness of logic, edge case handling, and step-by-step problem breakdown."
        )
        r1_3 = Rubric(
            examination_id=exam1.exam_id,
            criterion_name="Viva Verbal Articulation",
            maximum_marks=30.0,
            weightage=30.0,
            description="Clarity of thought, technical terminology, and confidence during viva."
        )

        # Rubrics for Exam 3 (CS303)
        r3_1 = Rubric(
            examination_id=exam3.exam_id,
            criterion_name="ER Diagram & Schema Normalization",
            maximum_marks=35.0,
            weightage=35.0,
            description="Third Normal Form (3NF) adherence and correct relationship cardinalities."
        )
        r3_2 = Rubric(
            examination_id=exam3.exam_id,
            criterion_name="SQL Query Optimization & Indexing",
            maximum_marks=35.0,
            weightage=35.0,
            description="Complex join execution, index design, and query efficiency."
        )
        r3_3 = Rubric(
            examination_id=exam3.exam_id,
            criterion_name="Project Demo & Transaction Handling",
            maximum_marks=30.0,
            weightage=30.0,
            description="Live execution of database transactions, ACID properties, and demo Q&A."
        )

        db.session.add_all([r1_1, r1_2, r1_3, r3_1, r3_2, r3_3])
        db.session.flush()

        # 7. Examination Slots
        # Slots for Exam 1 (Booking Open)
        tomorrow = now.date() + timedelta(days=1)
        day_after = now.date() + timedelta(days=2)

        s1 = ExaminationSlot(
            examination_id=exam1.exam_id,
            examiner_id=examiner1.id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            maximum_student_capacity=2,
            available_seats=1,
            status="Available"
        )
        s2 = ExaminationSlot(
            examination_id=exam1.exam_id,
            examiner_id=examiner1.id,
            date=tomorrow,
            start_time=time(11, 0),
            end_time=time(11, 30),
            maximum_student_capacity=2,
            available_seats=2,
            status="Available"
        )
        s3 = ExaminationSlot(
            examination_id=exam1.exam_id,
            examiner_id=examiner2.id,
            date=day_after,
            start_time=time(14, 0),
            end_time=time(14, 30),
            maximum_student_capacity=1,
            available_seats=1,
            status="Available"
        )

        # Slots for Exam 3 (Completed)
        past_date = now.date() - timedelta(days=5)
        s_comp1 = ExaminationSlot(
            examination_id=exam3.exam_id,
            examiner_id=examiner1.id,
            date=past_date,
            start_time=time(9, 30),
            end_time=time(10, 10),
            maximum_student_capacity=2,
            available_seats=0,
            status="Completed"
        )

        db.session.add_all([s1, s2, s3, s_comp1])
        db.session.flush()

        # 8. Bookings
        # Booking in Exam 1 (Upcoming Booked) for Rahul Verma
        b1 = Booking(
            student_id=created_students[0].id,  # Rahul
            slot_id=s1.slot_id,
            booking_date=now - timedelta(hours=6),
            status="Booked"
        )
        # Booking in Exam 3 (Completed) for Rahul Verma
        b_comp1 = Booking(
            student_id=created_students[0].id,  # Rahul
            slot_id=s_comp1.slot_id,
            booking_date=now - timedelta(days=6),
            status="Completed"
        )
        # Booking in Exam 3 (Completed) for Sneha Patel
        b_comp2 = Booking(
            student_id=created_students[1].id,  # Sneha
            slot_id=s_comp1.slot_id,
            booking_date=now - timedelta(days=6),
            status="Completed"
        )

        db.session.add_all([b1, b_comp1, b_comp2])
        db.session.flush()

        # 9. Evaluations for Exam 3 completed bookings
        # Rahul's evaluations
        ev1_1 = Evaluation(
            booking_id=b_comp1.booking_id,
            rubric_id=r3_1.rubric_id,
            marks=32.0,
            remarks="Excellent normalization; tables are properly in 3NF with clear constraints.",
            evaluated_at=now - timedelta(days=5)
        )
        ev1_2 = Evaluation(
            booking_id=b_comp1.booking_id,
            rubric_id=r3_2.rubric_id,
            marks=31.5,
            remarks="Good understanding of B-Tree indexes and execution plans.",
            evaluated_at=now - timedelta(days=5)
        )
        ev1_3 = Evaluation(
            booking_id=b_comp1.booking_id,
            rubric_id=r3_3.rubric_id,
            marks=28.0,
            remarks="Live demo executed without errors. Answered all ACID transaction questions.",
            evaluated_at=now - timedelta(days=5)
        )

        # Sneha's evaluations
        ev2_1 = Evaluation(
            booking_id=b_comp2.booking_id,
            rubric_id=r3_1.rubric_id,
            marks=35.0,
            remarks="Flawless database design and comprehensive relational integrity checks.",
            evaluated_at=now - timedelta(days=5)
        )
        ev2_2 = Evaluation(
            booking_id=b_comp2.booking_id,
            rubric_id=r3_2.rubric_id,
            marks=34.0,
            remarks="Outstanding query optimization using compound indexes.",
            evaluated_at=now - timedelta(days=5)
        )
        ev2_3 = Evaluation(
            booking_id=b_comp2.booking_id,
            rubric_id=r3_3.rubric_id,
            marks=29.0,
            remarks="Exceptional project demo with concurrent transactions handled smoothly.",
            evaluated_at=now - timedelta(days=5)
        )

        db.session.add_all([ev1_1, ev1_2, ev1_3, ev2_1, ev2_2, ev2_3])

        # Recalculate seats
        s1.recalculate_seats()
        s2.recalculate_seats()
        s3.recalculate_seats()
        s_comp1.recalculate_seats()

        db.session.commit()
        print("[EMP Seed] Database populated successfully with demo records!")

if __name__ == '__main__':
    seed_database()
