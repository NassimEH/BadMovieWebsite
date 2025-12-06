from models import Commentaire, Film
from extensions import db
from datetime import datetime, time

class WatchlistController:
    
    @staticmethod
    def get_user_watchlist(user_id):
        return Commentaire.query.filter_by(ID_user=user_id).all()

    @staticmethod
    def _get_or_create_film(movie_data):
        """Récupère un film existant ou en crée un nouveau. Met à jour l'image si elle est manquante."""
        try:
            tmdb_id = int(movie_data.get('tmdb_id'))
        except (ValueError, TypeError):
            return None

        film = Film.query.get(tmdb_id)
        if not film:
            # Conversion et création
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

            # Récupération de l'image avec gestion des URLs complètes
            image_url = movie_data.get('image', '')
            if image_url and not image_url.startswith('http'):
                # Si l'URL n'est pas complète, on essaie de la compléter
                if image_url.startswith('/'):
                    image_url = 'https://image.tmdb.org' + image_url
                elif not image_url.startswith('https://'):
                    image_url = 'https://image.tmdb.org/t/p/w500' + image_url
            
            film = Film(
                ID_film=tmdb_id,
                name_movie=movie_data.get('title', 'Inconnu'),
                image=image_url,
                year_movie=date_obj,
                duration=duration_obj,
                category=movie_data.get('category', 'Autre')
            )
            db.session.add(film)
            db.session.commit()
        else:
            # Si le film existe mais n'a pas d'image, on la met à jour
            image_url = movie_data.get('image', '')
            if image_url and not image_url.startswith('http'):
                # Si l'URL n'est pas complète, on essaie de la compléter
                if image_url.startswith('/'):
                    image_url = 'https://image.tmdb.org' + image_url
                elif not image_url.startswith('https://'):
                    image_url = 'https://image.tmdb.org/t/p/w500' + image_url
            
            if not film.image and image_url:
                film.image = image_url
                db.session.commit()
            elif film.image != image_url and image_url:
                # Met à jour l'image même si elle existe déjà (au cas où elle serait meilleure)
                film.image = image_url
                db.session.commit()
            # Met à jour aussi le titre si nécessaire
            if movie_data.get('title') and film.name_movie == 'Inconnu':
                film.name_movie = movie_data.get('title')
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
        """Met à jour la note (entier). Note un film le marque automatiquement comme vu."""
        film = WatchlistController._get_or_create_film(movie_data)
        if not film: return False

        commentaire = Commentaire.query.filter_by(ID_user=user_id, ID_film=film.ID_film).first()
        if not commentaire:
            # Si on note un film pas encore dans la liste, on l'ajoute et on le marque comme vu
            commentaire = Commentaire(ID_user=user_id, ID_film=film.ID_film, score_user=score, watched=True)
            db.session.add(commentaire)
        else:
            # Mettre à jour la note ET marquer comme vu (si on note, c'est qu'on a vu)
            commentaire.score_user = score
            commentaire.watched = True
        
        db.session.commit()
        return True

    @staticmethod
    def update_review(user_id, movie_data, review_text):
        """Met à jour ou ajoute une critique (texte)."""
        film = WatchlistController._get_or_create_film(movie_data)
        if not film: return False

        commentaire = Commentaire.query.filter_by(ID_user=user_id, ID_film=film.ID_film).first()
        if not commentaire:
            # Si on ajoute une critique pour un film pas encore dans la liste, on l'ajoute
            commentaire = Commentaire(ID_user=user_id, ID_film=film.ID_film, avis_user=review_text)
            db.session.add(commentaire)
        else:
            commentaire.avis_user = review_text
        
        db.session.commit()
        return True

    @staticmethod
    def remove_from_watchlist(user_id, movie_data):
        """Retire un film de la watchlist."""
        try:
            tmdb_id = int(movie_data.get('tmdb_id'))
        except (ValueError, TypeError):
            return False

        commentaire = Commentaire.query.filter_by(ID_user=user_id, ID_film=tmdb_id).first()
        if commentaire:
            db.session.delete(commentaire)
            db.session.commit()
            return True
        return False