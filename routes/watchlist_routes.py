from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from controllers.watchlist_controller import WatchlistController

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/watchlist')

@watchlist_bp.route('/')
@login_required
def show_watchlist():
    """Affiche la watchlist."""
    watchlist = WatchlistController.get_user_watchlist(current_user.ID_user)
    return render_template('watchlist.html', watchlist=watchlist)

@watchlist_bp.route('/add', methods=['POST'])
@login_required
def add_to_watchlist():
    """API pour ajouter un film."""
    data = request.get_json()
    success = WatchlistController.add_to_watchlist(current_user.ID_user, data)
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Erreur lors de l'ajout"}), 400
    
@watchlist_bp.route('/watched', methods=['POST'])
@login_required
def set_watched():
    data = request.get_json()
    # data contient les infos du film + 'watched' (true/false)
    status = data.get('watched', False)
    success = WatchlistController.update_watched(current_user.ID_user, data, status)
    return jsonify({"success": success})

@watchlist_bp.route('/rate', methods=['POST'])
@login_required
def rate_movie():
    data = request.get_json()
    # data contient les infos du film + 'score' (int)
    score = data.get('score')
    success = WatchlistController.update_score(current_user.ID_user, data, score)
    return jsonify({"success": success})