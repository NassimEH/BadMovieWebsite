import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class Config:
    # SECRET_KEY est obligatoire pour les sessions Flask
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Générer une clé secrète par défaut en développement (NE PAS utiliser en production)
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        print("⚠️  ATTENTION: SECRET_KEY non définie dans .env, utilisation d'une clé temporaire.")
        print("   Veuillez définir SECRET_KEY dans votre fichier .env pour la production.")
    
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///badmovie.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Clés TMDB (viennent du .env)
    # Clé API v3 : API_key=...
    TMDB_API_KEY = os.getenv('API_key')
    # Jeton de lecture v4 (Bearer) : JetonTMDB=...
    TMDB_READ_TOKEN = os.getenv('JetonTMDB')
