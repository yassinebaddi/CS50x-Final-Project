from flask import redirect, render_template, session
from functools import wraps

def error(feedback_message, code):
    def format_message(feedback_message):
        replacements = [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"), ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]
        for old, new in replacements:
            feedback_message = feedback_message.replace(old, new)
        return feedback_message
    return render_template("error.html", top=code, bottom=format_message(feedback_message)), code

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper
