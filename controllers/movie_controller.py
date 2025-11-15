"""Contrôleur pour la gestion des films."""
from models import Film


class MovieController:
    """Contrôleur pour les opérations sur les films."""
    
    @staticmethod
    def get_all_movies():
        """Récupère tous les films."""
        return Film.query.all()
    
    @staticmethod
    def get_movie_by_id(movie_id):
        """Récupère un film par son ID."""
        return Film.query.get_or_404(movie_id)
    
    @staticmethod
    def search_movies(query):
        """Recherche des films par nom."""
        return Film.query.filter(
            Film.name_movie.ilike(f'%{query}%')
        ).all()
    
    @staticmethod
    def get_movies_by_category(category):
        """Récupère les films d'une catégorie."""
        return Film.query.filter_by(category=category).all()

