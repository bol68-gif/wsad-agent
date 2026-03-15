from flask import Blueprint
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login_page():
    return "Login page — coming Night 1 coding"

@auth_bp.route("/logout")
def logout():
    return "Logout — coming Night 1 coding"
