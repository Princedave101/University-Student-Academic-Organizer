from flask import render_template, flash, redirect, url_for, abort, request, current_app
from flask_login import login_required, current_user
from .. import db
from ..models import Assignment, Reminder, Course, User, Role
from . import main
from .forms import (AssignmentForm, ReminderForm, EditReminderForm,
                    EditAssignmentForm, EditProfileForm, EditProfileAdminForm)
from ..utils import  send_email


@main.route("/")
@login_required
def index():
    return render_template('index.html', name="david")

@login_required
@main.route("/user/<string:username>")
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user != user and not current_user.is_admin():
        abort(403)
    return render_template("profile.html", user=user)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile_admin(id):
    if not current_user._get_current_object().is_admin():
        abort(403)
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route("/reminders")
@login_required
def reminders():
    page = request.args.get('page', 1, type=int)
    pagination = Reminder.query.filter_by(user=current_user).order_by(Reminder.due_date).paginate(
        page=page, per_page=current_app.config['CARDS_PER_PAGE'],
        error_out=False)
    reminders= pagination.items
    return render_template("reminder.html", pagination=pagination, reminders=reminders)

@main.route("/assignments")
@login_required
def assignments():
    page = request.args.get('page', 1, type=int)
    pagination = Assignment.query.filter_by(user=current_user).order_by(Assignment.due_date).paginate(
        page=page, per_page=current_app.config['CARDS_PER_PAGE'],
        error_out=False)
    assignments = pagination.items
    return render_template("assignment.html", pagination=pagination, assignments=assignments)

@main.route("/reminder/<int:id>")
@login_required
def reminder(id):
    reminder = Reminder.query.get_or_404(id)
    return render_template("reminder.html", reminders=[reminder])

@main.route("/assignment/<int:id>")
@login_required
def assignment(id):
    assignment = Assignment.query.get_or_404(id)
    return render_template("assignment.html", assignments=[assignment])

@main.route("/edit-reminder/<int:id>", methods=["GET", "POST"])
@login_required
def edit_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    if current_user != reminder.user:
        abort(403)
    form = EditReminderForm(reminder=reminder)
    if form.validate_on_submit():
        reminder.title=form.title.data
        reminder.description=form.description.data
        reminder.due_date=form.due_date.data
        reminder.disabled=form.disabled.data
        reminder.notification_time=form.notification_time.data
        reminder.recurring=form.recurring.data
        reminder.assignment_id=int(form.assignment_id.data)
        db.session.add(reminder)
        db.session.commit()
        flash("Edit Successfully", 'success')
        return redirect(url_for("main.reminders"))
    form.title.data = reminder.title
    form.description.data = reminder.description
    form.due_date.data = reminder.due_date
    form.disabled.data = reminder.disabled
    form.notification_time.data = reminder.notification_time
    form.recurring.data = reminder.recurring
    form.assignment_id.data = str(reminder.assignment_id)
    return render_template("edit_reminder.html", form=form)

@main.route("/edit-assignment/<int:id>", methods=["GET", "POST"])
@login_required
def edit_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if current_user != assignment.user:
        abort(403)
    form = EditAssignmentForm()
    if form.validate_on_submit():
        assignment.title=form.title.data
        assignment.description=form.description.data
        assignment.due_date=form.due_date.data
        assignment.course=Course.query.filter_by(course_code=form.course.data.lower()).first()
        assignment.submission_link = form.submission_link.data
        assignment.status = form.status.data.lower()
        flash("Edit Successfully", 'success')
        return redirect(url_for("main.reminders"))
    form.title.data = assignment.title
    form.description.data = assignment.description
    form.due_date.data = assignment.due_date
    form.course.data = assignment.course.course_code
    form.submission_link.data = assignment.submission_link
    form.status.data = assignment.submission_link
    return render_template("edit_assignment.html", form=form)

@main.route("/delete-reminder/<int:id>")
@login_required
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    if current_user != reminder.user:
        abort(403)
    db.session.delete(reminder)
    db.session.commit()
    send_email(current_user.email, 'Reminder Deletion',
               'mail/delete_reminder', user=current_user, reminder=reminder)
    flash("Deletion Successful", 'success')
    return redirect(url_for("main.reminders"))

@main.route("/delete-assignment/<int:id>")
@login_required
def delete_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if current_user != assignment.user:
        abort(403)
    reminder = Reminder.query.filter_by(assignment=assignment).first()
    if reminder:
        db.session.delete(reminder)
    db.session.delete(assignment)
    db.session.commit()
    send_email(current_user.email, 'Assignment Deletion',
               'mail/delete_assignment', user=current_user, assignment=assignment)
    flash("Deletion Successful", 'success')
    return redirect(url_for("main.assignments"))

@main.route("/set-reminder", methods=["GET", "POST"])
@login_required
def set_reminder():
    form = ReminderForm()
    if form.validate_on_submit():
        reminder= Reminder(
            title=form.title.data,
            description=form.description.data,
            due_date = form.due_date.data,
            notification_time=form.notification_time.data,
            recurring=form.recurring.data,
            assignment=Assignment.query.get(form.assignment_id.data),
            user = current_user._get_current_object()
        )
        db.session.add(reminder)
        db.session.commit()
        flash("Reminder created Successfully", "success")
        send_email(current_user.email, 'Reminder Created',
                   'mail/create_reminder', user=current_user, reminder=reminder)
        return redirect(url_for('main.reminders'))
    return render_template("set_reminder.html", form=form)

@main.route("/create-assignment", methods=["GET", "POST"])
@login_required
def create_assignment():
    form = AssignmentForm()
    if form.validate_on_submit():
        course = Course.query.filter_by(course_code=form.course.data).first_or_404()
        if course:
            assignment = Assignment(
                title=form.title.data,
                description=form.description.data,
                given_date=form.given_date.data,
                due_date=form.due_date.data,
                submission_link=form.submission_link.data,
                priority=form.priority.data,
                user=current_user._get_current_object(),
                course=course
            )
            reminder = Reminder(
                title=f'{course.course_code}-{form.title.data} Assignment',
                description=form.description.data,
                due_date=form.due_date.data,
                recurring=True,
                assignment=assignment,
                user=current_user._get_current_object()
            )
            db.session.add_all([assignment, reminder])
            db.session.commit()
            flash("Assignment created Successfully", "success")
            send_email(current_user.email, 'Assignment created',
                       'mail/create_assignment', user=current_user, assignment=assignment)
        return redirect(url_for('main.assignments'))
    return render_template("create_assignment.html", form=form)