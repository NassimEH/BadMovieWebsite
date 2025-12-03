"""Contrôleur pour la gestion des films."""
import os
import requests
from datetime import datetime, time
from flask import current_app
from extensions import db
from models import Film

class MovieController:
    """Contrôleur pour les opérations sur les films."""

    @staticmethod
    def get_all_movies():
        """Récupère tous les films."""
        return Film.query.all()

    @staticmethod
    def get_or_create_from_tmdb(tmdb_id):
        """
        Vérifie si le film existe en BDD. Sinon, le récupère depuis TMDB.
        """
        film = Film.query.get(tmdb_id)
        if film:
            return film

        api_key = os.getenv("API_key") or current_app.config.get("TMDB_API_KEY")
        if not api_key:
            raise ValueError("Clé API TMDB manquante.")

        # Appel à l'API TMDB
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        params = {"api_key": api_key, "language": "fr-FR"}
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return None
            
        data = response.json()

        # Traitement des données
        release_date = None
        if data.get('release_date'):
            try:
                release_date = datetime.strptime(data['release_date'], '%Y-%m-%d').date()
            except ValueError:
                pass 

        duration_time = None
        runtime = data.get('runtime') 
        if runtime:
            duration_time = time(runtime // 60, runtime % 60)

        poster_path = data.get('poster_path')
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        genres = data.get('genres', [])
        category_name = genres[0]['name'] if genres else "Inconnu"

        new_film = Film(
            ID_film=data['id'],
            name_movie=data['title'],
            image=image_url,
            year_movie=release_date,
            duration=duration_time,
            category=category_name
        )

        db.session.add(new_film)
        db.session.commit()

        return new_film