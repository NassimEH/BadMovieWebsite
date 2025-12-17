"""Application principale Flask - Point d'entrée."""
from flask import Flask, render_template
from extensions import db, login_manager
from config import Config
from routes.auth_routes import auth_bp
from routes.movie_routes import movie_bp
from routes.watchlist_routes import watchlist_bp
from routes.settings_routes import settings_bp
from models import User

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur depuis la base de données."""
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(movie_bp)
app.register_blueprint(watchlist_bp)
app.register_blueprint(settings_bp)


@app.route('/')
def index():
    """Page d'accueil."""
    return render_template('index.html')


if __name__ == '__main__':
    import os
    with app.app_context():
        db.create_all()  # Création des tables si elles n'existent pas
    # Écouter sur 0.0.0.0 pour permettre les connexions externes (Docker)
    # Utiliser DEBUG depuis les variables d'environnement (False par défaut en production)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
