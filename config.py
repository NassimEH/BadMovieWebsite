import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') 
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///badmovie.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Clés TMDB (viennent du .env)
    # Clé API v3 : API_key=...
    TMDB_API_KEY = os.getenv('API_key')
    # Jeton de lecture v4 (Bearer) : JetonTMDB=...
    TMDB_READ_TOKEN = os.getenv('JetonTMDB')
