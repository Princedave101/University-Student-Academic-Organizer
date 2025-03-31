from flask import render_template, flash
from . import main

@main.route("/")
def index():
    return render_template('index.html', name="David")

@main.route("/user/<string:username>")
def user(username):
    return "<h1>Hello, Welcome To {} Profile</h1>".format(username)
