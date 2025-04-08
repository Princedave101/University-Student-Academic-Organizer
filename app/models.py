import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from . import db, login_manager


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(16), nullable=False, index=True)
    title = db.Column(db.Text, nullable=False, unique=True)
    assignments = db.relationship("Assignment", backref="course", lazy='dynamic')

    @staticmethod
    def insert_courses():
        courses={"csc410":"Database Management",
                 "csc411":"Statistical Processing",
                 "csc412":"Numerical analysis",
                 "csc413":"Discrete Mathematics",
                 "csc414":"",
                 "csc415":"",
                 "csc416":"Project Management",
                 "csc417":"Data Processing",
                 "csc418":"Simulation and Modelling",
                 "csc419": "Software Engineering",
                 "csc434":"Web Programming",
                 "csc436":"", "csc437":""
                 }

        for c in courses:
            course = Course.query.filter_by(course_code=c).first()
            if course is None and len(courses[c]) !=0:
                course = Course(course_code=c, title=courses[c])
                db.session.add(course)
        db.session.commit()


    def __repr__(self):
        return "<Course {} >".format(self.course_code)



class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    given_date = db.Column(db.Date, nullable=False, default=datetime.date)
    due_date = db.Column(db.Date, nullable=False, default=datetime.date)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, overdue
    submission_link = db.Column(db.String(512), nullable=True)
    priority = db.Column(db.String(10), nullable=False, default='medium')
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    reminder = db.relationship("Reminder", backref="assignment", uselist=False)

    def __repr__(self):
        return "<Assignment {} - Ends {}>".format(self.title, self.due_date)


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=False, default=datetime.date)
    notification_time = db.Column(db.DateTime, nullable=True)
    recurring = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, nullable=False, default=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return "<Reminder {} - Ends {}>".format(self.title, self.due_date)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')


    @staticmethod
    def insert_roles():
        roles = [
            'Student',
            'Administrator']

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.now)
    last_seen = db.Column(db.DateTime(), default=datetime.now)
    avatar_hash = db.Column(db.String(32))
    assignments = db.relationship("Assignment", backref="user", lazy='dynamic')
    reminders = db.relationship("Reminder", backref="user", lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['APP_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
                self.confirmed=True
            else:
                self.role = Role.query.filter_by(name='Student').first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})

    def confirm(self, token, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'), max_age=expiration)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})

    @staticmethod
    def reset_password(token, new_password, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'), max_age=expiration)
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email})

    def change_email(self, token, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'), max_age=expiration)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def ping(self):
        self.last_seen = datetime.now()
        db.session.add(self)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def is_admin(self):
        return self.role.name == 'Administrator'

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
