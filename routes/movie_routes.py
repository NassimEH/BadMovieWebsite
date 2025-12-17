import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests 
from flask import Blueprint, render_template, jsonify, current_app, abort, request
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
            "Biographie": 36,
        }

        base_url = "https://api.themoviedb.org/3/discover/movie"
        grouped = {}

        def fetch_category_movies(category, genre_id):
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
                for movie in movies[:10]:
                    try:
                        poster_path = movie.get("poster_path")
                        release_date = movie.get("release_date") or ""
                        year = release_date.split("-")[0] if release_date else None

                        category_movies.append(
                            {
                                "id": movie.get("id"),
                                "tmdb_id": movie.get("id"),
                                "title": movie.get("title") or movie.get("name"),
                                "image": "https://image.tmdb.org/t/p/w500%s" % poster_path if poster_path else None,
                                "year": year,
                                "release_date": release_date,
                                "duration": None,
                                "runtime": None,
                                "category": category,
                            }
                        )
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning("Erreur lors du traitement d'un film dans %s: %s", category, str(e))
                        continue

                return category, category_movies
            except requests.exceptions.Timeout:
                logger.warning("Timeout lors de la récupération des films pour %s", category)
                return category, []
            except requests.exceptions.HTTPError as e:
                logger.error("Erreur HTTP pour %s: %s", category, e.response.status_code)
                return category, []
            except requests.RequestException as e:
                logger.error("Erreur de requête pour %s: %s", category, str(e))
                return category, []

        with ThreadPoolExecutor(max_workers=12) as executor:
            future_to_category = {
                executor.submit(fetch_category_movies, category, genre_id): category
                for category, genre_id in genre_map.items()
            }
            for future in as_completed(future_to_category):
                category, movies = future.result()
                grouped[category] = movies

        return jsonify(grouped)
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Erreur de traitement des données dans api_movies_by_category: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur serveur lors de la récupération des films"}), 500
    except requests.RequestException as e:
        logger.error("Erreur de connexion à l'API TMDB dans api_movies_by_category: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur de connexion à l'API"}), 500


