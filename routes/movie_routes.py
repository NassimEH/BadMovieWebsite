from flask import Blueprint

movie_bp = Blueprint('movies', __name__, url_prefix='/movies')


@movie_bp.route('/')
def list_movies():
    return "Movies list placeholder"
