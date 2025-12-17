"""Contrôleur pour la gestion des utilisateurs."""
import re
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from extensions import db
import os
from werkzeug.utils import secure_filename
from flask import current_app


class UserController:
    """Contrôleur pour les opérations sur les utilisateurs."""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def allowed_file(filename):
        """Vérifie si le fichier a une extension autorisée."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in UserController.ALLOWED_EXTENSIONS
    
    @staticmethod
    def update_username(user_id, new_username):
        """Met à jour le nom d'utilisateur."""
        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur non trouvé"
        
        existing_user = User.query.filter_by(nom=new_username).first()
        if existing_user and existing_user.ID_user != user_id:
            return False, "Ce nom d'utilisateur est déjà pris"
        
        if len(new_username) < 4:
            return False, "Le nom d'utilisateur doit contenir au moins 4 caractères"
        
        try:
            user.nom = new_username
            db.session.commit()
            return True, "Nom d'utilisateur mis à jour avec succès"
        except Exception:
            db.session.rollback()
            return False, "Erreur lors de la mise à jour"
    
    @staticmethod
    def update_email(user_id, new_email):
        """Met à jour l'adresse email."""
        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur non trouvé"
        
        existing_user = User.query.filter_by(mail=new_email).first()
        if existing_user and existing_user.ID_user != user_id:
            return False, "Cet email est déjà utilisé"
        
        # Validation de l'email avec regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, new_email):
            return False, "Format d'email invalide"
        if len(new_email) < 4:
            return False, "L'email doit contenir au moins 4 caractères"
        
        try:
            user.mail = new_email
            db.session.commit()
            return True, "Email mis à jour avec succès"
        except Exception:
            db.session.rollback()
            return False, "Erreur lors de la mise à jour"
    
    @staticmethod
    def update_password(user_id, current_password, new_password):
        """Met à jour le mot de passe."""
        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur non trouvé"
        
        if not check_password_hash(user.password, current_password):
            return False, "Mot de passe actuel incorrect"
        
        if len(new_password) < 7:
            return False, "Le mot de passe doit contenir au moins 7 caractères"
        
        try:
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()
            return True, "Mot de passe mis à jour avec succès"
        except Exception:
            db.session.rollback()
            return False, "Erreur lors de la mise à jour"
    
    @staticmethod
    def update_profile_picture(user_id, filename):
        """Met à jour la photo de profil."""
        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur non trouvé"
        
        try:
            user.profile_picture = filename
            db.session.commit()
            return True, "Photo de profil mise à jour avec succès"
        except Exception:
            db.session.rollback()
            return False, "Erreur lors de la mise à jour"
    
    @staticmethod
    def save_profile_picture(file, user_id):
        """Sauvegarde la photo de profil et retourne le chemin."""
        if not file or not UserController.allowed_file(file.filename):
            return None, "Format de fichier non autorisé. Formats acceptés: PNG, JPG, JPEG, GIF, WEBP"
        
        if len(file.read()) > UserController.MAX_FILE_SIZE:
            file.seek(0)  # Réinitialiser le pointeur
            return None, "Le fichier est trop volumineux (maximum 5MB)"
        
        file.seek(0)
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
        os.makedirs(upload_folder, exist_ok=True)
        
        import time
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        timestamp = int(time.time() * 1000)
        new_filename = f"user_{user_id}_{timestamp}.{file_ext}"
        filepath = os.path.join(upload_folder, new_filename)
        
        file.save(filepath)
        
        return f"/static/uploads/profiles/{new_filename}", None

