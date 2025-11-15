"""Application principale Flask - Point d'entrée."""
from flask import Flask, render_template
from extensions import db, login_manager
from config import Config

# Création de l'application Flask
app = Flask(__name__)
app.config.from_object(Config)

# Initialisation des extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import des modèles (après l'initialisation de db)
from models import User, Film, Commentaire

# Callback pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur depuis la base de données."""
    return User.query.get(int(user_id))

# Import et enregistrement des blueprints
from routes.auth_routes import auth_bp
from routes.movie_routes import movie_bp
from routes.watchlist_routes import watchlist_bp

app.register_blueprint(auth_bp)
app.register_blueprint(movie_bp)
app.register_blueprint(watchlist_bp)


@app.route('/')
def index():
    """Page d'accueil."""
    return render_template('index.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Création des tables si elles n'existent pas
    app.run(debug=True)
