from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SubmitField, DateField,
                     DateTimeField,SelectField, BooleanField, URLField)
from wtforms.validators import (ValidationError, DataRequired,
                                Optional, URL, Length, Email, Regexp)
from ..models import  Reminder, Assignment, Course, User, Role


class AssignmentForm(FlaskForm):
    title = StringField("Title")
    description = TextAreaField("Description", validators=[DataRequired()])
    given_date = DateField("Given Date", validators=[DataRequired()])
    due_date = DateField("Submission Date", validators=[DataRequired()])
    submission_link = URLField("Submission Link", validators=[URL(), Optional()])
    course = SelectField("Course", validators=[DataRequired()], choices=[])
    priority = SelectField("Priority", choices=[
                                        ("low", "Low"),
                                        ("medium", "Medium"),
                                        ("high", "High")], validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        self.course.choices = [("", "--Select a Course--")] + [
            (course.course_code, course.title) for course in Course.query.all()
        ]
    button = SubmitField("Submit")

    def validate_title(self, field):
        if Reminder.query.filter_by(title=field.data, user=current_user).first():
            raise ValidationError("Already Created A Reminder for this task")


class ReminderForm(FlaskForm):
    title = StringField("Title")
    description = TextAreaField("Description", validators=[DataRequired()])
    due_date = DateField("Due Date", validators=[DataRequired()])
    notification_time = DateTimeField("Notification Time (Optional)",
                                      format="%Y-%m-%d %H:%M:%S", validators=[Optional()])
    assignment_id = SelectField("Link to Assignment (Optional)", validators=[Optional()], choices=[])
    recurring = BooleanField("Repeat Reminder")

    button = SubmitField("Create Reminder")

    def __init__(self, *args, **kwargs):
        super(ReminderForm, self).__init__(*args, **kwargs)
        self.assignment_id.choices = [("", "--No Assignment--")] + [
            (str(assignment.id), assignment.title) for assignment in
            Assignment.query.filter_by(user_id=current_user.id).all()
        ]

    def validate_title(self, field):
        if Reminder.query.filter_by(title=field.data, user=current_user).first():
            raise ValidationError("Already Created A Reminder for this task")

class EditAssignmentForm(FlaskForm):
    title = StringField("Title")
    description = TextAreaField("Description", validators=[DataRequired()])
    due_date = DateField("Submission Date", validators=[DataRequired()])
    course = SelectField("Course", validators=[DataRequired()], choices=[])
    submission_link = StringField("Submission Link (Optional)", validators=[Optional(), URL()])
    status = SelectField("Status", validators=[DataRequired()],
                         choices=[("pending", "Pending"),
                                  ("completed", "Completed"),
                                  ("overdue", "Overdue")])
    button = SubmitField("Submit")

    def __init__(self, *args, **kwargs):
        super(EditAssignmentForm, self).__init__(*args, **kwargs)
        self.course.choices = [("", "--Select a Course--")] + [
            (course.course_code, course.title) for course in Course.query.all()]

class EditReminderForm(FlaskForm):
    title = StringField("Title")
    description = TextAreaField("Description", validators=[DataRequired()])
    due_date = DateField("Due Date", validators=[DataRequired()])
    disabled = BooleanField("Disable")
    notification_time = DateTimeField("Notification Time (Optional)",
                                      format="%Y-%m-%d %H:%M:%S", validators=[Optional()])
    assignment_id = SelectField("Link to Assignment (Optional)", validators=[Optional()], choices=[])
    recurring = BooleanField("Repeat Reminder")

    button = SubmitField("Edit")

    def __init__(self, reminder, *args, **kwargs):
        super(EditReminderForm, self).__init__(*args, **kwargs)
        self.assignment_id.choices = [("", "--No Assignment--")] + [
            (str(assignment.id), assignment.title) for assignment in
            Assignment.query.filter_by(user_id=current_user.id).all()
        ]
        self.reminder = reminder

    def validate_title(self, field):
        if field.data != self.reminder.title and Reminder.query.filter_by(title=field.data, user=current_user).first():
            raise ValidationError("Already Created A Reminder for this task")


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')