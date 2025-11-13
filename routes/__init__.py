"""Routes package for badmovie app - placeholder blueprints."""

from .auth_routes import auth_bp
from .movie_routes import movie_bp
from .watchlist_routes import watchlist_bp

__all__ = ["auth_bp", "movie_bp", "watchlist_bp"]
