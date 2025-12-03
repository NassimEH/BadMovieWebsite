import os

import requests
from flask import Blueprint, render_template, jsonify, current_app

movie_bp = Blueprint('movies', __name__, url_prefix='/movies')


@movie_bp.route('/')
def list_movies():
    """Page listant tous les films avec recherche et filtres."""
    return render_template('movies_list.html')


@movie_bp.route('/api/by-category')
def api_movies_by_category():
    """Retourne les films groupés par catégorie au format JSON depuis TMDB.

    Ce point d'API est utilisé côté frontend (JS) pour alimenter
    dynamiquement les sections de catégories sur la page d'accueil
    et la page listant tous les films.
    """
    # On utilise les noms réels définis dans le .env :
    # API_key = <clé API TMDB v3>
    # JetonTMDB = <token de lecture v4> (ici non utilisé car l'API discover accepte la clé v3)
    api_key = os.getenv("API_key") or current_app.config.get("TMDB_API_KEY")
    if not api_key:
        # En cas de mauvaise configuration, on retourne une structure vide
        return jsonify({"error": "TMDB_API_KEY manquante dans l'environnement"}), 500

    # Mapping de nos catégories vers les IDs de genre TMDB
    genre_map = {
        "Action": 28,
        "Horreur": 27,
        "Fantastique": 14,
        "Science-Fiction": 878,
        "Drame": 18,
        "Comédie": 35,
        "Thriller": 53,
        "Guerre": 10752,
        "Romance": 10749,
        "Animation": 16,
        "Documentaire": 99,
        "Biographie": 36,  # approximatif : Histoire
    }

    base_url = "https://api.themoviedb.org/3/discover/movie"
    grouped = {}

    for category, genre_id in genre_map.items():
        params = {
            "api_key": api_key,
            "language": "fr-FR",
            "sort_by": "popularity.desc",
            "with_genres": genre_id,
            "page": 1,
        }

        try:
            response = requests.get(base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            # En cas d'erreur pour une catégorie, on la laisse vide
            grouped[category] = []
            continue

        movies = data.get("results", [])
        grouped[category] = []

        for movie in movies[:10]:  # on limite pour éviter de surcharger l'UI
            poster_path = movie.get("poster_path")
            release_date = movie.get("release_date") or ""
            year = release_date.split("-")[0] if release_date else None

            grouped[category].append(
                {
                    "id": movie.get("id"),
                    "title": movie.get("title") or movie.get("name"),
                    # On construit l'URL de l'affiche TMDB si disponible
                    "image": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                    "year": year,
                    # TMDB retourne la durée ailleurs, donc on laisse vide ici
                    "duration": None,
                    "category": category,
                }
            )

    return jsonify(grouped)
