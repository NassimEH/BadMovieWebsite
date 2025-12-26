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

# Configuration du chemin static pour fonctionner sur Vercel
# Utiliser un chemin absolu basé sur l'emplacement de app.py
_static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, static_folder=_static_folder, static_url_path='/static')
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
    from flask import abort
    
    # Liste des chemins possibles pour le dossier static
    current_dir = os.getcwd()
    possible_dirs = [
        os.path.join(current_dir, 'static'),  # Dossier static à la racine
        os.path.join(current_dir, 'public', 'static'),  # Dossier public/static (pour Vercel)
        app.static_folder if app.static_folder else None,  # static_folder configuré
    ]
    
    # Filtrer les chemins None et vérifier l'existence
    for static_dir in possible_dirs:
        if static_dir and os.path.exists(static_dir) and os.path.isdir(static_dir):
            file_path = os.path.join(static_dir, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    return send_from_directory(static_dir, filename)
                except Exception as e:
                    # Continuer à essayer les autres chemins
                    print(f"Erreur avec {static_dir}: {e}")
                    continue
    
    # Si aucun chemin n'a fonctionné, logger pour debug
    print(f"Fichier static non trouvé: {filename}")
    print(f"Répertoire de travail: {current_dir}")
    print(f"Chemins testés: {possible_dirs}")
    print(f"app.static_folder: {app.static_folder}")
    abort(404)


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
