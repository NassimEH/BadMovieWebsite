"""Extensions Flask pour éviter les imports circulaires."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialisation des extensions sans l'app
db = SQLAlchemy()
login_manager = LoginManager()

