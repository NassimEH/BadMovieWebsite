"""Contrôleur pour l'authentification."""
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from extensions import db


class AuthController:
    """Contrôleur pour les opérations d'authentification."""
    
    @staticmethod
    def register_user(nom, email, password):
        """Enregistre un nouvel utilisateur."""
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(mail=email).first():
            return None, "Cet email est déjà utilisé"
        
        # Créer le nouvel utilisateur
        hashed_password = generate_password_hash(password)
        user = User(nom=nom, mail=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return user, None
    
    @staticmethod
    def authenticate_user(email, password):
        """Authentifie un utilisateur."""
        user = User.query.filter_by(mail=email).first()
        if user and check_password_hash(user.password, password):
            return user
        return None

