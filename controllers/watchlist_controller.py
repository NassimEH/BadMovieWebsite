"""Contrôleur pour la gestion de la watchlist."""
from models import Commentaire, Film
from extensions import db


class WatchlistController:
    """Contrôleur pour les opérations sur la watchlist."""
    
    @staticmethod
    def get_user_watchlist(user_id):
        """Récupère la watchlist d'un utilisateur."""
        return Commentaire.query.filter_by(ID_user=user_id).all()
    
    @staticmethod
    def add_to_watchlist(user_id, movie_id):
        """Ajoute un film à la watchlist."""
        commentaire = Commentaire.query.filter_by(
            ID_user=user_id, 
            ID_film=movie_id
        ).first()
        
        if commentaire:
            commentaire.watched = False
        else:
            commentaire = Commentaire(
                ID_user=user_id,
                ID_film=movie_id,
                watched=False
            )
            db.session.add(commentaire)
        
        db.session.commit()
        return commentaire
    
    @staticmethod
    def mark_as_watched(user_id, movie_id):
        """Marque un film comme vu."""
        commentaire = Commentaire.query.filter_by(
            ID_user=user_id,
            ID_film=movie_id
        ).first_or_404()
        
        commentaire.watched = True
        db.session.commit()
        return commentaire
    
    @staticmethod
    def remove_from_watchlist(user_id, movie_id):
        """Retire un film de la watchlist."""
        commentaire = Commentaire.query.filter_by(
            ID_user=user_id,
            ID_film=movie_id
        ).first_or_404()
        
        db.session.delete(commentaire)
        db.session.commit()

