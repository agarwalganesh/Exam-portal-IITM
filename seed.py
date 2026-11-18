import os
from datetime import datetime, timedelta, date, time
from app import create_app
from models import db, User, ExaminerProfile, Course, Examination, Rubric, ExaminationSlot, Booking, Evaluation

def seed_database():
    """
    Seed Database Script for Comprehensive Viva Voce Demonstration:
    Populates SQLite database with every academic scenario, user role,
    lifecycle status, and business rule edge-case required for video demonstration.
    """
    app = create_app()
    with app.app_context():
        print("=" * 75)
        print(" [EMP Seed] Reinitializing Database for Viva Voce Demonstration...")
        print("=" * 75)
        db.drop_all()
        db.create_all()

        now = datetime.now()

        # ======================================================================
        # 1. SYSTEM ADMINISTRATOR ACCOUNT
        # ======================================================================
        admin = User(
            name="System Administrator",
            email="Admin@gmail.com",
            role="admin",
            status="active"
        )
        admin.set_password("Admin@1234")
        db.session.add(admin)

        # ======================================================================
        # 2. FACULTY EXAMINERS (Approved, Pending, and Inactive)
        # ======================================================================
        # Examiner 1: Approved - Has active slots & candidate ready for live evaluation
        examiner1 = User(
            name="Dr. Priya Sharma",
            email="priya.sharma@gmail.com",
            role="examiner",
            status="active"
        )
        examiner1.set_password("Examiner@123")
        db.session.add(examiner1)
        db.session.flush()

        ep1 = ExaminerProfile(
            examiner_id=examiner1.id,
            name="Dr. Priya Sharma",
            contact_details="+91 98765 43210 (Cabin 302, CSE Dept)",
            department="Computer Science & Engineering",
            status="approved"
        )
        db.session.add(ep1)

        # Examiner 2: Approved - Second faculty for multi-examiner isolation & slot reassignment
        examiner2 = User(
            name="Prof. Rajesh Kumar",
            email="rajesh.kumar@gmail.com",
            role="examiner",
            status="active"
        )
        examiner2.set_password("Examiner@123")
        db.session.add(examiner2)
        db.session.flush()

        ep2 = ExaminerProfile(
            examiner_id=examiner2.id,
            name="Prof. Rajesh Kumar",
            contact_details="+91 98111 22334 (Room 405, Software Block)",
            department="Software Engineering",
            status="approved"
        )
        db.session.add(ep2)

        # Examiner 3: Pending Approval - Demonstrates Admin Verification Workflow
        examiner3 = User(
            name="Dr. Ananya Sen",
            email="ananya.sen@gmail.com",
            role="examiner",
            status="pending"  # Blocks dashboard, redirects to /pending-approval
        )
        examiner3.set_password("Examiner@123")
        db.session.add(examiner3)
        db.session.flush()

        ep3 = ExaminerProfile(
            examiner_id=examiner3.id,
            name="Dr. Ananya Sen",
            contact_details="+91 98450 78901 (AI Research Lab)",
            department="Data Science & Artificial Intelligence",
            status="pending"
        )
        db.session.add(ep3)

        # Examiner 4: Deactivated / Inactive - Demonstrates Account Suspension
        examiner4 = User(
            name="Dr. Vikram Aditya",
            email="vikram.aditya@gmail.com",
            role="examiner",
            status="inactive"  # Blocks login with 'account deactivated' notice
        )
        examiner4.set_password("Examiner@123")
        db.session.add(examiner4)
        db.session.flush()

        ep4 = ExaminerProfile(
            examiner_id=examiner4.id,
            name="Dr. Vikram Aditya",
            contact_details="+91 97777 88888 (Dept of Electrical Eng)",
            department="Electrical Engineering",
            status="rejected"
        )
        db.session.add(ep4)

        # ======================================================================
        # 3. STUDENT CANDIDATES (Covering every testing condition)
        # ======================================================================
        students_config = [
            ("Rahul Verma", "rahul.verma@gmail.com"),        # Active in CS101, Completed in CS303
            ("Sneha Patel", "sneha.patel@gmail.com"),        # Completed in CS303 (Top Scorer)
            ("Amit Gupta", "amit.gupta@gmail.com"),          # Fresh student (0 bookings): ready to book on live video
            ("Pooja Nair", "pooja.nair@gmail.com"),          # Has a cancelled booking (Rule 8 audit history)
            ("Kavita Krishnan", "kavita.krishnan@gmail.com"),# Booked in CS101: waiting for live grading by examiner
            ("Arjun Singh", "arjun.singh@gmail.com")         # Booked in CS101 Full slot (Rule 4 demonstration)
        ]

        created_students = {}
        for s_name, s_email in students_config:
            st = User(
                name=s_name,
                email=s_email,
                role="student",
                status="active"
            )
            st.set_password("Student@123")
            db.session.add(st)
            created_students[s_email] = st

        db.session.flush()

        # ======================================================================
        # 4. ACADEMIC COURSES
        # ======================================================================
        c1 = Course(
            course_code="CS101",
            course_name="Introduction to Programming & Problem Solving",
            description="Core foundational programming concepts in C and Python: data structures, control flow, functions, and algorithmic complexity.",
            status="active"
        )
        c2 = Course(
            course_code="CS202",
            course_name="Data Structures and Algorithms",
            description="Advanced linear and non-linear data structures: balanced search trees, graph theory, dynamic programming, and amortized analysis.",
            status="active"
        )
        c3 = Course(
            course_code="CS303",
            course_name="Database Management Systems",
            description="Relational database theory, SQL DDL/DML, normalization forms (1NF-BCNF), ACID transaction management, and indexing strategies.",
            status="active"
        )
        c4 = Course(
            course_code="CS404",
            course_name="Web Application Engineering",
            description="Full-stack client-server architecture, MVC framework implementations, RESTful API design, session security, and database ORM.",
            status="active"
        )
        c5 = Course(
            course_code="CS505",
            course_name="Cloud Computing & Distributed Systems",
            description="Distributed consensus algorithms, microservices orchestration, and virtualization technologies (Archived Elective Course).",
            status="inactive"  # Demonstrates inactive course behavior
        )
        db.session.add_all([c1, c2, c3, c4, c5])
        db.session.flush()

        # ======================================================================
        # 5. EXAMINATIONS COVERING ALL 5 LIFECYCLE PHASES
        # ======================================================================
        # Exam 1: CS101 - BOOKING OPEN (Students can browse, reserve, and cancel slots)
        exam1 = Examination(
            course_id=c1.course_id,
            examination_name="CS101 Viva Voce Assessment",
            examination_type="Viva",
            duration=30,
            maximum_marks=100.0,
            slot_creation_start=now - timedelta(days=6),
            slot_creation_end=now - timedelta(hours=12),     # Examiner creation closed
            slot_booking_start=now - timedelta(days=2),      # Student booking active!
            slot_booking_end=now + timedelta(days=4),
            status="Booking Open"
        )

        # Exam 2: CS202 - SLOT CREATION WINDOW (Examiners can create/edit slots right now)
        exam2 = Examination(
            course_id=c2.course_id,
            examination_name="CS202 Practical Lab Demonstration",
            examination_type="Practical",
            duration=45,
            maximum_marks=100.0,
            slot_creation_start=now - timedelta(days=1),     # Examiner creation open!
            slot_creation_end=now + timedelta(days=3),
            slot_booking_start=now + timedelta(days=4),      # Student booking not yet open
            slot_booking_end=now + timedelta(days=10),
            status="Slot Creation"
        )

        # Exam 3: CS303 - COMPLETED (Evaluations published; students can view full scorecards)
        exam3 = Examination(
            course_id=c3.course_id,
            examination_name="CS303 Final Project Demo & Evaluation",
            examination_type="Project Demo",
            duration=40,
            maximum_marks=100.0,
            slot_creation_start=now - timedelta(days=25),
            slot_creation_end=now - timedelta(days=18),
            slot_booking_start=now - timedelta(days=17),
            slot_booking_end=now - timedelta(days=10),
            status="Completed"
        )

        # Exam 4: CS404 - DRAFT (Admin has created exam structure, not yet published)
        exam4 = Examination(
            course_id=c4.course_id,
            examination_name="CS404 Architecture & Design Assessment",
            examination_type="Assessment",
            duration=60,
            maximum_marks=100.0,
            slot_creation_start=now + timedelta(days=5),
            slot_creation_end=now + timedelta(days=10),
            slot_booking_start=now + timedelta(days=11),
            slot_booking_end=now + timedelta(days=18),
            status="Draft"
        )

        # Exam 5: CS101 Oral Exam - CLOSED (Booking window has expired)
        exam5 = Examination(
            course_id=c1.course_id,
            examination_name="CS101 Midterm Oral Screening",
            examination_type="Viva",
            duration=20,
            maximum_marks=50.0,
            slot_creation_start=now - timedelta(days=15),
            slot_creation_end=now - timedelta(days=10),
            slot_booking_start=now - timedelta(days=9),
            slot_booking_end=now - timedelta(days=1),        # Expired yesterday
            status="Closed"
        )

        db.session.add_all([exam1, exam2, exam3, exam4, exam5])
        db.session.flush()

        # ======================================================================
        # 6. RUBRIC CRITERIA (Multi-parameter weighted grading)
        # ======================================================================
        # Rubrics for Exam 1 (CS101 Viva Voce - Total 100 Marks)
        r1_1 = Rubric(
            examination_id=exam1.exam_id,
            criterion_name="Core Code Understanding & Syntax",
            maximum_marks=30.0,
            weightage=30.0,
            description="Examines candidate's grasp of data structures, variable scopes, pointers, and memory layout."
        )
        r1_2 = Rubric(
            examination_id=exam1.exam_id,
            criterion_name="Algorithmic Problem Solving & Edge Cases",
            maximum_marks=40.0,
            weightage=40.0,
            description="Logical formulation, optimal time-space complexity, and identification of boundary edge cases."
        )
        r1_3 = Rubric(
            examination_id=exam1.exam_id,
            criterion_name="Viva Verbal Articulation & Technical Rigor",
            maximum_marks=30.0,
            weightage=30.0,
            description="Clarity of spoken technical reasoning, confidence, and defense of design decisions."
        )

        # Rubrics for Exam 2 (CS202 Practical Lab - Total 100 Marks)
        r2_1 = Rubric(
            examination_id=exam2.exam_id,
            criterion_name="Data Structure Selection & Justification",
            maximum_marks=30.0,
            weightage=30.0,
            description="Appropriate choice of tree/graph structures for real-world scenarios."
        )
        r2_2 = Rubric(
            examination_id=exam2.exam_id,
            criterion_name="Live Implementation & Bug Fixing",
            maximum_marks=40.0,
            weightage=40.0,
            description="Hands-on coding, debugging runtime errors, and compiling clean executable code."
        )
        r2_3 = Rubric(
            examination_id=exam2.exam_id,
            criterion_name="Code Cleanliness & Documentation",
            maximum_marks=30.0,
            weightage=30.0,
            description="Adherence to clean code principles, modularity, and concise inline comments."
        )

        # Rubrics for Exam 3 (CS303 Project Demo - Total 100 Marks)
        r3_1 = Rubric(
            examination_id=exam3.exam_id,
            criterion_name="ER Diagram & Schema Normalization (3NF)",
            maximum_marks=35.0,
            weightage=35.0,
            description="Relational database integrity, 3NF schema design, and avoidance of insertion/deletion anomalies."
        )
        r3_2 = Rubric(
            examination_id=exam3.exam_id,
            criterion_name="SQL Query Optimization & Indexing",
            maximum_marks=35.0,
            weightage=35.0,
            description="Query plan analysis, proper use of clustered/non-clustered indexes, and performance metrics."
        )
        r3_3 = Rubric(
            examination_id=exam3.exam_id,
            criterion_name="Live Transaction Demo & ACID Concurrency",
            maximum_marks=30.0,
            weightage=30.0,
            description="Live demonstration of isolated database transactions, commit/rollback, and deadlock prevention."
        )

        db.session.add_all([r1_1, r1_2, r1_3, r2_1, r2_2, r2_3, r3_1, r3_2, r3_3])
        db.session.flush()

        # ======================================================================
        # 7. EXAMINATION SLOTS (Covering all business rules & capacity states)
        # ======================================================================
        tomorrow = now.date() + timedelta(days=1)
        day_after = now.date() + timedelta(days=2)
        three_days_later = now.date() + timedelta(days=3)

        # Slot 1 (CS101, Dr. Priya Sharma): Capacity=2, Booked by Rahul & Arjun -> STATUS: FULL (0 seats)
        # Demonstrates: Rule 3 (Capacity) and Rule 4 (Auto Full Status Transition)
        s1 = ExaminationSlot(
            examination_id=exam1.exam_id,
            examiner_id=examiner1.id,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            maximum_student_capacity=2,
            available_seats=0,
            status="Full"
        )

        # Slot 2 (CS101, Dr. Priya Sharma): Capacity=2, Booked by Kavita -> STATUS: AVAILABLE (1 seat open)
        # Demonstrates:
        # 1. Fresh student Amit Gupta can LIVE BOOK this 1 remaining seat on video!
        # 2. Dr. Priya Sharma can LIVE EVALUATE Kavita Krishnan on video!
        s2 = ExaminationSlot(
            examination_id=exam1.exam_id,
            examiner_id=examiner1.id,
            date=tomorrow,
            start_time=time(11, 0),
            end_time=time(11, 30),
            maximum_student_capacity=2,
            available_seats=1,
            status="Available"
        )

        # Slot 3 (CS101, Prof. Rajesh Kumar): Capacity=2, 0 Bookings -> STATUS: AVAILABLE (2 seats open)
        # Demonstrates: Rule 6 (Examiner Isolation) and Rule 7 (Admin Override / Reassign Slot)
        s3 = ExaminationSlot(
            examination_id=exam1.exam_id,
            examiner_id=examiner2.id,
            date=day_after,
            start_time=time(14, 0),
            end_time=time(14, 30),
            maximum_student_capacity=2,
            available_seats=2,
            status="Available"
        )

        # Slot 4 (CS101, Prof. Rajesh Kumar): Capacity=1, Pooja had booked and CANCELLED -> STATUS: AVAILABLE
        # Demonstrates: Rule 8 (Preservation of booking history upon cancellation & seat release)
        s4 = ExaminationSlot(
            examination_id=exam1.exam_id,
            examiner_id=examiner2.id,
            date=day_after,
            start_time=time(15, 0),
            end_time=time(15, 30),
            maximum_student_capacity=1,
            available_seats=1,
            status="Available"
        )

        # Slot 5 (CS202, Prof. Rajesh Kumar): In Slot Creation Phase
        # Demonstrates: Rule 1 (Examiner can create/edit/delete slots in creation window)
        s5 = ExaminationSlot(
            examination_id=exam2.exam_id,
            examiner_id=examiner2.id,
            date=three_days_later,
            start_time=time(9, 0),
            end_time=time(9, 45),
            maximum_student_capacity=3,
            available_seats=3,
            status="Available"
        )

        # Slot 6 (CS303, Dr. Priya Sharma): Past Completed Slot with full evaluations
        # Demonstrates: Historical view of completed viva evaluations
        past_date = now.date() - timedelta(days=6)
        s_comp = ExaminationSlot(
            examination_id=exam3.exam_id,
            examiner_id=examiner1.id,
            date=past_date,
            start_time=time(10, 0),
            end_time=time(10, 40),
            maximum_student_capacity=2,
            available_seats=0,
            status="Completed"
        )

        db.session.add_all([s1, s2, s3, s4, s5, s_comp])
        db.session.flush()

        # ======================================================================
        # 8. STUDENT BOOKINGS (Active, Cancelled, and Completed)
        # ======================================================================
        # Booking 1: Rahul Verma in Slot 1 (CS101) -> Booked
        # Demonstrates: Duplicate booking prevention (Rule 5) when Rahul tries to book slot 2 or 3
        b_rahul = Booking(
            student_id=created_students["rahul.verma@gmail.com"].id,
            slot_id=s1.slot_id,
            booking_date=now - timedelta(days=1),
            status="Booked"
        )

        # Booking 2: Arjun Singh in Slot 1 (CS101) -> Booked (Makes Slot 1 FULL)
        b_arjun = Booking(
            student_id=created_students["arjun.singh@gmail.com"].id,
            slot_id=s1.slot_id,
            booking_date=now - timedelta(hours=18),
            status="Booked"
        )

        # Booking 3: Kavita Krishnan in Slot 2 (CS101) -> Booked (WAITING FOR LIVE EVALUATION)
        # Demonstrates: Examiner Priya Sharma evaluating a student on live video
        b_kavita = Booking(
            student_id=created_students["kavita.krishnan@gmail.com"].id,
            slot_id=s2.slot_id,
            booking_date=now - timedelta(hours=8),
            status="Booked"
        )

        # Booking 4: Pooja Nair in Slot 4 (CS101) -> CANCELLED
        # Demonstrates: Rule 8 Audit Record (Booking retained as 'Cancelled', seat released)
        b_pooja_cancelled = Booking(
            student_id=created_students["pooja.nair@gmail.com"].id,
            slot_id=s4.slot_id,
            booking_date=now - timedelta(days=2),
            status="Cancelled"
        )

        # Booking 5: Rahul Verma in CS303 -> COMPLETED (Scored 91.5%)
        b_rahul_comp = Booking(
            student_id=created_students["rahul.verma@gmail.com"].id,
            slot_id=s_comp.slot_id,
            booking_date=now - timedelta(days=8),
            status="Completed"
        )

        # Booking 6: Sneha Patel in CS303 -> COMPLETED (Scored 98.0% Top Scorer)
        b_sneha_comp = Booking(
            student_id=created_students["sneha.patel@gmail.com"].id,
            slot_id=s_comp.slot_id,
            booking_date=now - timedelta(days=8),
            status="Completed"
        )

        db.session.add_all([b_rahul, b_arjun, b_kavita, b_pooja_cancelled, b_rahul_comp, b_sneha_comp])
        db.session.flush()

        # ======================================================================
        # 9. EVALUATIONS & SCORECARDS (Granular Rubric Breakdown)
        # ======================================================================
        # Evaluations for Rahul Verma (Total: 91.5 / 100 -> 91.5% Grade: A+)
        ev_r1 = Evaluation(
            booking_id=b_rahul_comp.booking_id,
            rubric_id=r3_1.rubric_id,
            marks=32.5,
            remarks="Excellent normalization; tables satisfy 3NF constraints without redundant functional dependencies.",
            evaluated_at=now - timedelta(days=6)
        )
        ev_r2 = Evaluation(
            booking_id=b_rahul_comp.booking_id,
            rubric_id=r3_2.rubric_id,
            marks=31.0,
            remarks="Accurate query execution plan analysis and proficient B-Tree indexing application.",
            evaluated_at=now - timedelta(days=6)
        )
        ev_r3 = Evaluation(
            booking_id=b_rahul_comp.booking_id,
            rubric_id=r3_3.rubric_id,
            marks=28.0,
            remarks="Demonstrated transaction ACID rollback effectively. Clear explanation of isolation levels.",
            evaluated_at=now - timedelta(days=6)
        )

        # Evaluations for Sneha Patel (Total: 98.0 / 100 -> 98.0% Grade: Outstanding)
        ev_s1 = Evaluation(
            booking_id=b_sneha_comp.booking_id,
            rubric_id=r3_1.rubric_id,
            marks=35.0,
            remarks="Flawless schema architecture, relational integrity triggers, and thorough normalization defense.",
            evaluated_at=now - timedelta(days=6)
        )
        ev_s2 = Evaluation(
            booking_id=b_sneha_comp.booking_id,
            rubric_id=r3_2.rubric_id,
            marks=34.0,
            remarks="Outstanding compound index design optimizing join performance on 100k+ rows.",
            evaluated_at=now - timedelta(days=6)
        )
        ev_s3 = Evaluation(
            booking_id=b_sneha_comp.booking_id,
            rubric_id=r3_3.rubric_id,
            marks=29.0,
            remarks="Exceptional real-time transaction demonstration with multi-user concurrency testing.",
            evaluated_at=now - timedelta(days=6)
        )

        db.session.add_all([ev_r1, ev_r2, ev_r3, ev_s1, ev_s2, ev_s3])

        # Synchronize seats and auto-full status for all slots
        for s in [s1, s2, s3, s4, s5, s_comp]:
            s.recalculate_seats()

        db.session.commit()

        # ======================================================================
        # PRINT VIVA VOCE CHEAT SHEET
        # ======================================================================
        print("\n" + "=" * 75)
        print(" [SUCCESS] EMP DATABASE POPULATED FOR VIVA VOCE DEMONSTRATION")
        print("=" * 75)
        print("\n--- 1. DEMO CREDENTIALS REFERENCE ---")
        print("  Role       | Email                      | Password     | Scenario / Purpose")
        print("  -----------+----------------------------+--------------+-------------------------------------------")
        print("  Admin      | Admin@gmail.com            | Admin@1234   | Full management, approvals, override")
        print("  Examiner   | priya.sharma@gmail.com     | Examiner@123 | Approved faculty: ready for live grading")
        print("  Examiner   | rajesh.kumar@gmail.com     | Examiner@123 | Approved faculty: slot management")
        print("  Examiner   | ananya.sen@gmail.com       | Examiner@123 | Pending approval: test admin approval")
        print("  Examiner   | vikram.aditya@gmail.com    | Examiner@123 | Inactive: test suspended account notice")
        print("  Student    | amit.gupta@gmail.com       | Student@123  | Fresh candidate: ready for LIVE BOOKING")
        print("  Student    | rahul.verma@gmail.com      | Student@123  | Active in CS101, Completed in CS303")
        print("  Student    | sneha.patel@gmail.com      | Student@123  | Top scorer scorecard in CS303 (98%)")
        print("  Student    | pooja.nair@gmail.com       | Student@123  | Cancelled reservation audit record")
        print("  Student    | kavita.krishnan@gmail.com  | Student@123  | Booked in CS101: waiting to be evaluated")
        print("\n--- 2. STEP-BY-STEP VIVA VIDEO DEMONSTRATION SCRIPT ---")
        print("  Step 1: Admin Overview")
        print("          - Log in as Admin@gmail.com / Admin@1234.")
        print("          - Show Courses (CS101-CS404 active, CS505 inactive).")
        print("          - Show Examinations in all 5 states (Draft, Slot Creation, Booking Open, Closed, Completed).")
        print("          - Go to Examiners: Approve Dr. Ananya Sen (ananya.sen@gmail.com).")
        print("  Step 2: Examiner Slot Management & Isolation")
        print("          - Log in as rajesh.kumar@gmail.com.")
        print("          - Open CS202 (Slot Creation Phase): create/edit a new examination slot.")
        print("          - Notice: Dr. Rajesh cannot edit slots of CS101 once student booking has begun (Rule 1).")
        print("  Step 3: Student Slot Booking & Business Rules")
        print("          - Log in as fresh candidate amit.gupta@gmail.com.")
        print("          - Browse CS101: Slot 1 is marked 'Full' (cannot book).")
        print("          - Book Slot 2 (1 seat remaining): Notice seat count immediately becomes 0 and slot turns 'Full' (Rules 3 & 4).")
        print("          - Try to book another slot in CS101: Rejected due to Duplicate Booking Rule (Rule 5).")
        print("  Step 4: Examiner Live Grading & Evaluation")
        print("          - Log in as priya.sharma@gmail.com.")
        print("          - Open Candidates / Roster: Find student 'Kavita Krishnan'.")
        print("          - Click 'Evaluate': enter rubric scores & qualitative remarks, then submit.")
        print("  Step 5: Student Scorecard & Cancellation")
        print("          - Log in as rahul.verma@gmail.com or sneha.patel@gmail.com.")
        print("          - View completed detailed scorecard with rubric breakdowns & percentage.")
        print("          - Log in as pooja.nair@gmail.com: show audit trail of cancelled booking (Rule 8).")
        print("=" * 75 + "\n")

if __name__ == '__main__':
    seed_database()
