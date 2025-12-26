"""Point d'entrée pour Vercel (format serverless)."""
import sys
import os

# Obtenir le répertoire racine du projet (un niveau au-dessus de api/)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ajouter le répertoire racine au path Python
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Changer le répertoire de travail vers la racine pour que les chemins relatifs fonctionnent
os.chdir(root_dir)

# Importer l'application Flask APRÈS avoir changé le répertoire de travail
from app import app
from extensions import db

# Initialiser la base de données au démarrage
def init_db():
    """Initialise la base de données."""
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")

# Initialiser la DB une seule fois
init_db()

# Exporter l'application Flask pour Vercel
# Vercel s'attend à un objet 'app' ou 'application'
application = app

# Pour le debug, on peut aussi exporter 'app'
__all__ = ['app', 'application']

