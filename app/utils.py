from threading import Thread
from functools import wraps
from flask import current_app, render_template, flash, url_for, redirect, abort
from flask_mail import Message
from flask_login import current_user
from . import mail


def send_async_email(app, msg):
    try:
        with app.app_context():
            mail.send(msg)
    except Exception as e:
        print(f"{e}")


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['APP_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

#
# def admin_required(f):
#     return permission_required(Permission.ADMIN)(f)


def logout_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated or not current_user.is_anonymous:
            flash("You are already authenticated.", "info")
            return redirect(url_for("main.index"))
        return func(*args, **kwargs)

    return decorated_function



