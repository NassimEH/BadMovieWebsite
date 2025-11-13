Membres : 
- Nassim EL HADDAD
- Rebecca RINGUET
- Lucas DREANO
- Chadi MANGLE

# CAHIER DES CHARGES : BadMovie
Ce projet est une application web permettant d’afficher, gérer et noter une liste de films.  
L’utilisateur peut rechercher, filtrer, marquer les films vus ou non vus, et donner ses propres avis.
 
## 1) Fonctionnalités principales

### Gestion des films

- Affichage d’une liste de films (titre, affiche, année, genre, note moyenne, etc.)
- Page de détails pour chaque film :
  - Synopsis / résumé  
  - Réalisateur, acteurs  
  - Catégories / genres  
  - Durée, date de sortie 


### Recherche et filtrage

- Recherche de films par titre  
- Filtres disponibles :
  - Par catégorie / genre (Action, Comédie, Drame, etc.)  
  - Par statut (vu / pas vu)  
  - Par appréciation (aimé / pas aimé)  
  - Par note

### Gestion de la liste personnelle
- Ajouter un film à sa liste personnelle  
- Supprimer un film de sa liste  
- Marquer un film comme :
  - Vu  
  - À voir  
- Possibilité de changer le statut (vu / non vu) directement depuis la liste

### Notation et commentaires

- Attribuer une note uniquement pour les films vus  
- Écrire un commentaire / avis personnel
- Modifier ou supprimer sa note ou son commentaire  

### Préférences et tri

- Filtrer les films :
  - Aimés  
  - Pas aimés 
- Trier la liste:
  - Par titre (A–Z / Z–A)  
  - Par année de sortie  
  - Par note  
  - Par date d’ajout  
  
---
## 2) Interface utilisateur

- Page d'accueil
- Page de connexion
- Page de films 
- Page de watchlist ( + filtres ) 
- ( Page de films aléatoires )
- ( Page de films recommandés ) 

---
## 3) Terminaisons

Pas besoin de faire des endpoints car on va utilisé Jinja pour rendre les templates. 

- GET - /home
- (GET,POST) - /register
- (GET, POST) - /login
- POST - /logout
- POST - /search/{movie_name} 
- GET - /movie/{movie_id}
- GET - /washlist/{user_id}

---
## 4) Modèle de données
```sql
CREATE TABLE users(
   ID_user INT,
   nom VARCHAR(50),
   mdp_haché VARCHAR(50),
   mail VARCHAR(50),
   PRIMARY KEY(ID_user)
);

CREATE TABLE films(
   ID_film INT,
   image VARCHAR(50),
   nom_film VARCHAR(50),
   année_film DATE,
   temps TIME,
   catégorie VARCHAR(50),
   PRIMARY KEY(ID_film)
);

CREATE TABLE commentaire(
   ID_user INT,
   ID_film INT,
   vu_user BOOLEAN,
   score_user TINYINT,
   avis_user VARCHAR(255),
   PRIMARY KEY(ID_user, ID_film),
   FOREIGN KEY(ID_user) REFERENCES users(ID_user),
   FOREIGN KEY(ID_film) REFERENCES films(ID_film)
);

---
## 5) Plan d'action
- Frontend (Nassim)
- Backend (Lucas)
- Base de données (Marceau)
- Intégration API TMDB (Chadi & Rebecca)
- Conteneurisation (Rebecca)
- Orchestration (Chadi)

##### _Projet personnel – Libre d’utilisation et d’adaptation._
