from datetime import datetime, date, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, User, Course, Examination, Rubric, ExaminationSlot, Booking, Evaluation
from utils.decorators import role_required

examiner_bp = Blueprint('examiner', __name__, url_prefix='/examiner')

@examiner_bp.before_request
@login_required
@role_required('examiner')
def check_examiner():
    pass


# ==========================================
# EXAMINER DASHBOARD
# ==========================================
@examiner_bp.route('/')
@examiner_bp.route('/dashboard')
def dashboard():
    now = datetime.now()
    # Examiner's slots
    my_slots = ExaminationSlot.query.filter_by(examiner_id=current_user.id).all()
    slot_ids = [s.slot_id for s in my_slots]

    # Active examinations
    active_examinations = Examination.query.filter(
        Examination.status.in_(['Slot Creation', 'Booking Open', 'Closed'])
    ).all()

    # Bookings in my slots
    my_bookings = Booking.query.filter(Booking.slot_id.in_(slot_ids)).all() if slot_ids else []
    total_students_booked = sum(1 for b in my_bookings if b.status in ['Booked', 'Completed'])
    
    # Pending evaluations: Booked students who have not yet been evaluated
    pending_evaluations = [
        b for b in my_bookings 
        if b.status == 'Booked' and not b.is_evaluated
    ]

    return render_template(
        'examiner/dashboard.html',
        total_slots=len(my_slots),
        total_students_booked=total_students_booked,
        pending_evaluations_count=len(pending_evaluations),
        pending_evaluations=pending_evaluations[:5],
        recent_slots=my_slots[:5],
        active_examinations=active_examinations,
        now=now
    )


# ==========================================
# ASSIGNED / AVAILABLE EXAMINATIONS
# ==========================================
@examiner_bp.route('/examinations')
def assigned_examinations():
    now = datetime.now()
    # List examinations open for slot creation or where examiner already has slots
    all_exams = Examination.query.filter(Examination.status != 'Draft').order_by(Examination.slot_creation_start.desc()).all()
    my_slots = ExaminationSlot.query.filter_by(examiner_id=current_user.id).all()
    my_exam_ids = {s.examination_id for s in my_slots}

    return render_template(
        'examiner/assigned_exams.html',
        examinations=all_exams,
        my_exam_ids=my_exam_ids,
        now=now
    )


# ==========================================
# SLOT MANAGEMENT
# ==========================================
@examiner_bp.route('/slots')
def slots():
    now = datetime.now()
    exam_filter = request.args.get('exam_id')

    query = ExaminationSlot.query.filter_by(examiner_id=current_user.id)
    if exam_filter:
        query = query.filter_by(examination_id=exam_filter)

    my_slots = query.order_by(ExaminationSlot.date.desc(), ExaminationSlot.start_time.asc()).all()
    examinations = Examination.query.filter(Examination.status != 'Draft').all()

    return render_template('examiner/slots.html', slots=my_slots, examinations=examinations, selected_exam_id=exam_filter, now=now)


