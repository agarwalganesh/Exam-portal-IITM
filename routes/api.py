from flask import Blueprint, jsonify, request
from models import Examination, ExaminationSlot, Booking, User, ExaminerProfile

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/examinations', methods=['GET'])
def get_examinations():
    status = request.args.get('status')
    query = Examination.query
    if status:
        query = query.filter_by(status=status)
    exams = query.all()

    return jsonify([
        {
            'exam_id': e.exam_id,
            'course_code': e.course.course_code if e.course else None,
            'course_name': e.course.course_name if e.course else None,
            'examination_name': e.examination_name,
            'examination_type': e.examination_type,
            'duration': e.duration,
            'maximum_marks': e.maximum_marks,
            'slot_creation_start': e.slot_creation_start.isoformat(),
            'slot_creation_end': e.slot_creation_end.isoformat(),
            'slot_booking_start': e.slot_booking_start.isoformat(),
            'slot_booking_end': e.slot_booking_end.isoformat(),
            'status': e.status,
            'rubrics_count': len(e.rubrics),
            'slots_count': len(e.slots)
        } for e in exams
    ])


@api_bp.route('/examinations/<int:exam_id>', methods=['GET'])
def get_examination_detail(exam_id):
    e = Examination.query.get_or_404(exam_id)
    return jsonify({
        'exam_id': e.exam_id,
        'course_code': e.course.course_code if e.course else None,
        'course_name': e.course.course_name if e.course else None,
        'examination_name': e.examination_name,
        'examination_type': e.examination_type,
        'duration': e.duration,
        'maximum_marks': e.maximum_marks,
        'slot_creation_start': e.slot_creation_start.isoformat(),
        'slot_creation_end': e.slot_creation_end.isoformat(),
        'slot_booking_start': e.slot_booking_start.isoformat(),
        'slot_booking_end': e.slot_booking_end.isoformat(),
        'status': e.status,
        'rubrics': [
            {
                'rubric_id': r.rubric_id,
                'criterion_name': r.criterion_name,
                'maximum_marks': r.maximum_marks,
                'weightage': r.weightage,
                'description': r.description
            } for r in e.rubrics
        ],
        'slots': [
            {
                'slot_id': s.slot_id,
                'examiner_name': s.examiner.name if s.examiner else None,
                'date': s.date.isoformat(),
                'start_time': s.start_time.strftime('%H:%M'),
                'end_time': s.end_time.strftime('%H:%M'),
                'maximum_capacity': s.maximum_student_capacity,
                'available_seats': s.available_seats,
                'status': s.status
            } for s in e.slots
        ]
    })


@api_bp.route('/slots', methods=['GET'])
def get_slots():
    exam_id = request.args.get('exam_id')
    status = request.args.get('status')
    query = ExaminationSlot.query
    if exam_id:
        query = query.filter_by(examination_id=exam_id)
    if status:
        query = query.filter_by(status=status)
    slots = query.all()

    return jsonify([
        {
            'slot_id': s.slot_id,
            'examination_id': s.examination_id,
            'examination_name': s.examination.examination_name if s.examination else None,
            'examiner_id': s.examiner_id,
            'examiner_name': s.examiner.name if s.examiner else None,
            'date': s.date.isoformat(),
            'start_time': s.start_time.strftime('%H:%M'),
            'end_time': s.end_time.strftime('%H:%M'),
            'capacity': s.maximum_student_capacity,
            'available_seats': s.available_seats,
            'status': s.status
        } for s in slots
    ])


@api_bp.route('/bookings', methods=['GET'])
def get_bookings():
    query = Booking.query.all()
    return jsonify([
        {
            'booking_id': b.booking_id,
            'student_id': b.student_id,
            'student_name': b.student.name if b.student else None,
            'slot_id': b.slot_id,
            'examination_name': b.slot.examination.examination_name if b.slot and b.slot.examination else None,
            'examiner_name': b.slot.examiner.name if b.slot and b.slot.examiner else None,
            'date': b.slot.date.isoformat() if b.slot else None,
            'time': f"{b.slot.start_time.strftime('%H:%M')} - {b.slot.end_time.strftime('%H:%M')}" if b.slot else None,
            'status': b.status,
            'booking_date': b.booking_date.isoformat(),
            'is_evaluated': b.is_evaluated,
            'marks_obtained': b.total_marks_obtained if b.is_evaluated else None
        } for b in query
    ])


@api_bp.route('/examiners', methods=['GET'])
def get_examiners():
    examiners = User.query.filter_by(role='examiner').all()
    return jsonify([
        {
            'examiner_id': u.id,
            'name': u.name,
            'email': u.email,
            'department': u.examiner_profile.department if u.examiner_profile else None,
            'contact_details': u.examiner_profile.contact_details if u.examiner_profile else None,
            'status': u.status,
            'slots_count': len(u.slots)
        } for u in examiners
    ])
