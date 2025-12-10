FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet
COPY . .

# Créer le répertoire pour la base de données
RUN mkdir -p /app/instance

# Exposer le port Flask
EXPOSE 5000

# Variables d'environnement
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Commande de démarrage
CMD ["python", "app.py"]