@examiner_bp.route('/slots/new', methods=['GET', 'POST'])
def new_slot():
    now = datetime.now()
    exam_id = request.args.get('exam_id') or request.form.get('examination_id')
    available_exams = Examination.query.filter(Examination.status != 'Draft').all()

    selected_exam = None
    if exam_id:
        selected_exam = Examination.query.get(exam_id)

    if request.method == 'POST':
        examination_id = request.form.get('examination_id')
        exam = Examination.query.get_or_404(examination_id)

        # RULE 1: Slot Creation Period
        # Examiner can create slots ONLY during the configured slot creation period:
        # current_time >= slot_creation_start AND current_time <= slot_creation_end
        if not (exam.slot_creation_start <= now <= exam.slot_creation_end):
            flash(
                f'Slot creation is NOT open for "{exam.examination_name}". '
                f'Slot Creation Window is: {exam.slot_creation_start.strftime("%Y-%m-%d %H:%M")} to {exam.slot_creation_end.strftime("%Y-%m-%d %H:%M")}.',
                'danger'
            )
            return render_template('examiner/slot_form.html', examinations=available_exams, selected_exam=exam, is_edit=False)

        slot_date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        capacity_str = request.form.get('maximum_student_capacity', 1)

        errors = []
        try:
            slot_date = datetime.strptime(slot_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            errors.append('Invalid date provided.')

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            if end_time <= start_time:
                errors.append('Slot end time must be later than start time.')
        except (ValueError, TypeError):
            errors.append('Invalid time provided.')

        try:
            capacity = int(capacity_str)
            if capacity <= 0:
                errors.append('Maximum capacity must be at least 1 student.')
        except (ValueError, TypeError):
            errors.append('Capacity must be a valid number.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('examiner/slot_form.html', examinations=available_exams, selected_exam=exam, is_edit=False)

        new_slot_obj = ExaminationSlot(
            examination_id=exam.exam_id,
            examiner_id=current_user.id,
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
            maximum_student_capacity=capacity,
            available_seats=capacity,
            status='Available'
        )
        db.session.add(new_slot_obj)
        db.session.commit()

        flash(f'Examination slot for {slot_date} ({start_time}-{end_time}) created successfully!', 'success')
        return redirect(url_for('examiner.slots'))

    return render_template('examiner/slot_form.html', examinations=available_exams, selected_exam=selected_exam, is_edit=False)


@examiner_bp.route('/slots/<int:slot_id>/edit', methods=['GET', 'POST'])
def edit_slot(slot_id):
    slot = ExaminationSlot.query.get_or_404(slot_id)
    now = datetime.now()

    # Rule 6: Examiner authorization
    if slot.examiner_id != current_user.id:
        flash('Unauthorized: You can only edit your own slots.', 'danger')
        return redirect(url_for('examiner.slots'))

    exam = slot.examination

    # RULE 1: Can only edit during slot creation period, AND cannot edit if booking has started
    if not (exam.slot_creation_start <= now <= exam.slot_creation_end):
        flash('Slot cannot be edited: Slot creation period has closed for this examination.', 'danger')
        return redirect(url_for('examiner.slots'))

    if now >= exam.slot_booking_start:
        flash('Slot cannot be edited: Student booking has already started.', 'danger')
        return redirect(url_for('examiner.slots'))

    if request.method == 'POST':
        slot_date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        capacity_str = request.form.get('maximum_student_capacity')

        errors = []
        try:
            slot_date = datetime.strptime(slot_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            errors.append('Invalid date provided.')

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            if end_time <= start_time:
                errors.append('Slot end time must be later than start time.')
        except (ValueError, TypeError):
            errors.append('Invalid time provided.')

        try:
            capacity = int(capacity_str)
            if capacity <= 0:
                errors.append('Capacity must be at least 1.')
        except (ValueError, TypeError):
            errors.append('Capacity must be a valid number.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('examiner/slot_form.html', slot=slot, is_edit=True)

        slot.date = slot_date
        slot.start_time = start_time
        slot.end_time = end_time
        slot.maximum_student_capacity = capacity
        slot.recalculate_seats()
        db.session.commit()

        flash('Slot updated successfully.', 'success')
        return redirect(url_for('examiner.slots'))

    return render_template('examiner/slot_form.html', slot=slot, is_edit=True)


@examiner_bp.route('/slots/<int:slot_id>/delete', methods=['POST'])
def delete_slot(slot_id):
    slot = ExaminationSlot.query.get_or_404(slot_id)
    now = datetime.now()

    if slot.examiner_id != current_user.id:
        flash('Unauthorized: You can only delete your own slots.', 'danger')
        return redirect(url_for('examiner.slots'))

    exam = slot.examination

    # Rule 1: Cannot delete if booking started or creation window closed
    if now >= exam.slot_booking_start:
        flash('Slot cannot be deleted: Student booking has already started.', 'danger')
        return redirect(url_for('examiner.slots'))

    if not (exam.slot_creation_start <= now <= exam.slot_creation_end):
        flash('Slot cannot be deleted: Slot creation period has ended.', 'danger')
        return redirect(url_for('examiner.slots'))

    db.session.delete(slot)
    db.session.commit()
    flash('Slot deleted successfully.', 'success')
    return redirect(url_for('examiner.slots'))


# ==========================================
# STUDENT MANAGEMENT & EVALUATION
# ==========================================
@examiner_bp.route('/students')
def students():
    # Examiner can view students booked ONLY in their own slots
    my_slots = ExaminationSlot.query.filter_by(examiner_id=current_user.id).all()
    slot_ids = [s.slot_id for s in my_slots]

    exam_filter = request.args.get('exam_id')
    status_filter = request.args.get('status', '').strip()

    bookings = []
    if slot_ids:
        query = Booking.query.filter(Booking.slot_id.in_(slot_ids))
        if exam_filter:
            query = query.filter(Booking.slot.has(ExaminationSlot.examination_id == exam_filter))
        if status_filter:
            query = query.filter_by(status=status_filter)
        bookings = query.order_by(Booking.booking_date.desc()).all()

    examinations = Examination.query.filter(Examination.status != 'Draft').all()

    return render_template(
        'examiner/students.html',
        bookings=bookings,
        examinations=examinations,
        selected_exam_id=exam_filter,
        status_filter=status_filter
    )


@examiner_bp.route('/evaluate/<int:booking_id>', methods=['GET', 'POST'])
def evaluate_student(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    slot = booking.slot

    # Rule 6: Examiner Authorization
    # Examiner can evaluate ONLY students booked into slots created by that examiner!
    if slot.examiner_id != current_user.id:
        flash('Access Denied: You are not authorized to evaluate students booked under another examiner.', 'danger')
        return redirect(url_for('examiner.students'))

    exam = slot.examination
    rubrics = exam.rubrics

    if not rubrics:
        flash('This examination does not have any rubric criteria defined yet. Please contact the administrator.', 'warning')

    # Existing evaluations for this booking
    existing_evals = {e.rubric_id: e for e in booking.evaluations}

    if request.method == 'POST':
        errors = []
        eval_entries = []

        for rubric in rubrics:
            marks_str = request.form.get(f'marks_{rubric.rubric_id}', '').strip()
            remarks = request.form.get(f'remarks_{rubric.rubric_id}', '').strip()

            if marks_str == '':
                errors.append(f'Marks are required for criterion: "{rubric.criterion_name}".')
                continue

            try:
                marks_val = float(marks_str)
                if marks_val < 0:
                    errors.append(f'Marks for "{rubric.criterion_name}" cannot be negative.')
                elif marks_val > rubric.maximum_marks:
                    errors.append(f'Marks for "{rubric.criterion_name}" ({marks_val}) exceed maximum allowed marks ({rubric.maximum_marks}).')
                else:
                    eval_entries.append((rubric.rubric_id, marks_val, remarks))
            except ValueError:
                errors.append(f'Invalid marks entered for "{rubric.criterion_name}".')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('examiner/evaluate.html', booking=booking, exam=exam, rubrics=rubrics, existing_evals=existing_evals)

        # Save evaluations in SQLite
        for rubric_id, marks_val, remarks in eval_entries:
            if rubric_id in existing_evals:
                ev = existing_evals[rubric_id]
                ev.marks = marks_val
                ev.remarks = remarks
                ev.evaluated_at = datetime.now()
            else:
                new_ev = Evaluation(
                    booking_id=booking.booking_id,
                    rubric_id=rubric_id,
                    marks=marks_val,
                    remarks=remarks,
                    evaluated_at=datetime.now()
                )
                db.session.add(new_ev)

        # Mark booking as Completed
        booking.status = 'Completed'
        db.session.commit()

        flash(f'Evaluation submitted successfully for student {booking.student.name}!', 'success')
        return redirect(url_for('examiner.students'))

    return render_template('examiner/evaluate.html', booking=booking, exam=exam, rubrics=rubrics, existing_evals=existing_evals)
