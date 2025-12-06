import os
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, render_template, jsonify, current_app, abort
from flask_login import current_user, login_required  
from models import Commentaire        

movie_bp = Blueprint('movies', __name__, url_prefix='/movies')
logger = logging.getLogger(__name__)


@movie_bp.route('/')
def list_movies():
    """Page listant tous les films avec recherche et filtres."""
    return render_template('movies_list.html')


@movie_bp.route('/coming-soon')
def coming_soon():
    """Page listant les films à venir organisés par année."""
    return render_template('coming_soon.html')


@movie_bp.route('/for-you')
@login_required
def for_you():
    """Page de recommandations personnalisées."""
    return render_template('for_you.html')


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

        def fetch_category_movies(category, genre_id):
            """Fonction pour récupérer les films d'une catégorie."""
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
                movies = data.get("results", [])
                
                category_movies = []
                for movie in movies[:10]:  # on limite pour éviter de surcharger l'UI
                    try:
                        poster_path = movie.get("poster_path")
                        release_date = movie.get("release_date") or ""
                        year = release_date.split("-")[0] if release_date else None

                        category_movies.append(
                            {
                                "id": movie.get("id"),
                                "tmdb_id": movie.get("id"),
                                "title": movie.get("title") or movie.get("name"),
                                "image": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                                "year": year,
                                "release_date": release_date,
                                "duration": None,
                                "runtime": None,
                                "category": category,
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement d'un film dans {category}: {str(e)}")
                        continue
                
                return category, category_movies
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout lors de la récupération des films pour {category}")
                return category, []
            except requests.exceptions.HTTPError as e:
                logger.error(f"Erreur HTTP pour {category}: {e.response.status_code}")
                return category, []
            except requests.RequestException as e:
                logger.error(f"Erreur de requête pour {category}: {str(e)}")
                return category, []
            except Exception as e:
                logger.error(f"Erreur inattendue pour {category}: {str(e)}")
                return category, []

        # Exécution parallèle des requêtes avec ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=12) as executor:
            # Soumettre toutes les tâches en parallèle
            future_to_category = {
                executor.submit(fetch_category_movies, category, genre_id): category 
                for category, genre_id in genre_map.items()
            }
            
            # Récupérer les résultats au fur et à mesure
            for future in as_completed(future_to_category):
                category, movies = future.result()
                grouped[category] = movies

        return jsonify(grouped)
    except Exception as e:
        logger.error(f"Erreur inattendue dans api_movies_by_category: {str(e)}", exc_info=True)
        return jsonify({"error": "Erreur serveur lors de la récupération des films"}), 500


@movie_bp.route('/api/filtered')
def api_filtered_movies():
    """Retourne les films filtrés selon les critères de recherche, genre, année, tri."""
    try:
        api_key = _get_tmdb_api_key()
        if not api_key:
            logger.error("TMDB_API_KEY manquante dans l'environnement")
            return jsonify({"error": "TMDB_API_KEY manquante dans l'environnement"}), 500

        from flask import request
        search_query = request.args.get('search', '').strip()
        genre = request.args.get('genre', '').strip()
        year = request.args.get('year', '').strip()
        sort_by = request.args.get('sort', 'recent').strip()
        page = int(request.args.get('page', 1))

        # Mapping des genres
        genre_map = {
            "action": 28,
            "horreur": 27,
            "fantastique": 14,
            "science-fiction": 878,
            "drame": 18,
            "comédie": 35,
            "thriller": 53,
            "guerre": 10752,
            "romance": 10749,
            "animation": 16,
            "documentaire": 99,
            "biographie": 36,
        }

        # Mapping du tri
        sort_map = {
            "recent": "release_date.desc",
            "oldest": "release_date.asc",
            "title-asc": "title.asc",
            "title-desc": "title.desc",
            "rating": "vote_average.desc",
            "popularity": "popularity.desc",
        }

        base_url = "https://api.themoviedb.org/3"
        
        # Utiliser discover pour avoir plus de contrôle sur les filtres
        url = f"{base_url}/discover/movie"
        
        # Tri par défaut : popularité
        default_sort = "popularity.desc"
        if sort_by == "recent":
            # Si l'utilisateur choisit "recent", utiliser release_date.desc
            sort_value = sort_map.get(sort_by, default_sort)
        else:
            sort_value = sort_map.get(sort_by, default_sort)
        
        params = {
            "api_key": api_key,
            "language": "fr-FR",
            "sort_by": sort_value,
            "page": page,
            # Filtrer pour ne montrer que les films déjà sortis (jusqu'en 2025)
            "primary_release_date.lte": "2025-12-31",
            # Ne montrer que les films avec une affiche
            "with_poster": True,
        }
        
        # Ajouter le filtre de genre
        if genre and genre in genre_map:
            params["with_genres"] = genre_map[genre]
        
        # Ajouter le filtre d'année
        if year:
            try:
                year_int = int(year)
                params["primary_release_year"] = year_int
            except ValueError:
                pass
        
        # Si recherche, utiliser l'API de recherche puis filtrer côté serveur
        # Note: TMDB search ne supporte pas bien les filtres combinés, donc on utilise discover
        # Si recherche seule, on peut utiliser search, sinon on filtre après
        if search_query and not genre and not year:
            # Si seulement recherche sans autres filtres, utiliser search
            url = f"{base_url}/search/movie"
            params = {
                "api_key": api_key,
                "language": "fr-FR",
                "query": search_query,
                "page": page,
            }
        # Si recherche avec filtres, on doit filtrer après la recherche
        if search_query and (genre or year):
            try:
                search_response = requests.get(url, params=params, timeout=5)
                search_response.raise_for_status()
                search_data = search_response.json()
                all_movies = search_data.get("results", [])
                
                # Filtrer les résultats par genre, année, et affiche
                filtered_movies = []
                for movie in all_movies:
                    # Ignorer les films sans affiche
                    if not movie.get("poster_path"):
                        continue
                    
                    # Filtrer par date de sortie (max 2025)
                    release_date = movie.get("release_date", "")
                    if release_date:
                        try:
                            from datetime import datetime
                            release_dt = datetime.strptime(release_date, "%Y-%m-%d")
                            max_date = datetime(2025, 12, 31)
                            if release_dt > max_date:
                                continue  # Ignorer les films futurs après 2025
                        except ValueError:
                            pass
                    
                    # Filtrer par genre
                    if genre and genre in genre_map:
                        movie_genres = movie.get("genre_ids", [])
                        if genre_map[genre] not in movie_genres:
                            continue
                    
                    # Filtrer par année
                    if year:
                        if not release_date or not release_date.startswith(year):
                            continue
                    
                    filtered_movies.append(movie)
                
                # Appliquer le tri
                if sort_by == "title-asc":
                    filtered_movies.sort(key=lambda x: (x.get("title") or x.get("name") or "").lower())
                elif sort_by == "title-desc":
                    filtered_movies.sort(key=lambda x: (x.get("title") or x.get("name") or "").lower(), reverse=True)
                elif sort_by == "rating":
                    filtered_movies.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
                elif sort_by == "recent":
                    filtered_movies.sort(key=lambda x: x.get("release_date", ""), reverse=True)
                elif sort_by == "oldest":
                    filtered_movies.sort(key=lambda x: x.get("release_date", ""))
                
                # Pagination manuelle
                per_page = 20
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_movies = filtered_movies[start_idx:end_idx]
                
                # Formater les résultats
                formatted_movies = []
                for movie in paginated_movies:
                    try:
                        poster_path = movie.get("poster_path")
                        release_date = movie.get("release_date") or ""
                        year_movie = release_date.split("-")[0] if release_date else None
                        
                        # Construire l'URL de l'image correctement
                        image_url = None
                        if poster_path:
                            if poster_path.startswith("http"):
                                image_url = poster_path
                            elif poster_path.startswith("/"):
                                image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                            else:
                                image_url = f"https://image.tmdb.org/t/p/w500/{poster_path}"
                        
                        # Récupérer les genres du film
                        genre_names = []
                        if movie.get("genre_ids"):
                            genre_id_to_name = {
                                28: "Action", 27: "Horreur", 14: "Fantastique", 878: "Science-Fiction",
                                18: "Drame", 35: "Comédie", 53: "Thriller", 10752: "Guerre",
                                10749: "Romance", 16: "Animation", 99: "Documentaire", 36: "Biographie"
                            }
                            genre_names = [genre_id_to_name.get(gid, "") for gid in movie.get("genre_ids", [])[:2] if genre_id_to_name.get(gid)]
                        
                        runtime = movie.get("runtime")
                        duration_str = None
                        if runtime:
                            hours = runtime // 60
                            minutes = runtime % 60
                            if hours > 0:
                                duration_str = f"{hours}h{minutes:02d}min"
                            else:
                                duration_str = f"{minutes}min"

                        formatted_movies.append({
                            "id": movie.get("id"),
                            "tmdb_id": movie.get("id"),
                            "title": movie.get("title") or movie.get("name") or "Titre inconnu",
                            "image": image_url,
                            "year": year_movie,
                            "release_date": release_date,
                            "duration": duration_str,
                            "runtime": runtime,
                            "category": ", ".join(genre_names) if genre_names else "Autre",
                            "vote_average": movie.get("vote_average", 0),
                        })
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement d'un film: {str(e)}")
                        continue
                
                # Calculer le total de pages
                total_filtered = len(filtered_movies)
                total_pages = max(1, (total_filtered + per_page - 1) // per_page)
                
                return jsonify({
                    "movies": formatted_movies,
                    "total_pages": total_pages,
                    "current_page": page,
                    "total_results": total_filtered
                })
            except requests.RequestException as e:
                logger.error(f"Erreur lors de la recherche: {str(e)}")
                return jsonify({"error": "Erreur lors de la recherche", "movies": [], "total_pages": 1, "current_page": 1}), 500

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération des films filtrés: {str(e)}")
            return jsonify({"error": "Erreur lors de la récupération des films", "movies": [], "total_pages": 1, "current_page": 1}), 500

        movies = data.get("results", [])
        total_pages = data.get("total_pages", 1)
        current_page = data.get("page", 1)

        formatted_movies = []
        for movie in movies:
            # Filtrer les films sans affiche
            if not movie.get("poster_path"):
                continue
            
            # Filtrer les films futurs (après 2025)
            release_date = movie.get("release_date", "")
            if release_date:
                try:
                    from datetime import datetime
                    release_dt = datetime.strptime(release_date, "%Y-%m-%d")
                    max_date = datetime(2025, 12, 31)
                    if release_dt > max_date:
                        continue
                except ValueError:
                    pass
            try:
                poster_path = movie.get("poster_path")
                release_date = movie.get("release_date") or ""
                year_movie = release_date.split("-")[0] if release_date else None
                
                # Filtrer les films sans affiche ou avec date de sortie future
                if not poster_path:
                    continue  # Ignorer les films sans affiche
                
                # Vérifier que le film est déjà sorti (date <= aujourd'hui ou <= 2025)
                if release_date:
                    try:
                        from datetime import datetime
                        release_dt = datetime.strptime(release_date, "%Y-%m-%d")
                        max_date = datetime(2025, 12, 31)
                        if release_dt > max_date:
                            continue  # Ignorer les films futurs après 2025
                    except ValueError:
                        pass  # Si la date est invalide, on garde le film
                
                # Construire l'URL de l'image correctement
                image_url = None
                if poster_path:
                    # S'assurer que le chemin ne commence pas déjà par http
                    if poster_path.startswith("http"):
                        image_url = poster_path
                    elif poster_path.startswith("/"):
                        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    else:
                        image_url = f"https://image.tmdb.org/t/p/w500/{poster_path}"
                
                # Récupérer les genres
                genre_names = []
                if movie.get("genres"):
                    genre_names = [g.get("name", "") for g in movie.get("genres", [])[:2]]
                elif movie.get("genre_ids"):
                    # Mapping des IDs de genres vers les noms
                    genre_id_to_name = {
                        28: "Action", 27: "Horreur", 14: "Fantastique", 878: "Science-Fiction",
                        18: "Drame", 35: "Comédie", 53: "Thriller", 10752: "Guerre",
                        10749: "Romance", 16: "Animation", 99: "Documentaire", 36: "Biographie"
                    }
                    genre_names = [genre_id_to_name.get(gid, "") for gid in movie.get("genre_ids", [])[:2] if genre_id_to_name.get(gid)]
                
                # Récupérer la durée si disponible
                runtime = movie.get("runtime")
                duration_str = None
                if runtime:
                    hours = runtime // 60
                    minutes = runtime % 60
                    if hours > 0:
                        duration_str = f"{hours}h{minutes:02d}min"
                    else:
                        duration_str = f"{minutes}min"

                formatted_movies.append({
                    "id": movie.get("id"),
                    "tmdb_id": movie.get("id"),
                    "title": movie.get("title") or movie.get("name") or "Titre inconnu",
                    "image": image_url,
                    "year": year_movie,
                    "release_date": release_date,
                    "duration": duration_str,
                    "runtime": runtime,
                    "category": ", ".join(genre_names) if genre_names else "Autre",
                    "vote_average": movie.get("vote_average", 0),
                })
            except Exception as e:
                logger.warning(f"Erreur lors du traitement d'un film: {str(e)}")
                continue

        return jsonify({
            "movies": formatted_movies,
            "total_pages": total_pages,
            "current_page": current_page,
            "total_results": data.get("total_results", 0)
        })
    except Exception as e:
        logger.error(f"Erreur inattendue dans api_filtered_movies: {str(e)}", exc_info=True)
        return jsonify({"error": "Erreur serveur lors de la récupération des films", "movies": [], "total_pages": 1, "current_page": 1}), 500


@movie_bp.route('/api/coming-soon')
def api_coming_soon():
    """Retourne les films à venir groupés par année (2026-2030)."""
    try:
        api_key = _get_tmdb_api_key()
        if not api_key:
            logger.error("TMDB_API_KEY manquante dans l'environnement")
            return jsonify({"error": "TMDB_API_KEY manquante dans l'environnement"}), 500

        base_url = "https://api.themoviedb.org/3/discover/movie"
        years = [2026, 2027, 2028, 2029, 2030]
        # Initialiser toutes les années avec des listes vides
        grouped = {str(year): [] for year in years}

        def fetch_year_movies(year):
            """Fonction pour récupérer les films d'une année spécifique."""
            params = {
                "api_key": api_key,
                "language": "fr-FR",
                "sort_by": "popularity.desc",
                "primary_release_year": year,
                "primary_release_date.gte": f"{year}-01-01",
                "primary_release_date.lte": f"{year}-12-31",
                "page": 1,
                "with_poster": True,
            }

            try:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                movies = data.get("results", [])
                
                year_movies = []
                for movie in movies[:20]:  # Limiter à 20 films par année
                    try:
                        poster_path = movie.get("poster_path")
                        # Ignorer les films sans affiche
                        if not poster_path:
                            continue
                        
                        release_date = movie.get("release_date") or ""
                        year_movie = release_date.split("-")[0] if release_date else None

                        # Construire l'URL de l'image
                        image_url = None
                        if poster_path:
                            if poster_path.startswith("http"):
                                image_url = poster_path
                            elif poster_path.startswith("/"):
                                image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                            else:
                                image_url = f"https://image.tmdb.org/t/p/w500/{poster_path}"
                        
                        # Récupérer les genres
                        genre_names = []
                        if movie.get("genre_ids"):
                            genre_id_to_name = {
                                28: "Action", 27: "Horreur", 14: "Fantastique", 878: "Science-Fiction",
                                18: "Drame", 35: "Comédie", 53: "Thriller", 10752: "Guerre",
                                10749: "Romance", 16: "Animation", 99: "Documentaire", 36: "Biographie"
                            }
                            genre_names = [genre_id_to_name.get(gid, "") for gid in movie.get("genre_ids", [])[:2] if genre_id_to_name.get(gid)]
                        
                        runtime = movie.get("runtime")
                        duration_str = None
                        if runtime:
                            hours = runtime // 60
                            minutes = runtime % 60
                            if hours > 0:
                                duration_str = f"{hours}h{minutes:02d}min"
                            else:
                                duration_str = f"{minutes}min"

                        year_movies.append({
                            "id": movie.get("id"),
                            "tmdb_id": movie.get("id"),
                            "title": movie.get("title") or movie.get("name") or "Titre inconnu",
                            "image": image_url,
                            "year": year_movie,
                            "release_date": release_date,
                            "duration": duration_str,
                            "runtime": runtime,
                            "category": ", ".join(genre_names) if genre_names else "Autre",
                            "vote_average": movie.get("vote_average", 0),
                        })
                    except Exception as e:
                        logger.warning(f"Erreur lors du traitement d'un film pour {year}: {str(e)}")
                        continue
                
                return year, year_movies
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout lors de la récupération des films pour {year}")
                return year, []
            except requests.exceptions.HTTPError as e:
                logger.error(f"Erreur HTTP pour {year}: {e.response.status_code}")
                return year, []
            except requests.RequestException as e:
                logger.error(f"Erreur de requête pour {year}: {str(e)}")
                return year, []
            except Exception as e:
                logger.error(f"Erreur inattendue pour {year}: {str(e)}")
                return year, []

        # Exécution parallèle des requêtes pour les années 2026-2030
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_year = {
                executor.submit(fetch_year_movies, year): year 
                for year in years
            }
            
            # Récupérer les résultats au fur et à mesure
            for future in as_completed(future_to_year):
                try:
                    year, movies = future.result()
                    grouped[str(year)] = movies
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération du résultat pour une année: {str(e)}")
                    # L'année reste avec une liste vide (déjà initialisée)

        # S'assurer que toutes les années sont présentes dans la réponse
        for year in years:
            if str(year) not in grouped:
                grouped[str(year)] = []

        return jsonify(grouped)
    except Exception as e:
        logger.error(f"Erreur inattendue dans api_coming_soon: {str(e)}", exc_info=True)
        return jsonify({"error": "Erreur serveur lors de la récupération des films à venir"}), 500


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

    # Casting
    credits = movie.get("credits", {})
    cast = credits.get("cast", []) if isinstance(credits, dict) else []
    main_cast = [member.get("name") for member in cast[:6] if member.get("name")]

    # --- NOUVEAU : Vérifier si le film est déjà dans la liste ---
    interaction = None
    if current_user.is_authenticated:
        # On cherche s'il existe une liaison User-Film pour cet ID
        interaction = Commentaire.query.filter_by(
            ID_user=current_user.ID_user, 
            ID_film=tmdb_id
        ).first()

        return render_template(
        "movie_detail.html",
        movie=movie,
        poster_url=poster_url,
        backdrop_url=backdrop_url,
        main_cast=main_cast,
        interaction=interaction  # On passe l'info au template
    )


@movie_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    """API pour récupérer les recommandations personnalisées."""
    try:
        from flask import request
        from controllers.recommendation_controller import RecommendationController
        
        limit = int(request.args.get('limit', 20))
        recommendations = RecommendationController.get_recommendations(
            current_user.ID_user, 
            limit=limit
        )
        
        return jsonify({"movies": recommendations})
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {str(e)}", exc_info=True)
        return jsonify({"error": "Erreur serveur lors de la génération des recommandations", "movies": []}), 500