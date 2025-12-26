import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        print("********* ATTENTION: SECRET_KEY non définie dans .env, utilisation d'une clé temporaire.")
        print("   Veuillez définir SECRET_KEY dans votre fichier .env pour la production.")

    # Configuration PostgreSQL (avec fallback SQLite pour développement local)
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        # PostgreSQL (production/Docker)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # SQLite (développement local sans Docker)
        SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///badmovie.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TMDB_API_KEY = os.getenv('API_key')
    TMDB_READ_TOKEN = os.getenv('JetonTMDB')
