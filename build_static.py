"""Script de build pour copier les fichiers statiques vers public/ pour Vercel."""
import os
import shutil
from pathlib import Path

def copy_static_to_public():
    """Copie le dossier static/ vers public/static/ pour Vercel."""
    source_dir = Path('static')
    dest_dir = Path('public/static')
    
    if not source_dir.exists():
        print(f"Erreur: Le dossier {source_dir} n'existe pas")
        return False
    
    # Créer le dossier public s'il n'existe pas
    dest_dir.parent.mkdir(exist_ok=True)
    
    # Supprimer l'ancien dossier public/static s'il existe
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    
    # Copier le dossier static vers public/static
    shutil.copytree(source_dir, dest_dir)
    print(f"✓ Fichiers statiques copiés de {source_dir} vers {dest_dir}")
    return True

if __name__ == '__main__':
    copy_static_to_public()

