from threading import Thread
from functools import wraps
from flask import current_app, render_template, flash, url_for, redirect
from flask_mail import Message
from flask_login import current_user
from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    msg = Message(current_app.config['APP_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=current_app.config['APP_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[current_app, msg])
    thr.start()
    return thr

def logout_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated or not current_user.is_anonymous:
            flash("You are already authenticated.", "info")
            return redirect(url_for("main.index"))
        return func(*args, **kwargs)

    return decorated_function