@movie_bp.route('/api/filtered')
def api_filtered_movies():
    """Retourne les films filtrés selon les critères de recherche, genre, année, tri."""
    try:
        api_key = _get_tmdb_api_key()
        if not api_key:
            logger.error("TMDB_API_KEY manquante dans l'environnement")
            return jsonify({"error": "TMDB_API_KEY manquante dans l'environnement"}), 500

        search_query = request.args.get('search', '').strip()
        genre = request.args.get('genre', '').strip()
        year = request.args.get('year', '').strip()
        sort_by = request.args.get('sort', 'recent').strip()
        page = int(request.args.get('page', 1))

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
        url = "%s/discover/movie" % base_url

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
            "primary_release_date.lte": "2025-12-31",
            "with_poster": True,
        }

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
        if search_query and (genre or year):
            try:
                search_response = requests.get(url, params=params, timeout=5)
                search_response.raise_for_status()
                search_data = search_response.json()
                all_movies = search_data.get("results", [])
                
                filtered_movies = []
                for movie in all_movies:
                    if not movie.get("poster_path"):
                        continue

                    release_date = movie.get("release_date", "")
                    if release_date:
                        try:
                            release_dt = datetime.strptime(release_date, "%Y-%m-%d")
                            max_date = datetime(2025, 12, 31)
                            if release_dt > max_date:
                                continue
                        except ValueError:
                            pass

                    if genre and genre in genre_map:
                        movie_genres = movie.get("genre_ids", [])
                        if genre_map[genre] not in movie_genres:
                            continue

                    if year:
                        if not release_date or not release_date.startswith(year):
                            continue

                    filtered_movies.append(movie)

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

                per_page = 20
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_movies = filtered_movies[start_idx:end_idx]

                formatted_movies = []
                for movie in paginated_movies:
                    try:
                        poster_path = movie.get("poster_path")
                        release_date = movie.get("release_date") or ""
                        year_movie = release_date.split("-")[0] if release_date else None

                        image_url = None
                        if poster_path:
                            if poster_path.startswith("http"):
                                image_url = poster_path
                            elif poster_path.startswith("/"):
                                image_url = "https://image.tmdb.org/t/p/w500%s" % poster_path
                            else:
                                image_url = "https://image.tmdb.org/t/p/w500/%s" % poster_path

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
                                duration_str = "%dh%02dmin" % (hours, minutes)
                            else:
                                duration_str = "%dmin" % minutes

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
                    except (KeyError, ValueError, TypeError, AttributeError) as e:
                        logger.warning("Erreur lors du traitement d'un film: %s", str(e))
                        continue

                total_filtered = len(filtered_movies)
                total_pages = max(1, (total_filtered + per_page - 1) // per_page)

                return jsonify({
                    "movies": formatted_movies,
                    "total_pages": total_pages,
                    "current_page": page,
                    "total_results": total_filtered
                })
            except requests.RequestException as e:
                logger.error("Erreur lors de la recherche: %s", str(e))
                return jsonify({"error": "Erreur lors de la recherche", "movies": [], "total_pages": 1, "current_page": 1}), 500

        def filter_and_format_movies(movies_list):
            formatted = []
            for movie in movies_list:
                if not movie.get("poster_path"):
                    continue

                release_date = movie.get("release_date", "")
                if release_date:
                    try:
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

                    if not poster_path:
                        continue

                    if release_date:
                        try:
                            release_dt = datetime.strptime(release_date, "%Y-%m-%d")
                            max_date = datetime(2025, 12, 31)
                            if release_dt > max_date:
                                continue
                        except ValueError:
                            pass

                    image_url = None
                    if poster_path:
                        if poster_path.startswith("http"):
                            image_url = poster_path
                        elif poster_path.startswith("/"):
                            image_url = "https://image.tmdb.org/t/p/w500%s" % poster_path
                        else:
                            image_url = "https://image.tmdb.org/t/p/w500/%s" % poster_path

                    genre_names = []
                    if movie.get("genres"):
                        genre_names = [g.get("name", "") for g in movie.get("genres", [])[:2]]
                    elif movie.get("genre_ids"):
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
                            duration_str = "%dh%02dmin" % (hours, minutes)
                        else:
                            duration_str = "%dmin" % minutes

                    formatted.append({
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
                except (KeyError, ValueError, TypeError, AttributeError) as e:
                    logger.warning("Erreur lors du traitement d'un film: %s", str(e))
                    continue
            return formatted

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error("Erreur lors de la récupération des films filtrés: %s", str(e))
            return jsonify({"error": "Erreur lors de la récupération des films", "movies": [], "total_pages": 1, "current_page": 1}), 500

        movies = data.get("results", [])
        total_pages = data.get("total_pages", 1)
        current_page = data.get("page", 1)

        formatted_movies = filter_and_format_movies(movies)
        
        if len(formatted_movies) == 0 and current_page == total_pages and current_page > 1:
            max_attempts = min(5, current_page - 1)
            for attempt in range(1, max_attempts + 1):
                prev_page = current_page - attempt
                if prev_page < 1:
                    break
                
                try:
                    prev_params = params.copy()
                    prev_params["page"] = prev_page
                    prev_response = requests.get(url, params=prev_params, timeout=5)
                    prev_response.raise_for_status()
                    prev_data = prev_response.json()
                    prev_movies = prev_data.get("results", [])
                    prev_formatted = filter_and_format_movies(prev_movies)
                    
                    if len(prev_formatted) > 0:
                        formatted_movies = prev_formatted
                        current_page = prev_page
                        total_pages = prev_page
                        logger.info("Page %s vide, utilisation de la page %s avec %s films", current_page, prev_page, len(prev_formatted))
                        break
                except requests.RequestException as e:
                    logger.warning("Erreur lors de la récupération de la page %s: %s", prev_page, str(e))
                    continue

        return jsonify({
            "movies": formatted_movies,
            "total_pages": total_pages,
            "current_page": current_page,
            "total_results": data.get("total_results", 0)
        })
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        logger.error("Erreur de traitement des données dans api_filtered_movies: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur de traitement des données", "movies": [], "total_pages": 1, "current_page": 1}), 500
    except requests.RequestException as e:
        logger.error("Erreur de connexion à l'API TMDB dans api_filtered_movies: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur de connexion à l'API", "movies": [], "total_pages": 1, "current_page": 1}), 500


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
        grouped = {str(year): [] for year in years}

        today = datetime.now().strftime("%Y-%m-%d")
        max_date = "2030-12-31"

        def fetch_future_movies():
            all_movies = []
            page = 1
            max_pages = 20  # Augmenter à 20 pages pour avoir plus de films
            
            # Objectif : avoir au moins 10 films par année avant de s'arrêter
            min_films_per_year = 10
            
            while page <= max_pages:
                params = {
                    "api_key": api_key,
                    "language": "fr-FR",
                    "sort_by": "popularity.desc",
                    "primary_release_date.gte": today,
                    "primary_release_date.lte": max_date,
                    "page": page,
                    "with_poster": True,
                }

                try:
                    response = requests.get(base_url, params=params, timeout=8)
                    response.raise_for_status()
                    data = response.json()
                    movies = data.get("results", [])

                    if not movies:
                        break

                    all_movies.extend(movies)

                    # Vérifier si on a assez de films pour chaque année
                    # Vérifier plus tôt (après 100 films au lieu de 300) pour s'arrêter plus rapidement
                    if len(all_movies) >= 100:
                        temp_grouped = {}
                        for movie in all_movies:
                            release_date = movie.get("release_date", "")
                            if release_date:
                                year = int(release_date.split("-")[0])
                                if year in years:
                                    if str(year) not in temp_grouped:
                                        temp_grouped[str(year)] = 0
                                    temp_grouped[str(year)] += 1
                            

                        years_present = [y for y in years if str(y) in temp_grouped]

                        # Si toutes les années sont présentes ET qu'elles ont toutes au moins 8 films, on peut arrêter
                        if len(years_present) == len(years):
                            min_films = min([temp_grouped[str(y)] for y in years])
                            # S'assurer qu'on a au moins 8 films pour chaque année avant d'arrêter
                            if min_films >= min_films_per_year:
                                break
  
                    total_pages = data.get("total_pages", 1)
                    if page >= total_pages:
                        break

                    page += 1
                except requests.exceptions.Timeout:
                    logger.warning("Timeout lors de la récupération de la page %s", page)
                    break
                except requests.exceptions.HTTPError as e:
                    logger.error("Erreur HTTP pour la page %s: %s", page, e.response.status_code)
                    break
                except requests.RequestException as e:
                    logger.error("Erreur de requête pour la page %s: %s", page, str(e))
                    break
                except (KeyError, ValueError, TypeError) as e:
                    logger.error("Erreur de traitement des données pour la page %s: %s", page, str(e))
                    break
  
            return all_movies

        try:
            movies = fetch_future_movies()

            for movie in movies:
                try:
                    poster_path = movie.get("poster_path")
                    if not poster_path:
                        continue

                    release_date = movie.get("release_date") or ""
                    if not release_date:
                        continue

                    # Extraire l'année de la date de sortie
                    try:
                        year_movie = int(release_date.split("-")[0])
                    except (ValueError, IndexError):
                        continue

                    if year_movie not in years:
                        continue

                    image_url = None
                    if poster_path:
                        if poster_path.startswith("http"):
                            image_url = poster_path
                        elif poster_path.startswith("/"):
                            image_url = "https://image.tmdb.org/t/p/w500%s" % poster_path
                        else:
                            image_url = "https://image.tmdb.org/t/p/w500/%s" % poster_path
   
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
                            duration_str = "%dh%02dmin" % (hours, minutes)
                        else:
                            duration_str = "%dmin" % minutes

                    movie_data = {
                        "id": movie.get("id"),
                        "tmdb_id": movie.get("id"),
                        "title": movie.get("title") or movie.get("name") or "Titre inconnu",
                        "image": image_url,
                        "year": str(year_movie),
                        "release_date": release_date,
                        "duration": duration_str,
                        "runtime": runtime,
                        "category": ", ".join(genre_names) if genre_names else "Autre",
                        "vote_average": movie.get("vote_average", 0),
                    }     
                    grouped[str(year_movie)].append(movie_data)
                except (KeyError, ValueError, TypeError, AttributeError) as e:
                    logger.warning("Erreur lors du traitement d'un film: %s", str(e))
                    continue
            # Limiter à 12 films par année après avoir tout traité pour améliorer les performances
            # Mais s'assurer qu'on a au moins quelques films pour chaque année
            for year in years:
                if len(grouped[str(year)]) > 12:
                    grouped[str(year)] = grouped[str(year)][:12]
                # Si une année a très peu de films, essayer de garder tous ceux qu'on a
                elif len(grouped[str(year)]) < 5:
                    # Garder tous les films disponibles pour cette année
                    pass
        except (KeyError, ValueError, TypeError) as e:
            logger.error("Erreur de traitement des données lors de la récupération des films à venir: %s", str(e))
            # Les années restent avec des listes vides (déjà initialisées)
        except requests.RequestException as e:
            logger.error("Erreur de connexion à l'API lors de la récupération des films à venir: %s", str(e))
            # Les années restent avec des listes vides (déjà initialisées)

        for year in years:
            if str(year) not in grouped:
                grouped[str(year)] = []

        return jsonify(grouped)
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Erreur de traitement des données dans api_coming_soon: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur de traitement des données"}), 500
    except requests.RequestException as e:
        logger.error("Erreur de connexion à l'API TMDB dans api_coming_soon: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur de connexion à l'API"}), 500


