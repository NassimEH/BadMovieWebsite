from flask import Blueprint, render_template

movie_bp = Blueprint('movies', __name__, url_prefix='/movies')


@movie_bp.route('/')
def list_movies():
    """Page listant tous les films avec recherche et filtres."""
    return render_template('movies_list.html')
