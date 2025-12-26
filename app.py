"""Application principale Flask - Point d'entrée."""
from flask import Flask, render_template, send_from_directory
import os
from extensions import db, login_manager
from config import Config
from routes.auth_routes import auth_bp
from routes.movie_routes import movie_bp
from routes.watchlist_routes import watchlist_bp
from routes.settings_routes import settings_bp
from models import User

app = Flask(__name__, static_folder='static', static_url_path='/static')
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


# Route explicite pour servir les fichiers statiques (nécessaire pour Vercel)
@app.route('/static/<path:filename>')
def static_files(filename):
    """Sert les fichiers statiques."""
    import os
    from flask import abort
    
    # Obtenir le chemin absolu du dossier static
    # Sur Vercel, le fichier app.py est à la racine, donc static/ est au même niveau
    current_file = os.path.abspath(__file__)  # Chemin de app.py
    current_dir = os.path.dirname(current_file)
    static_dir = os.path.join(current_dir, 'static')
    
    # Vérifier si le dossier existe, sinon essayer depuis le répertoire parent
    if not os.path.exists(static_dir):
        # Si on est dans api/, remonter d'un niveau
        parent_dir = os.path.dirname(current_dir)
        static_dir = os.path.join(parent_dir, 'static')
    
    # Vérifier que le fichier existe
    file_path = os.path.join(static_dir, filename)
    if not os.path.exists(file_path):
        # Log pour debug (sera visible dans les logs Vercel)
        print(f"Fichier non trouvé: {file_path}")
        print(f"Recherche dans: {static_dir}")
        print(f"Fichier demandé: {filename}")
        abort(404)
    
    return send_from_directory(static_dir, filename)


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
