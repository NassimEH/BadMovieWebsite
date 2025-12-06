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
    
    if success:
        # Récupérer l'état mis à jour pour le retourner
        from models import Commentaire
        try:
            tmdb_id = int(data.get('tmdb_id'))
            interaction = Commentaire.query.filter_by(
                ID_user=current_user.ID_user,
                ID_film=tmdb_id
            ).first()
            
            return jsonify({
                "success": True,
                "watched": interaction.watched if interaction else False,
                "score": interaction.score_user if interaction else None
            })
        except (ValueError, TypeError):
            return jsonify({"success": True, "watched": True, "score": score})
    else:
        return jsonify({"success": False})

@watchlist_bp.route('/review', methods=['POST'])
@login_required
def save_review():
    """API pour sauvegarder une critique."""
    data = request.get_json()
    review_text = data.get('review', '').strip()
    
    # Si la critique est vide, on la supprime
    if not review_text:
        review_text = None
    
    success = WatchlistController.update_review(current_user.ID_user, data, review_text)
    
    if success:
        return jsonify({"success": True, "review": review_text})
    else:
        return jsonify({"success": False, "message": "Erreur lors de la sauvegarde"}), 400

@watchlist_bp.route('/remove', methods=['POST', 'DELETE'])
@login_required
def remove_from_watchlist():
    """API pour retirer un film de la watchlist."""
    data = request.get_json()
    success = WatchlistController.remove_from_watchlist(current_user.ID_user, data)
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Erreur lors de la suppression"}), 400

@watchlist_bp.route('/api/filtered')
@login_required
def get_filtered_watchlist():
    """API pour récupérer la watchlist filtrée et triée."""
    filter_status = request.args.get('status', 'all')  # 'all', 'watched', 'towatch'
    sort_by = request.args.get('sort', 'date')  # 'date', 'rating-asc', 'rating-desc', 'title-asc', 'title-desc'
    
    watchlist = WatchlistController.get_user_watchlist(current_user.ID_user)
    
    # Filtrer par statut
    filtered = []
    for item in watchlist:
        if filter_status == 'all':
            filtered.append(item)
        elif filter_status == 'watched' and item.watched:
            filtered.append(item)
        elif filter_status == 'towatch' and not item.watched:
            filtered.append(item)
    
    # Trier
    if sort_by == 'rating-asc':
        # Trier par note croissante, les films sans note en dernier
        filtered.sort(key=lambda x: (x.score_user if x.score_user is not None else 999, x.film.name_movie.lower()))
    elif sort_by == 'rating-desc':
        # Trier par note décroissante, les films sans note en dernier
        filtered.sort(key=lambda x: (x.score_user if x.score_user is not None else -1, x.film.name_movie.lower()), reverse=True)
    elif sort_by == 'title-asc':
        filtered.sort(key=lambda x: x.film.name_movie.lower())
    elif sort_by == 'title-desc':
        filtered.sort(key=lambda x: x.film.name_movie.lower(), reverse=True)
    # 'date' est le tri par défaut (ordre d'ajout, pas de tri supplémentaire)
    
    # Formater les résultats
    formatted = []
    for item in filtered:
        year = None
        if item.film.year_movie:
            year = item.film.year_movie.year if hasattr(item.film.year_movie, 'year') else str(item.film.year_movie)[:4]
        
        duration = None
        if item.film.duration:
            if hasattr(item.film.duration, 'hour') and hasattr(item.film.duration, 'minute'):
                total_minutes = item.film.duration.hour * 60 + item.film.duration.minute
                duration = f"{total_minutes} min"
            else:
                duration = str(item.film.duration)
        
        formatted.append({
            "id": item.film.ID_film,
            "tmdb_id": item.film.ID_film,
            "title": item.film.name_movie,
            "image": item.film.image or "",
            "year": year,
            "duration": duration,
            "category": item.film.category or "",
            "watched": item.watched,
            "score": item.score_user,
            "review": item.avis_user or "",
        })
    
    return jsonify({"movies": formatted})