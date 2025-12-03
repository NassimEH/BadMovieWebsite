import os
import logging

import requests
from flask import Blueprint, render_template, jsonify, current_app, abort

movie_bp = Blueprint('movies', __name__, url_prefix='/movies')
logger = logging.getLogger(__name__)


@movie_bp.route('/')
def list_movies():
    """Page listant tous les films avec recherche et filtres."""
    return render_template('movies_list.html')


def _get_tmdb_api_key():
    """Récupère la clé TMDB depuis l'env ou la config Flask."""
    return os.getenv("API_key") or current_app.config.get("TMDB_API_KEY")


@movie_bp.route('/api/by-category')
def api_movies_by_category():
    """Retourne les films groupés par catégorie au format JSON depuis TMDB.

    Ce point d'API est utilisé côté frontend (JS) pour alimenter
    dynamiquement les sections de catégories sur la page d'accueil
    et la page listant tous les films.
    """
    try:
        api_key = _get_tmdb_api_key()
        if not api_key:
            logger.error("TMDB_API_KEY manquante dans l'environnement")
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
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout lors de la récupération des films pour {category}")
                grouped[category] = []
                continue
            except requests.exceptions.HTTPError as e:
                logger.error(f"Erreur HTTP pour {category}: {e.response.status_code} - {e.response.text}")
                grouped[category] = []
                continue
            except requests.RequestException as e:
                logger.error(f"Erreur de requête pour {category}: {str(e)}")
                grouped[category] = []
                continue

            movies = data.get("results", [])
            grouped[category] = []

            for movie in movies[:10]:  # on limite pour éviter de surcharger l'UI
                try:
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
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement d'un film dans {category}: {str(e)}")
                    continue

        return jsonify(grouped)
    except Exception as e:
        logger.error(f"Erreur inattendue dans api_movies_by_category: {str(e)}", exc_info=True)
        return jsonify({"error": "Erreur serveur lors de la récupération des films"}), 500


@movie_bp.route('/<int:tmdb_id>')
def movie_detail(tmdb_id: int):
    """Page de détail pour un film issu de TMDB."""
    api_key = _get_tmdb_api_key()
    if not api_key:
        abort(500, description="TMDB_API_KEY manquante dans l'environnement")

    base_url = "https://api.themoviedb.org/3/movie"

    try:
        # Détails du film
        detail_resp = requests.get(
            f"{base_url}/{tmdb_id}",
            params={
                "api_key": api_key,
                "language": "fr-FR",
                "append_to_response": "credits,videos",
            },
            timeout=5,
        )
        detail_resp.raise_for_status()
        movie = detail_resp.json()
    except requests.RequestException:
        abort(404)

    # Construction des URLs d'images
    poster_path = movie.get("poster_path")
    backdrop_path = movie.get("backdrop_path")

    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else None

    # Casting principal (quelques acteurs)
    credits = movie.get("credits", {})
    cast = credits.get("cast", []) if isinstance(credits, dict) else []
    main_cast = [
        member.get("name")
        for member in cast[:6]
        if member.get("name")
    ]

    return render_template(
        "movie_detail.html",
        movie=movie,
        poster_url=poster_url,
        backdrop_url=backdrop_url,
        main_cast=main_cast,
    )
