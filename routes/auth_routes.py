from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    return "Login page placeholder"
