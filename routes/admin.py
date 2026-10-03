from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, User, ExaminerProfile, Course, Examination, Rubric, ExaminationSlot, Booking, Evaluation
from utils.decorators import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
@role_required('admin')
def check_admin():
    pass


# ==========================================
# DASHBOARD
# ==========================================
@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    total_courses = Course.query.count()
    total_examinations = Examination.query.count()
    total_examiners = User.query.filter_by(role='examiner').count()
    pending_examiners = User.query.filter_by(role='examiner', status='pending').count()
    total_students = User.query.filter_by(role='student').count()
    total_slots = ExaminationSlot.query.count()
    total_bookings = Booking.query.count()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(6).all()
    recent_examinations = Examination.query.order_by(Examination.exam_id.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_courses=total_courses,
        total_examinations=total_examinations,
        total_examiners=total_examiners,
        pending_examiners=pending_examiners,
        total_students=total_students,
        total_slots=total_slots,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings,
        recent_examinations=recent_examinations
    )


# ==========================================
# COURSE MANAGEMENT
# ==========================================
@admin_bp.route('/courses')
def courses():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Course.query
    if search_query:
        query = query.filter(
            or_(
                Course.course_code.ilike(f'%{search_query}%'),
                Course.course_name.ilike(f'%{search_query}%'),
                Course.description.ilike(f'%{search_query}%')
            )
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    course_list = query.order_by(Course.course_code).all()
    return render_template('admin/courses.html', courses=course_list, search_query=search_query, status_filter=status_filter)


@admin_bp.route('/courses/new', methods=['GET', 'POST'])
def new_course():
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip().upper()
        name = request.form.get('course_name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'active')

        if not code or not name:
            flash('Course Code and Course Name are required.', 'danger')
            return render_template('admin/course_form.html', code=code, name=name, description=description, status=status)

        existing = Course.query.filter_by(course_code=code).first()
        if existing:
            flash(f'Course code "{code}" already exists.', 'danger')
            return render_template('admin/course_form.html', code=code, name=name, description=description, status=status)

        course = Course(course_code=code, course_name=name, description=description, status=status)
        db.session.add(course)
        db.session.commit()
        flash(f'Course "{name}" created successfully.', 'success')
        return redirect(url_for('admin.courses'))

    return render_template('admin/course_form.html', is_edit=False)


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip().upper()
        name = request.form.get('course_name', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'active')

        if not code or not name:
            flash('Course Code and Course Name are required.', 'danger')
            return render_template('admin/course_form.html', course=course, is_edit=True)

        existing = Course.query.filter(Course.course_code == code, Course.course_id != course_id).first()
        if existing:
            flash(f'Course code "{code}" is already in use by another course.', 'danger')
            return render_template('admin/course_form.html', course=course, is_edit=True)

        course.course_code = code
        course.course_name = name
        course.description = description
        course.status = status
        db.session.commit()
        flash(f'Course "{name}" updated successfully.', 'success')
        return redirect(url_for('admin.courses'))

    return render_template('admin/course_form.html', course=course, is_edit=True)


@admin_bp.route('/courses/<int:course_id>/toggle-status', methods=['POST'])
def toggle_course_status(course_id):
    course = Course.query.get_or_404(course_id)
    course.status = 'inactive' if course.status == 'active' else 'active'
    db.session.commit()
    flash(f'Course "{course.course_name}" status set to {course.status}.', 'info')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    name = course.course_name
    db.session.delete(course)
    db.session.commit()
    flash(f'Course "{name}" and its associated records have been deleted.', 'success')
    return redirect(url_for('admin.courses'))


# ==========================================
# EXAMINATION MANAGEMENT
# ==========================================
@admin_bp.route('/examinations')
def examinations():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    type_filter = request.args.get('type', '').strip()

    query = Examination.query
    if search_query:
        query = query.filter(
            or_(
                Examination.examination_name.ilike(f'%{search_query}%'),
                Examination.course.has(Course.course_name.ilike(f'%{search_query}%')),
                Examination.course.has(Course.course_code.ilike(f'%{search_query}%'))
            )
        )
    if status_filter:
        query = query.filter_by(status=status_filter)
    if type_filter:
        query = query.filter_by(examination_type=type_filter)

    exam_list = query.order_by(Examination.exam_id.desc()).all()
    return render_template('admin/examinations.html', examinations=exam_list, search_query=search_query, status_filter=status_filter, type_filter=type_filter)


@admin_bp.route('/examinations/new', methods=['GET', 'POST'])
def new_examination():
    courses = Course.query.filter_by(status='active').order_by(Course.course_code).all()
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        name = request.form.get('examination_name', '').strip()
        exam_type = request.form.get('examination_type', 'Viva')
        duration = request.form.get('duration', 30)
        maximum_marks = request.form.get('maximum_marks', 100.0)
        slot_creation_start_str = request.form.get('slot_creation_start')
        slot_creation_end_str = request.form.get('slot_creation_end')
        slot_booking_start_str = request.form.get('slot_booking_start')
        slot_booking_end_str = request.form.get('slot_booking_end')
        status = request.form.get('status', 'Draft')

        # Validation
        errors = []
        if not course_id:
            errors.append('Please select a course.')
        if not name:
            errors.append('Examination name is required.')

        try:
            duration = int(duration)
            if duration <= 0:
                errors.append('Duration must be a positive integer.')
        except ValueError:
            errors.append('Duration must be a valid number.')

        try:
            maximum_marks = float(maximum_marks)
            if maximum_marks <= 0:
                errors.append('Maximum marks must be greater than 0.')
        except ValueError:
            errors.append('Maximum marks must be a valid number.')

        slot_creation_start = None
        slot_creation_end = None
        slot_booking_start = None
        slot_booking_end = None

        try:
            slot_creation_start = datetime.strptime(slot_creation_start_str, '%Y-%m-%dT%H:%M')
            slot_creation_end = datetime.strptime(slot_creation_end_str, '%Y-%m-%dT%H:%M')
            slot_booking_start = datetime.strptime(slot_booking_start_str, '%Y-%m-%dT%H:%M')
            slot_booking_end = datetime.strptime(slot_booking_end_str, '%Y-%m-%dT%H:%M')

            if slot_creation_end <= slot_creation_start:
                errors.append('Slot creation end time must be after slot creation start time.')
            if slot_booking_end <= slot_booking_start:
                errors.append('Slot booking end time must be after slot booking start time.')
        except (ValueError, TypeError):
            errors.append('All timeline dates and times must be properly formatted.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/examination_form.html', courses=courses, is_edit=False)

        exam = Examination(
            course_id=course_id,
            examination_name=name,
            examination_type=exam_type,
            duration=duration,
            maximum_marks=maximum_marks,
            slot_creation_start=slot_creation_start,
            slot_creation_end=slot_creation_end,
            slot_booking_start=slot_booking_start,
            slot_booking_end=slot_booking_end,
            status=status
        )
        db.session.add(exam)
        db.session.commit()
        flash(f'Examination "{name}" created successfully.', 'success')
        return redirect(url_for('admin.examination_detail', exam_id=exam.exam_id))

    return render_template('admin/examination_form.html', courses=courses, is_edit=False)


@admin_bp.route('/examinations/<int:exam_id>')
def examination_detail(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    rubrics = Rubric.query.filter_by(examination_id=exam_id).all()
    slots = ExaminationSlot.query.filter_by(examination_id=exam_id).order_by(ExaminationSlot.date, ExaminationSlot.start_time).all()
    examiners = User.query.filter_by(role='examiner', status='active').all()
    return render_template('admin/examination_detail.html', exam=exam, rubrics=rubrics, slots=slots, examiners=examiners)


@admin_bp.route('/examinations/<int:exam_id>/edit', methods=['GET', 'POST'])
def edit_examination(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    courses = Course.query.filter_by(status='active').order_by(Course.course_code).all()

    if request.method == 'POST':
        course_id = request.form.get('course_id')
        name = request.form.get('examination_name', '').strip()
        exam_type = request.form.get('examination_type', 'Viva')
        duration = request.form.get('duration', 30)
        maximum_marks = request.form.get('maximum_marks', 100.0)
        slot_creation_start_str = request.form.get('slot_creation_start')
        slot_creation_end_str = request.form.get('slot_creation_end')
        slot_booking_start_str = request.form.get('slot_booking_start')
        slot_booking_end_str = request.form.get('slot_booking_end')
        status = request.form.get('status', 'Draft')

        errors = []
        if not course_id:
            errors.append('Please select a course.')
        if not name:
            errors.append('Examination name is required.')

        try:
            duration = int(duration)
            if duration <= 0:
                errors.append('Duration must be a positive integer.')
        except ValueError:
            errors.append('Duration must be a valid number.')

        try:
            maximum_marks = float(maximum_marks)
            if maximum_marks <= 0:
                errors.append('Maximum marks must be greater than 0.')
        except ValueError:
            errors.append('Maximum marks must be a valid number.')

        try:
            slot_creation_start = datetime.strptime(slot_creation_start_str, '%Y-%m-%dT%H:%M')
            slot_creation_end = datetime.strptime(slot_creation_end_str, '%Y-%m-%dT%H:%M')
            slot_booking_start = datetime.strptime(slot_booking_start_str, '%Y-%m-%dT%H:%M')
            slot_booking_end = datetime.strptime(slot_booking_end_str, '%Y-%m-%dT%H:%M')

            if slot_creation_end <= slot_creation_start:
                errors.append('Slot creation end time must be after slot creation start time.')
            if slot_booking_end <= slot_booking_start:
                errors.append('Slot booking end time must be after slot booking start time.')
        except (ValueError, TypeError):
            errors.append('All timeline dates and times must be properly formatted.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/examination_form.html', exam=exam, courses=courses, is_edit=True)

        exam.course_id = course_id
        exam.examination_name = name
        exam.examination_type = exam_type
        exam.duration = duration
        exam.maximum_marks = maximum_marks
        exam.slot_creation_start = slot_creation_start
        exam.slot_creation_end = slot_creation_end
        exam.slot_booking_start = slot_booking_start
        exam.slot_booking_end = slot_booking_end
        exam.status = status
        db.session.commit()
        flash(f'Examination "{name}" updated successfully.', 'success')
        return redirect(url_for('admin.examination_detail', exam_id=exam.exam_id))

    return render_template('admin/examination_form.html', exam=exam, courses=courses, is_edit=True)


@admin_bp.route('/examinations/<int:exam_id>/status', methods=['POST'])
def update_examination_status(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    new_status = request.form.get('status')
    if new_status in ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed']:
        exam.status = new_status
        db.session.commit()
        flash(f'Examination status changed to "{new_status}".', 'success')
    else:
        flash('Invalid status supplied.', 'danger')
    return redirect(url_for('admin.examination_detail', exam_id=exam.exam_id))


@admin_bp.route('/examinations/<int:exam_id>/delete', methods=['POST'])
def delete_examination(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    name = exam.examination_name
    db.session.delete(exam)
    db.session.commit()
    flash(f'Examination "{name}" has been deleted.', 'success')
    return redirect(url_for('admin.examinations'))


# ==========================================
# RUBRIC MANAGEMENT
# ==========================================
@admin_bp.route('/examinations/<int:exam_id>/rubrics/new', methods=['GET', 'POST'])
def new_rubric(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    if request.method == 'POST':
        criterion_name = request.form.get('criterion_name', '').strip()
        maximum_marks = request.form.get('maximum_marks')
        weightage = request.form.get('weightage', 100.0)
        description = request.form.get('description', '').strip()

        errors = []
        if not criterion_name:
            errors.append('Criterion name is required.')

        try:
            max_m = float(maximum_marks)
            if max_m <= 0:
                errors.append('Maximum marks must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Maximum marks must be a valid number.')

        try:
            wt = float(weightage)
            if wt < 0:
                errors.append('Weightage cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Weightage must be a valid number.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/rubric_form.html', exam=exam, is_edit=False)

        rubric = Rubric(
            examination_id=exam_id,
            criterion_name=criterion_name,
            maximum_marks=max_m,
            weightage=wt,
            description=description
        )
        db.session.add(rubric)
        db.session.commit()
        flash(f'Rubric criterion "{criterion_name}" added successfully.', 'success')
        return redirect(url_for('admin.examination_detail', exam_id=exam_id))

    return render_template('admin/rubric_form.html', exam=exam, is_edit=False)


@admin_bp.route('/rubrics/<int:rubric_id>/edit', methods=['GET', 'POST'])
def edit_rubric(rubric_id):
    rubric = Rubric.query.get_or_404(rubric_id)
    exam = rubric.examination

    if request.method == 'POST':
        criterion_name = request.form.get('criterion_name', '').strip()
        maximum_marks = request.form.get('maximum_marks')
        weightage = request.form.get('weightage', 100.0)
        description = request.form.get('description', '').strip()

        errors = []
        if not criterion_name:
            errors.append('Criterion name is required.')

        try:
            max_m = float(maximum_marks)
            if max_m <= 0:
                errors.append('Maximum marks must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Maximum marks must be a valid number.')

        try:
            wt = float(weightage)
            if wt < 0:
                errors.append('Weightage cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Weightage must be a valid number.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/rubric_form.html', exam=exam, rubric=rubric, is_edit=True)

        rubric.criterion_name = criterion_name
        rubric.maximum_marks = max_m
        rubric.weightage = wt
        rubric.description = description
        db.session.commit()
        flash(f'Rubric criterion "{criterion_name}" updated successfully.', 'success')
        return redirect(url_for('admin.examination_detail', exam_id=exam.exam_id))

    return render_template('admin/rubric_form.html', exam=exam, rubric=rubric, is_edit=True)


@admin_bp.route('/rubrics/<int:rubric_id>/delete', methods=['POST'])
def delete_rubric(rubric_id):
    rubric = Rubric.query.get_or_404(rubric_id)
    exam_id = rubric.examination_id
    db.session.delete(rubric)
    db.session.commit()
    flash('Rubric criterion deleted successfully.', 'success')
    return redirect(url_for('admin.examination_detail', exam_id=exam_id))


# ==========================================
# EXAMINER MANAGEMENT
# ==========================================
@admin_bp.route('/examiners')
def examiners():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = User.query.filter_by(role='examiner')
    if search_query:
        query = query.filter(
            or_(
                User.name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                User.examiner_profile.has(ExaminerProfile.department.ilike(f'%{search_query}%'))
            )
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    examiner_list = query.order_by(User.id.desc()).all()
    return render_template('admin/examiners.html', examiners=examiner_list, search_query=search_query, status_filter=status_filter)


@admin_bp.route('/examiners/<int:user_id>')
def examiner_detail(user_id):
    examiner = User.query.filter_by(id=user_id, role='examiner').first_or_404()
    slots = ExaminationSlot.query.filter_by(examiner_id=user_id).order_by(ExaminationSlot.date.desc()).all()
    return render_template('admin/examiner_detail.html', examiner=examiner, slots=slots)


@admin_bp.route('/examiners/<int:user_id>/approve', methods=['POST'])
def approve_examiner(user_id):
    examiner = User.query.filter_by(id=user_id, role='examiner').first_or_404()
    examiner.status = 'active'
    if examiner.examiner_profile:
        examiner.examiner_profile.status = 'approved'
    db.session.commit()
    flash(f'Examiner "{examiner.name}" has been approved and can now access the portal.', 'success')
    return redirect(request.referrer or url_for('admin.examiners'))


@admin_bp.route('/examiners/<int:user_id>/toggle-status', methods=['POST'])
def toggle_examiner_status(user_id):
    examiner = User.query.filter_by(id=user_id, role='examiner').first_or_404()
    if examiner.status == 'active':
        examiner.status = 'inactive'
        if examiner.examiner_profile:
            examiner.examiner_profile.status = 'inactive'
        flash(f'Examiner "{examiner.name}" has been deactivated.', 'warning')
    else:
        examiner.status = 'active'
        if examiner.examiner_profile:
            examiner.examiner_profile.status = 'approved'
        flash(f'Examiner "{examiner.name}" has been activated.', 'success')
    db.session.commit()
    return redirect(request.referrer or url_for('admin.examiners'))


# ==========================================
# EXAMINATION SLOT MANAGEMENT & REASSIGNMENT
# ==========================================
@admin_bp.route('/slots')
def slots():
    exam_id = request.args.get('exam_id')
    status_filter = request.args.get('status', '').strip()

    query = ExaminationSlot.query
    if exam_id:
        query = query.filter_by(examination_id=exam_id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    slot_list = query.order_by(ExaminationSlot.date.desc(), ExaminationSlot.start_time.asc()).all()
    examinations = Examination.query.all()
    examiners = User.query.filter_by(role='examiner', status='active').all()

    return render_template('admin/slots.html', slots=slot_list, examinations=examinations, examiners=examiners, selected_exam_id=exam_id, status_filter=status_filter)


@admin_bp.route('/slots/<int:slot_id>/reassign', methods=['POST'])
def reassign_slot(slot_id):
    slot = ExaminationSlot.query.get_or_404(slot_id)
    new_examiner_id = request.form.get('examiner_id')

    new_examiner = User.query.filter_by(id=new_examiner_id, role='examiner', status='active').first()
    if not new_examiner:
        flash('Selected examiner is invalid or inactive.', 'danger')
        return redirect(request.referrer or url_for('admin.slots'))

    old_name = slot.examiner.name if slot.examiner else 'None'
    slot.examiner_id = new_examiner.id
    db.session.commit()
    flash(f'Slot #{slot.slot_id} reassigned from {old_name} to {new_examiner.name}.', 'success')
    return redirect(request.referrer or url_for('admin.slots'))


@admin_bp.route('/slots/<int:slot_id>/cancel', methods=['POST'])
def cancel_slot(slot_id):
    slot = ExaminationSlot.query.get_or_404(slot_id)
    slot.status = 'Cancelled'
    db.session.commit()
    flash(f'Slot #{slot.slot_id} marked as Cancelled.', 'warning')
    return redirect(request.referrer or url_for('admin.slots'))


@admin_bp.route('/slots/<int:slot_id>/status', methods=['POST'])
def update_slot_status(slot_id):
    slot = ExaminationSlot.query.get_or_404(slot_id)
    new_status = request.form.get('status')
    if new_status in ['Available', 'Full', 'Cancelled', 'Completed']:
        slot.status = new_status
        db.session.commit()
        flash(f'Slot #{slot.slot_id} status updated to {new_status}.', 'success')
    return redirect(request.referrer or url_for('admin.slots'))


# ==========================================
# BOOKING MANAGEMENT & RESCHEDULING
# ==========================================
@admin_bp.route('/bookings')
def bookings():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    exam_id = request.args.get('exam_id')

    query = Booking.query
    if search_query:
        query = query.filter(
            or_(
                Booking.student.has(User.name.ilike(f'%{search_query}%')),
                Booking.student.has(User.email.ilike(f'%{search_query}%')),
                Booking.slot.has(ExaminationSlot.examination.has(Examination.examination_name.ilike(f'%{search_query}%')))
            )
        )
    if status_filter:
        query = query.filter_by(status=status_filter)
    if exam_id:
        query = query.filter(Booking.slot.has(ExaminationSlot.examination_id == exam_id))

    booking_list = query.order_by(Booking.booking_date.desc()).all()
    examinations = Examination.query.all()

    return render_template('admin/bookings.html', bookings=booking_list, search_query=search_query, status_filter=status_filter, examinations=examinations, selected_exam_id=exam_id)


@admin_bp.route('/bookings/<int:booking_id>/reschedule', methods=['GET', 'POST'])
def reschedule_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    current_slot = booking.slot
    exam = current_slot.examination

    # Available alternative slots for the same examination
    available_slots = ExaminationSlot.query.filter(
        ExaminationSlot.examination_id == exam.exam_id,
        ExaminationSlot.slot_id != current_slot.slot_id,
        ExaminationSlot.status == 'Available',
        ExaminationSlot.available_seats > 0
    ).all()

    if request.method == 'POST':
        new_slot_id = request.form.get('new_slot_id')
        new_slot = ExaminationSlot.query.get(new_slot_id)

        if not new_slot or new_slot.examination_id != exam.exam_id:
            flash('Invalid target slot selected.', 'danger')
            return render_template('admin/reschedule_booking.html', booking=booking, exam=exam, current_slot=current_slot, available_slots=available_slots)

        if new_slot.available_seats <= 0:
            flash('Target slot is already full.', 'danger')
            return render_template('admin/reschedule_booking.html', booking=booking, exam=exam, current_slot=current_slot, available_slots=available_slots)

        # Move booking
        old_slot = booking.slot
        booking.slot_id = new_slot.slot_id
        booking.status = 'Booked'

        # Recalculate seats for both slots
        old_slot.recalculate_seats()
        new_slot.recalculate_seats()

        db.session.commit()
        flash(f'Booking #{booking.booking_id} for student {booking.student.name} successfully rescheduled to Slot #{new_slot.slot_id} ({new_slot.date} {new_slot.start_time}).', 'success')
        return redirect(url_for('admin.bookings'))

    return render_template('admin/reschedule_booking.html', booking=booking, exam=exam, current_slot=current_slot, available_slots=available_slots)


@admin_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Cancelled'
    booking.slot.recalculate_seats()
    db.session.commit()
    flash(f'Booking #{booking.booking_id} has been cancelled.', 'info')
    return redirect(url_for('admin.bookings'))


# ==========================================
# SERVER-SIDE GLOBAL SEARCH
# ==========================================
@admin_bp.route('/search')
def search():
    query_str = request.args.get('q', '').strip()
    results = {
        'students': [],
        'examiners': [],
        'examinations': [],
        'bookings': []
    }

    if query_str:
        # Students
        results['students'] = User.query.filter(
            User.role == 'student',
            or_(User.name.ilike(f'%{query_str}%'), User.email.ilike(f'%{query_str}%'))
        ).all()

        # Examiners
        results['examiners'] = User.query.filter(
            User.role == 'examiner',
            or_(
                User.name.ilike(f'%{query_str}%'),
                User.email.ilike(f'%{query_str}%'),
                User.examiner_profile.has(ExaminerProfile.department.ilike(f'%{query_str}%'))
            )
        ).all()

        # Examinations
        results['examinations'] = Examination.query.filter(
            or_(
                Examination.examination_name.ilike(f'%{query_str}%'),
                Examination.examination_type.ilike(f'%{query_str}%'),
                Examination.course.has(Course.course_name.ilike(f'%{query_str}%')),
                Examination.course.has(Course.course_code.ilike(f'%{query_str}%'))
            )
        ).all()

        # Bookings
        results['bookings'] = Booking.query.filter(
            or_(
                Booking.student.has(User.name.ilike(f'%{query_str}%')),
                Booking.student.has(User.email.ilike(f'%{query_str}%')),
                Booking.slot.has(ExaminationSlot.examination.has(Examination.examination_name.ilike(f'%{query_str}%')))
            )
        ).all()

    return render_template('admin/search.html', query=query_str, results=results)
