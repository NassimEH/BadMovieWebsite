from flask import Blueprint

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/watchlist')


@watchlist_bp.route('/')
def show_watchlist():
    return "Watchlist placeholder"