@movie_bp.route('/<int:tmdb_id>')
def movie_detail(tmdb_id: int):
    """Page de détail pour un film issu de TMDB."""
    api_key = _get_tmdb_api_key()
    if not api_key:
        abort(500, description="TMDB_API_KEY manquante dans l'environnement")

    base_url = "https://api.themoviedb.org/3/movie"

    try:
        detail_resp = requests.get(
            "%s/%s" % (base_url, tmdb_id),
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

    poster_path = movie.get("poster_path")
    backdrop_path = movie.get("backdrop_path")

    poster_url = "https://image.tmdb.org/t/p/w500%s" % poster_path if poster_path else None
    backdrop_url = "https://image.tmdb.org/t/p/original%s" % backdrop_path if backdrop_path else None

    credits = movie.get("credits", {})
    cast = credits.get("cast", []) if isinstance(credits, dict) else []
    main_cast = [member.get("name") for member in cast[:6] if member.get("name")]

    # Vérifier si le film est déjà dans la liste ---
    interaction = None
    if current_user.is_authenticated:
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
        interaction=interaction
    )


@movie_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    """API pour récupérer les recommandations personnalisées."""
    try:
        from controllers.recommendation_controller import RecommendationController
        from controllers.watchlist_controller import WatchlistController
        limit = int(request.args.get('limit', 20))
        
        # Vérifier si la watchlist est vide pour déterminer si les recommandations sont aléatoires
        watchlist = WatchlistController.get_user_watchlist(current_user.ID_user)
        is_random = not watchlist or len(watchlist) == 0
        
        recommendations = RecommendationController.get_recommendations(
            current_user.ID_user,
            limit=limit
        )
        return jsonify({
            "movies": recommendations,
            "is_random": is_random
        })
    except ImportError as e:
        logger.error("Erreur d'importation du contrôleur de recommandations: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur de configuration du serveur", "movies": []}), 500
    except (ValueError, TypeError, AttributeError) as e:
        logger.error("Erreur de traitement des données lors de la génération des recommandations: %s", str(e), exc_info=True)
        return jsonify({"error": "Erreur de traitement des données", "movies": []}), 500
