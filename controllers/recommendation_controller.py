"""Contrôleur pour les recommandations de films."""
import os
import logging
import requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import current_app
from models import Commentaire
from controllers.watchlist_controller import WatchlistController

logger = logging.getLogger(__name__)


class RecommendationController:
    """Contrôleur pour générer des recommandations de films."""
    
    @staticmethod
    def _get_tmdb_api_key():
        """Récupère la clé TMDB depuis l'env ou la config Flask."""
        return os.getenv("API_key") or current_app.config.get("TMDB_API_KEY")
    
    @staticmethod
    def get_user_preferences(user_id):
        """Récupère les préférences de l'utilisateur basées sur sa watchlist."""
        watchlist = WatchlistController.get_user_watchlist(user_id)
        
        highly_rated = [
            item for item in watchlist 
            if item.score_user and item.score_user > 3
        ]
        
        if not highly_rated:
            return None, None, None, []
        
        watchlist_ids = {item.ID_film for item in watchlist}
        
        genres_counter = Counter()
        directors_counter = Counter()
        actors_counter = Counter()
        favorite_movie_ids = []
        
        api_key = RecommendationController._get_tmdb_api_key()
        if not api_key:
            logger.error("TMDB_API_KEY manquante")
            return None, None, None, watchlist_ids
        
        base_url = "https://api.themoviedb.org/3/movie"
        
        def fetch_movie_details(item):
            tmdb_id = item.ID_film
            try:
                response = requests.get(
                    f"{base_url}/{tmdb_id}",
                    params={
                        "api_key": api_key,
                        "language": "fr-FR",
                        "append_to_response": "credits",
                    },
                    timeout=3,
                )
                response.raise_for_status()
                return item, response.json()
            except requests.RequestException as e:
                logger.warning(f"Erreur lors de la récupération des détails pour {tmdb_id}: {str(e)}")
                return item, None
            except Exception as e:
                logger.warning(f"Erreur inattendue pour {tmdb_id}: {str(e)}")
                return item, None
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {
                executor.submit(fetch_movie_details, item): item 
                for item in highly_rated
            }
            
            for future in as_completed(future_to_item):
                item, movie_data = future.result()
                if not movie_data:
                    continue
                
                favorite_movie_ids.append(item.ID_film)
                
                movie_genres = movie_data.get("genres", [])
                for genre in movie_genres:
                    genres_counter[genre.get("id")] += item.score_user
                
                credits = movie_data.get("credits", {})
                crew = credits.get("crew", []) if isinstance(credits, dict) else []
                for person in crew:
                    if person.get("job") == "Director":
                        directors_counter[person.get("id")] += item.score_user
                
                cast = credits.get("cast", []) if isinstance(credits, dict) else []
                for actor in cast[:3]:
                    actors_counter[actor.get("id")] += item.score_user
        
        top_genres = [genre_id for genre_id, _ in genres_counter.most_common(3)]
        top_directors = [director_id for director_id, _ in directors_counter.most_common(2)]
        top_actors = [actor_id for actor_id, _ in actors_counter.most_common(3)]
        
        return top_genres, top_directors, top_actors, watchlist_ids
    
    @staticmethod
    def get_recommendations(user_id, limit=20):
        """Génère des recommandations de films pour l'utilisateur."""
        api_key = RecommendationController._get_tmdb_api_key()
        if not api_key:
            logger.error("TMDB_API_KEY manquante")
            return []
        
        # Récupérer les préférences
        top_genres, top_directors, top_actors, watchlist_ids = RecommendationController.get_user_preferences(user_id)
        
        if not top_genres:
            return RecommendationController._get_popular_movies(api_key, watchlist_ids, limit)
        
        base_url = "https://api.themoviedb.org/3/discover/movie"
        recommended_movies = []
        seen_ids = set(watchlist_ids)
        
        if top_directors:
            for director_id in top_directors[:2]:
                for genre_id in top_genres[:2]:
                    movies = RecommendationController._discover_movies(
                        api_key, base_url,
                        genre_ids=[genre_id],
                        director_id=director_id,
                        exclude_ids=seen_ids,
                        limit=5
                    )
                    for movie in movies:
                        if movie["id"] not in seen_ids:
                            recommended_movies.append(movie)
                            seen_ids.add(movie["id"])
                            if len(recommended_movies) >= limit:
                                break
                    if len(recommended_movies) >= limit:
                        break
                if len(recommended_movies) >= limit:
                    break
        
        if len(recommended_movies) < limit and top_actors:
            for actor_id in top_actors[:2]:
                for genre_id in top_genres[:2]:
                    movies = RecommendationController._discover_movies(
                        api_key, base_url,
                        genre_ids=[genre_id],
                        actor_id=actor_id,
                        exclude_ids=seen_ids,
                        limit=5
                    )
                    for movie in movies:
                        if movie["id"] not in seen_ids:
                            recommended_movies.append(movie)
                            seen_ids.add(movie["id"])
                            if len(recommended_movies) >= limit:
                                break
                    if len(recommended_movies) >= limit:
                        break
                if len(recommended_movies) >= limit:
                    break
        
        if len(recommended_movies) < limit:
            from models import Commentaire
            watchlist = WatchlistController.get_user_watchlist(user_id)
            highly_rated = [
                item for item in watchlist 
                if item.score_user and item.score_user > 3
            ]
            
            for item in highly_rated[:3]:
                if len(recommended_movies) >= limit:
                    break
                movies = RecommendationController._get_similar_movies(
                    api_key, item.ID_film, exclude_ids=seen_ids, limit=5
                )
                for movie in movies:
                    if movie["id"] not in seen_ids:
                        recommended_movies.append(movie)
                        seen_ids.add(movie["id"])
                        if len(recommended_movies) >= limit:
                            break
        
        if len(recommended_movies) < limit:
            for genre_id in top_genres:
                movies = RecommendationController._discover_movies(
                    api_key, base_url,
                    genre_ids=[genre_id],
                    exclude_ids=seen_ids,
                    limit=10
                )
                for movie in movies:
                    if movie["id"] not in seen_ids:
                        recommended_movies.append(movie)
                        seen_ids.add(movie["id"])
                        if len(recommended_movies) >= limit:
                            break
                if len(recommended_movies) >= limit:
                    break
        
        if len(recommended_movies) < limit:
            popular = RecommendationController._get_popular_movies(
                api_key, seen_ids, limit - len(recommended_movies)
            )
            recommended_movies.extend(popular)
        
        return recommended_movies[:limit]
    
    @staticmethod
    def _discover_movies(api_key, base_url, genre_ids=None, director_id=None, actor_id=None, exclude_ids=None, limit=10):
        """Découvre des films selon des critères."""
        params = {
            "api_key": api_key,
            "language": "fr-FR",
            "sort_by": "popularity.desc",
            "page": 1,
            "primary_release_date.lte": "2025-12-31",
        }
        
        if genre_ids:
            params["with_genres"] = ",".join(map(str, genre_ids))
        
        if director_id:
            params["with_crew"] = str(director_id)
        
        if actor_id:
            params["with_cast"] = str(actor_id)
        
        try:
            response = requests.get(base_url, params=params, timeout=3)
            response.raise_for_status()
            data = response.json()
            movies = data.get("results", [])
            
            formatted = []
            for movie in movies:
                movie_id = movie.get("id")
                if exclude_ids and movie_id in exclude_ids:
                    continue
                
                poster_path = movie.get("poster_path")
                if not poster_path:
                    continue
                
                release_date = movie.get("release_date", "")
                year = release_date.split("-")[0] if release_date else None
                
                if release_date:
                    try:
                        from datetime import datetime
                        release = datetime.strptime(release_date, "%Y-%m-%d")
                        if release.year > 2025:
                            continue
                    except ValueError:
                        pass
                
                formatted.append({
                    "id": movie_id,
                    "tmdb_id": movie_id,
                    "title": movie.get("title") or movie.get("name") or "Titre inconnu",
                    "image": f"https://image.tmdb.org/t/p/w500{poster_path}",
                    "year": year,
                    "release_date": release_date,
                    "vote_average": movie.get("vote_average", 0),
                    "popularity": movie.get("popularity", 0),
                })
                
                if len(formatted) >= limit:
                    break
            
            return formatted
        except requests.RequestException as e:
            logger.warning(f"Erreur lors de la découverte de films: {str(e)}")
            return []
    
    @staticmethod
    def _get_similar_movies(api_key, movie_id, exclude_ids=None, limit=10):
        """Récupère des films similaires à un film donné."""
        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
            response = requests.get(
                url,
                params={
                    "api_key": api_key,
                    "language": "fr-FR",
                    "page": 1,
                },
                timeout=3,
            )
            response.raise_for_status()
            data = response.json()
            movies = data.get("results", [])
            
            formatted = []
            for movie in movies:
                movie_id = movie.get("id")
                if exclude_ids and movie_id in exclude_ids:
                    continue
                
                poster_path = movie.get("poster_path")
                if not poster_path:
                    continue
                
                release_date = movie.get("release_date", "")
                year = release_date.split("-")[0] if release_date else None
                
                if release_date:
                    try:
                        from datetime import datetime
                        release = datetime.strptime(release_date, "%Y-%m-%d")
                        if release.year > 2025:
                            continue
                    except ValueError:
                        pass
                
                formatted.append({
                    "id": movie_id,
                    "tmdb_id": movie_id,
                    "title": movie.get("title") or movie.get("name") or "Titre inconnu",
                    "image": f"https://image.tmdb.org/t/p/w500{poster_path}",
                    "year": year,
                    "release_date": release_date,
                    "vote_average": movie.get("vote_average", 0),
                    "popularity": movie.get("popularity", 0),
                })
                
                if len(formatted) >= limit:
                    break
            
            return formatted
        except requests.RequestException as e:
            logger.warning(f"Erreur lors de la récupération de films similaires: {str(e)}")
            return []
    
    @staticmethod
    def _get_popular_movies(api_key, exclude_ids=None, limit=20):
        """Récupère des films populaires."""
        try:
            url = "https://api.themoviedb.org/3/discover/movie"
            response = requests.get(
                url,
                params={
                    "api_key": api_key,
                    "language": "fr-FR",
                    "sort_by": "popularity.desc",
                    "page": 1,
                    "primary_release_date.lte": "2025-12-31",
                },
                timeout=3,
            )
            response.raise_for_status()
            data = response.json()
            movies = data.get("results", [])
            
            formatted = []
            for movie in movies:
                movie_id = movie.get("id")
                if exclude_ids and movie_id in exclude_ids:
                    continue
                
                poster_path = movie.get("poster_path")
                if not poster_path:
                    continue
                
                release_date = movie.get("release_date", "")
                year = release_date.split("-")[0] if release_date else None
                
                formatted.append({
                    "id": movie_id,
                    "tmdb_id": movie_id,
                    "title": movie.get("title") or movie.get("name") or "Titre inconnu",
                    "image": f"https://image.tmdb.org/t/p/w500{poster_path}",
                    "year": year,
                    "release_date": release_date,
                    "vote_average": movie.get("vote_average", 0),
                    "popularity": movie.get("popularity", 0),
                })
                
                if len(formatted) >= limit:
                    break
            
            return formatted
        except requests.RequestException as e:
            logger.warning(f"Erreur lors de la récupération de films populaires: {str(e)}")
            return []

