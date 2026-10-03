from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, User, Course, Examination, Rubric, ExaminationSlot, Booking, Evaluation
from utils.decorators import role_required

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
@login_required
@role_required('student')
def check_student():
    pass


# ==========================================
# STUDENT DASHBOARD
# ==========================================
@student_bp.route('/')
@student_bp.route('/dashboard')
def dashboard():
    now = datetime.now()

    # Active student bookings
    all_bookings = Booking.query.filter_by(student_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    upcoming_bookings = [b for b in all_bookings if b.status == 'Booked']
    completed_bookings = [b for b in all_bookings if b.status == 'Completed' or b.is_evaluated]

    # Available examinations currently in booking open period
    available_examinations = [
        exam for exam in Examination.query.filter(
            Examination.status.in_(['Booking Open', 'Slot Creation'])
        ).all()
        if exam.slot_booking_start <= now <= exam.slot_booking_end
    ]

    # Exam IDs student already has booked
    active_booked_exam_ids = {
        b.slot.examination_id for b in all_bookings if b.status == 'Booked' and b.slot
    }

    return render_template(
        'student/dashboard.html',
        upcoming_bookings=upcoming_bookings,
        completed_bookings=completed_bookings,
        all_bookings_count=len(all_bookings),
        available_examinations=available_examinations,
        active_booked_exam_ids=active_booked_exam_ids,
        now=now
    )


# ==========================================
# EXAMINATION SEARCH & DETAILS
# ==========================================
@student_bp.route('/examinations')
def examinations():
    now = datetime.now()
    search_query = request.args.get('q', '').strip()
    type_filter = request.args.get('type', '').strip()

    query = Examination.query.filter(Examination.status != 'Draft')
    if search_query:
        query = query.filter(
            or_(
                Examination.examination_name.ilike(f'%{search_query}%'),
                Examination.course.has(Course.course_name.ilike(f'%{search_query}%')),
                Examination.course.has(Course.course_code.ilike(f'%{search_query}%'))
            )
        )
    if type_filter:
        query = query.filter_by(examination_type=type_filter)

    exam_list = query.order_by(Examination.slot_booking_start.asc()).all()

    # Get student's booked exam IDs to show "Already Booked" badge
    my_active_bookings = Booking.query.filter_by(student_id=current_user.id, status='Booked').all()
    my_booked_exam_ids = {b.slot.examination_id for b in my_active_bookings if b.slot}

    return render_template(
        'student/examinations.html',
        examinations=exam_list,
        my_booked_exam_ids=my_booked_exam_ids,
        search_query=search_query,
        type_filter=type_filter,
        now=now
    )


@student_bp.route('/examinations/<int:exam_id>')
def examination_detail(exam_id):
    now = datetime.now()
    exam = Examination.query.get_or_404(exam_id)
    rubrics = Rubric.query.filter_by(examination_id=exam_id).all()

    # Slots for this examination
    slots = ExaminationSlot.query.filter_by(examination_id=exam_id).order_by(
        ExaminationSlot.date.asc(), ExaminationSlot.start_time.asc()
    ).all()

    # Check if student already has an active booking for this exam
    existing_booking = Booking.query.filter(
        Booking.student_id == current_user.id,
        Booking.status == 'Booked',
        Booking.slot.has(ExaminationSlot.examination_id == exam_id)
    ).first()

    is_booking_open = exam.slot_booking_start <= now <= exam.slot_booking_end

    return render_template(
        'student/examination_detail.html',
        exam=exam,
        rubrics=rubrics,
        slots=slots,
        existing_booking=existing_booking,
        is_booking_open=is_booking_open,
        now=now
    )


# ==========================================
# SLOT BOOKING & CANCELLATION
# ==========================================
@student_bp.route('/slots/<int:slot_id>/book', methods=['POST'])
def book_slot(slot_id):
    now = datetime.now()
    slot = ExaminationSlot.query.get_or_404(slot_id)
    exam = slot.examination

    # RULE 2: Student Booking Period
    # Student can book slots only when current_time >= slot_booking_start AND current_time <= slot_booking_end
    if not (exam.slot_booking_start <= now <= exam.slot_booking_end):
        flash(
            f'Booking is closed for this examination. '
            f'The booking window is {exam.slot_booking_start.strftime("%Y-%m-%d %H:%M")} to {exam.slot_booking_end.strftime("%Y-%m-%d %H:%M")}.',
            'danger'
        )
        return redirect(url_for('student.examination_detail', exam_id=exam.exam_id))

    # RULE 5: Duplicate Booking
    # A student cannot have multiple bookings for the same examination
    existing_booking = Booking.query.filter(
        Booking.student_id == current_user.id,
        Booking.status == 'Booked',
        Booking.slot.has(ExaminationSlot.examination_id == exam.exam_id)
    ).first()

    if existing_booking:
        flash(f'You already have an active booking for "{exam.examination_name}". You cannot book multiple slots for the same examination.', 'warning')
        return redirect(url_for('student.examination_detail', exam_id=exam.exam_id))

    # RULE 3 & 4: Capacity check & Automatic Full status
    slot.recalculate_seats()
    if slot.available_seats <= 0 or slot.status != 'Available':
        flash('This examination slot is already full or unavailable.', 'danger')
        return redirect(url_for('student.examination_detail', exam_id=exam.exam_id))

    # Create Booking
    booking = Booking(
        student_id=current_user.id,
        slot_id=slot.slot_id,
        booking_date=datetime.now(),
        status='Booked'
    )
    db.session.add(booking)

    # Recalculate available seats and status
    slot.available_seats -= 1
    if slot.available_seats <= 0:
        slot.status = 'Full'

    db.session.commit()

    flash(f'Successfully booked slot for "{exam.examination_name}" on {slot.date} ({slot.start_time}-{slot.end_time}) with Examiner {slot.examiner.name}!', 'success')
    return redirect(url_for('student.my_bookings'))


@student_bp.route('/bookings')
def my_bookings():
    now = datetime.now()
    bookings_list = Booking.query.filter_by(student_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('student/my_bookings.html', bookings=bookings_list, now=now)


@student_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    now = datetime.now()
    booking = Booking.query.filter_by(booking_id=booking_id, student_id=current_user.id).first_or_404()

    if booking.status != 'Booked':
        flash('Only active bookings can be cancelled.', 'warning')
        return redirect(url_for('student.my_bookings'))

    exam = booking.slot.examination
    # Booking cancellation rule: Can cancel before booking deadline
    if now > exam.slot_booking_end:
        flash('Booking deadline has passed. Cancellation is no longer permitted.', 'danger')
        return redirect(url_for('student.my_bookings'))

    # Update status to Cancelled (Rule 8: Booking history preserved)
    booking.status = 'Cancelled'

    # Rule 6: Cancelled booking releases seat
    slot = booking.slot
    slot.recalculate_seats()

    db.session.commit()
    flash('Your examination booking has been successfully cancelled. The seat has been released.', 'info')
    return redirect(url_for('student.my_bookings'))


# ==========================================
# RESULTS & EVALUATION HISTORY
# ==========================================
@student_bp.route('/results')
def results():
    # Only show bookings that are Completed or have evaluations
    evaluated_bookings = Booking.query.filter(
        Booking.student_id == current_user.id,
        Booking.status == 'Completed'
    ).order_by(Booking.booking_date.desc()).all()

    return render_template('student/results.html', bookings=evaluated_bookings)


@student_bp.route('/results/<int:booking_id>')
def result_detail(booking_id):
    booking = Booking.query.filter_by(booking_id=booking_id, student_id=current_user.id).first_or_404()
    if not booking.is_evaluated and booking.status != 'Completed':
        flash('Results for this examination are not yet available.', 'warning')
        return redirect(url_for('student.results'))

    slot = booking.slot
    exam = slot.examination
    evaluations = booking.evaluations

    return render_template('student/result_detail.html', booking=booking, exam=exam, slot=slot, evaluations=evaluations)
