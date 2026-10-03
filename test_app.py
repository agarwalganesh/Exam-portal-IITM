import unittest
from datetime import datetime, timedelta, date, time
from app import create_app
from config import Config
from models import db, User, Course, Examination, Rubric, ExaminationSlot, Booking, Evaluation

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class EMPTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_default_admin_created(self):
        admin = User.query.filter_by(role='admin').first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.email, 'admin@emp.iitm.ac.in')
        self.assertTrue(admin.check_password('Admin@123'))

    def test_examiner_registration_and_approval_workflow(self):
        # Register new examiner
        res = self.client.post('/register/examiner', data={
            'name': 'Dr. Test Examiner',
            'email': 'test.examiner@emp.iitm.ac.in',
            'department': 'Mechanical Engineering',
            'contact_details': '+91 99999 11111',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        examiner = User.query.filter_by(email='test.examiner@emp.iitm.ac.in').first()
        self.assertIsNotNone(examiner)
        self.assertEqual(examiner.role, 'examiner')
        self.assertEqual(examiner.status, 'pending')

        # Try to access examiner dashboard while pending -> should be redirected to pending-approval
        self.client.post('/login', data={'email': 'test.examiner@emp.iitm.ac.in', 'password': 'Password@123'})
        dash_res = self.client.get('/examiner/dashboard', follow_redirects=True)
        self.assertIn(b'pending-approval', dash_res.request.path.encode())

        # Admin logs in and approves examiner
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={'email': 'admin@emp.iitm.ac.in', 'password': 'Admin@123'})
        approve_res = self.client.post(f'/admin/examiners/{examiner.id}/approve', follow_redirects=True)
        self.assertEqual(approve_res.status_code, 200)

        examiner_updated = User.query.get(examiner.id)
        self.assertEqual(examiner_updated.status, 'active')

        # Now examiner logs in and can access dashboard
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={'email': 'test.examiner@emp.iitm.ac.in', 'password': 'Password@123'})
        dash_res2 = self.client.get('/examiner/dashboard')
        self.assertEqual(dash_res2.status_code, 200)

    def test_course_crud(self):
        self.client.post('/login', data={'email': 'admin@emp.iitm.ac.in', 'password': 'Admin@123'})
        # Create course
        create_res = self.client.post('/admin/courses/new', data={
            'course_code': 'TEST101',
            'course_name': 'Test Systems 101',
            'description': 'Testing course functionality',
            'status': 'active'
        }, follow_redirects=True)
        self.assertEqual(create_res.status_code, 200)
        c = Course.query.filter_by(course_code='TEST101').first()
        self.assertIsNotNone(c)

        # Edit course
        edit_res = self.client.post(f'/admin/courses/{c.course_id}/edit', data={
            'course_code': 'TEST101',
            'course_name': 'Test Systems 101 Updated',
            'description': 'Updated description',
            'status': 'active'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)
        c_updated = Course.query.get(c.course_id)
        self.assertEqual(c_updated.course_name, 'Test Systems 101 Updated')

    def test_examination_and_rubrics_crud(self):
        self.client.post('/login', data={'email': 'admin@emp.iitm.ac.in', 'password': 'Admin@123'})
        course = Course(course_code='CS100', course_name='Computer Science Intro', status='active')
        db.session.add(course)
        db.session.commit()

        now = datetime.now()
        # Create examination
        exam_res = self.client.post('/admin/examinations/new', data={
            'course_id': course.course_id,
            'examination_name': 'CS100 Viva Exam',
            'examination_type': 'Viva',
            'duration': 30,
            'maximum_marks': 100.0,
            'slot_creation_start': (now - timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'slot_creation_end': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'slot_booking_start': (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'slot_booking_end': (now + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
            'status': 'Booking Open'
        }, follow_redirects=True)
        self.assertEqual(exam_res.status_code, 200)

        exam = Examination.query.filter_by(examination_name='CS100 Viva Exam').first()
        self.assertIsNotNone(exam)

        # Add rubric
        rubric_res = self.client.post(f'/admin/examinations/{exam.exam_id}/rubrics/new', data={
            'criterion_name': 'Technical Concepts',
            'maximum_marks': 50.0,
            'weightage': 50.0,
            'description': 'Core fundamentals'
        }, follow_redirects=True)
        self.assertEqual(rubric_res.status_code, 200)

        rubric = Rubric.query.filter_by(examination_id=exam.exam_id).first()
        self.assertIsNotNone(rubric)
        self.assertEqual(rubric.maximum_marks, 50.0)

    def test_slot_creation_window_and_booking_rules(self):
        # 1. Setup Examiner & Student
        examiner = User(name='Dr. Examiner', email='dr.ex@emp.iitm.ac.in', role='examiner', status='active')
        examiner.set_password('Ex@123')
        student1 = User(name='Student One', email='s1@student.iitm.ac.in', role='student', status='active')
        student1.set_password('St@123')
        student2 = User(name='Student Two', email='s2@student.iitm.ac.in', role='student', status='active')
        student2.set_password('St@123')
        course = Course(course_code='CS500', course_name='Advanced CS', status='active')
        db.session.add_all([examiner, student1, student2, course])
        db.session.commit()

        now = datetime.now()

        # Exam with active slot creation window & active booking window
        exam = Examination(
            course_id=course.course_id,
            examination_name='CS500 Final Assessment',
            examination_type='Assessment',
            duration=30,
            maximum_marks=50.0,
            slot_creation_start=now - timedelta(hours=2),
            slot_creation_end=now + timedelta(hours=2),
            slot_booking_start=now - timedelta(hours=1),
            slot_booking_end=now + timedelta(hours=5),
            status='Booking Open'
        )
        db.session.add(exam)
        db.session.commit()

        rubric = Rubric(
            examination_id=exam.exam_id,
            criterion_name='Knowledge Mastery',
            maximum_marks=50.0,
            weightage=100.0
        )
        db.session.add(rubric)
        db.session.commit()

        # Slot with capacity = 1
        slot = ExaminationSlot(
            examination_id=exam.exam_id,
            examiner_id=examiner.id,
            date=(now + timedelta(days=1)).date(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            maximum_student_capacity=1,
            available_seats=1,
            status='Available'
        )
        db.session.add(slot)
        db.session.commit()

        # Student 1 books slot
        self.client.post('/login', data={'email': 's1@student.iitm.ac.in', 'password': 'St@123'})
        book_res = self.client.post(f'/student/slots/{slot.slot_id}/book', follow_redirects=True)
        self.assertEqual(book_res.status_code, 200)

        # Verify capacity decremented and slot became Full (Rule 3 & 4)
        updated_slot = ExaminationSlot.query.get(slot.slot_id)
        self.assertEqual(updated_slot.available_seats, 0)
        self.assertEqual(updated_slot.status, 'Full')

        # Rule 5: Duplicate booking prevention (Student 1 tries to book again for same exam)
        # Create second slot
        slot2 = ExaminationSlot(
            examination_id=exam.exam_id,
            examiner_id=examiner.id,
            date=(now + timedelta(days=1)).date(),
            start_time=time(11, 0),
            end_time=time(11, 30),
            maximum_student_capacity=2,
            available_seats=2,
            status='Available'
        )
        db.session.add(slot2)
        db.session.commit()

        dup_res = self.client.post(f'/student/slots/{slot2.slot_id}/book', follow_redirects=True)
        self.assertIn(b'already have an active booking', dup_res.data)

        # Student 2 tries to book slot 1 which is Full -> should be rejected
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={'email': 's2@student.iitm.ac.in', 'password': 'St@123'})
        full_res = self.client.post(f'/student/slots/{slot.slot_id}/book', follow_redirects=True)
        self.assertIn(b'full or unavailable', full_res.data)

        # Student 1 cancels booking -> seat released (Rule 6) and status set to Cancelled (Rule 8)
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={'email': 's1@student.iitm.ac.in', 'password': 'St@123'})
        booking1 = Booking.query.filter_by(student_id=student1.id, slot_id=slot.slot_id).first()
        cancel_res = self.client.post(f'/student/bookings/{booking1.booking_id}/cancel', follow_redirects=True)
        self.assertEqual(cancel_res.status_code, 200)

        slot_after_cancel = ExaminationSlot.query.get(slot.slot_id)
        self.assertEqual(slot_after_cancel.available_seats, 1)
        self.assertEqual(slot_after_cancel.status, 'Available')
        booking_after_cancel = Booking.query.get(booking1.booking_id)
        self.assertEqual(booking_after_cancel.status, 'Cancelled')

    def test_examiner_evaluation_and_result(self):
        # Setup Examiner, Student, Course, Exam, Rubric, Slot, Booking
        now = datetime.now()
        examiner = User(name='Dr. Smith', email='smith@emp.iitm.ac.in', role='examiner', status='active')
        examiner.set_password('Smith@123')
        student = User(name='Alice', email='alice@student.iitm.ac.in', role='student', status='active')
        student.set_password('Alice@123')
        course = Course(course_code='CS600', course_name='Security', status='active')
        db.session.add_all([examiner, student, course])
        db.session.commit()

        exam = Examination(
            course_id=course.course_id,
            examination_name='Security Practical',
            examination_type='Practical',
            duration=45,
            maximum_marks=50.0,
            slot_creation_start=now - timedelta(days=2),
            slot_creation_end=now + timedelta(days=2),
            slot_booking_start=now - timedelta(days=1),
            slot_booking_end=now + timedelta(days=2),
            status='Booking Open'
        )
        db.session.add(exam)
        db.session.commit()

        rubric = Rubric(
            examination_id=exam.exam_id,
            criterion_name='Penetration Testing',
            maximum_marks=50.0,
            weightage=100.0
        )
        db.session.add(rubric)
        db.session.commit()

        slot = ExaminationSlot(
            examination_id=exam.exam_id,
            examiner_id=examiner.id,
            date=now.date(),
            start_time=time(14, 0),
            end_time=time(14, 45),
            maximum_student_capacity=1,
            available_seats=0,
            status='Full'
        )
        db.session.add(slot)
        db.session.commit()

        booking = Booking(student_id=student.id, slot_id=slot.slot_id, status='Booked')
        db.session.add(booking)
        db.session.commit()

        # Examiner logs in and evaluates Alice
        self.client.post('/login', data={'email': 'smith@emp.iitm.ac.in', 'password': 'Smith@123'})

        # Validation: Marks cannot exceed maximum (e.g. entering 55 when max is 50)
        invalid_eval = self.client.post(f'/examiner/evaluate/{booking.booking_id}', data={
            f'marks_{rubric.rubric_id}': '55.0',
            f'remarks_{rubric.rubric_id}': 'Exceeds max'
        }, follow_redirects=True)
        self.assertIn(b'exceed maximum allowed marks', invalid_eval.data)

        # Valid evaluation submission
        valid_eval = self.client.post(f'/examiner/evaluate/{booking.booking_id}', data={
            f'marks_{rubric.rubric_id}': '46.5',
            f'remarks_{rubric.rubric_id}': 'Excellent exploit identification and methodology.'
        }, follow_redirects=True)
        self.assertEqual(valid_eval.status_code, 200)

        # Verify booking status became Completed
        updated_b = Booking.query.get(booking.booking_id)
        self.assertEqual(updated_b.status, 'Completed')
        self.assertTrue(updated_b.is_evaluated)
        self.assertEqual(updated_b.total_marks_obtained, 46.5)

        # Alice logs in and checks scorecard
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={'email': 'alice@student.iitm.ac.in', 'password': 'Alice@123'})
        result_res = self.client.get(f'/student/results/{booking.booking_id}')
        self.assertEqual(result_res.status_code, 200)
        self.assertIn(b'46.5', result_res.data)
        self.assertIn(b'Excellent exploit identification', result_res.data)

    def test_rest_api_endpoints(self):
        res1 = self.client.get('/api/examinations')
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.is_json)

        res2 = self.client.get('/api/slots')
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.is_json)

        res3 = self.client.get('/api/examiners')
        self.assertEqual(res3.status_code, 200)
        self.assertTrue(res3.is_json)

        res4 = self.client.get('/api/bookings')
        self.assertEqual(res4.status_code, 200)
        self.assertTrue(res4.is_json)

if __name__ == '__main__':
    unittest.main()
