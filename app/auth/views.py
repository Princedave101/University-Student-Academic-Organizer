from . import auth

@auth.route("/login")
def login():
    return "<h1>Hello, Login now</h1>"

@auth.route("/register")
def register():
    return "<h1>Hello, Register now</h1>"

