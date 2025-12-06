"""Routes pour les paramètres utilisateur."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from controllers.user_controller import UserController
import os

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/')
@login_required
def settings():
    """Page de paramètres utilisateur."""
    return render_template('settings.html')


@settings_bp.route('/update-username', methods=['POST'])
@login_required
def update_username():
    """API pour mettre à jour le nom d'utilisateur."""
    data = request.get_json()
    new_username = data.get('username', '').strip()
    
    if not new_username:
        return jsonify({"success": False, "message": "Le nom d'utilisateur ne peut pas être vide"}), 400
    
    success, message = UserController.update_username(current_user.ID_user, new_username)
    
    if success:
        return jsonify({"success": True, "message": message, "username": new_username})
    else:
        return jsonify({"success": False, "message": message}), 400


@settings_bp.route('/update-email', methods=['POST'])
@login_required
def update_email():
    """API pour mettre à jour l'email."""
    data = request.get_json()
    new_email = data.get('email', '').strip()
    
    if not new_email:
        return jsonify({"success": False, "message": "L'email ne peut pas être vide"}), 400
    
    success, message = UserController.update_email(current_user.ID_user, new_email)
    
    if success:
        return jsonify({"success": True, "message": message, "email": new_email})
    else:
        return jsonify({"success": False, "message": message}), 400


@settings_bp.route('/update-password', methods=['POST'])
@login_required
def update_password():
    """API pour mettre à jour le mot de passe."""
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({"success": False, "message": "Les mots de passe ne peuvent pas être vides"}), 400
    
    success, message = UserController.update_password(
        current_user.ID_user, 
        current_password, 
        new_password
    )
    
    if success:
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "message": message}), 400


@settings_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """API pour uploader une photo de profil."""
    if 'profile_picture' not in request.files:
        return jsonify({"success": False, "message": "Aucun fichier fourni"}), 400
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "Aucun fichier sélectionné"}), 400
    
    filepath, error = UserController.save_profile_picture(file, current_user.ID_user)
    
    if error:
        return jsonify({"success": False, "message": error}), 400
    
    # Mettre à jour le chemin dans la base de données
    success, message = UserController.update_profile_picture(current_user.ID_user, filepath)
    
    if success:
        return jsonify({"success": True, "message": message, "profile_picture_url": filepath})
    else:
        return jsonify({"success": False, "message": message}), 400

