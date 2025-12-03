from models import Commentaire, Film
from extensions import db
from datetime import datetime, time

class WatchlistController:
    
    @staticmethod
    def get_user_watchlist(user_id):
        return Commentaire.query.filter_by(ID_user=user_id).all()

    @staticmethod
    def _get_or_create_film(movie_data):
        # ... (Votre code existant pour créer le film) ...
        try:
            tmdb_id = int(movie_data.get('tmdb_id'))
        except (ValueError, TypeError):
            return None

        film = Film.query.get(tmdb_id)
        if not film:
            # Conversion et création (comme avant)
            release_date = movie_data.get('release_date')
            date_obj = None
            if release_date:
                try:
                    date_obj = datetime.strptime(release_date, '%Y-%m-%d').date()
                except ValueError:
                    date_obj = None
            
            runtime = movie_data.get('runtime')
            duration_obj = None
            if runtime and str(runtime).isdigit():
                minutes = int(runtime)
                duration_obj = time(hour=minutes // 60, minute=minutes % 60)

            film = Film(
                ID_film=tmdb_id,
                name_movie=movie_data.get('title', 'Inconnu'),
                image=movie_data.get('image'),
                year_movie=date_obj,
                duration=duration_obj,
                category=movie_data.get('category', 'Autre')
            )
            db.session.add(film)
            db.session.commit()
        return film

    @staticmethod
    def add_to_watchlist(user_id, movie_data):
        film = WatchlistController._get_or_create_film(movie_data)
        if not film: return False
        
        commentaire = Commentaire.query.filter_by(ID_user=user_id, ID_film=film.ID_film).first()
        if not commentaire:
            commentaire = Commentaire(ID_user=user_id, ID_film=film.ID_film, watched=False)
            db.session.add(commentaire)
            db.session.commit()
        return True

    @staticmethod
    def update_watched(user_id, movie_data, watched_status):
        """Met à jour le statut 'vu' (boolean)."""
        film = WatchlistController._get_or_create_film(movie_data)
        if not film: return False

        commentaire = Commentaire.query.filter_by(ID_user=user_id, ID_film=film.ID_film).first()
        if not commentaire:
            commentaire = Commentaire(ID_user=user_id, ID_film=film.ID_film, watched=watched_status)
            db.session.add(commentaire)
        else:
            commentaire.watched = watched_status
        
        db.session.commit()
        return True

    @staticmethod
    def update_score(user_id, movie_data, score):
        """Met à jour la note (entier)."""
        film = WatchlistController._get_or_create_film(movie_data)
        if not film: return False

        commentaire = Commentaire.query.filter_by(ID_user=user_id, ID_film=film.ID_film).first()
        if not commentaire:
            # Si on note un film pas encore dans la liste, on l'ajoute
            commentaire = Commentaire(ID_user=user_id, ID_film=film.ID_film, score_user=score, watched=True) # On suppose que si on note, on a vu
            db.session.add(commentaire)
        else:
            commentaire.score_user = score
        
        db.session.commit()
        return True