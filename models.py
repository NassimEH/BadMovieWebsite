from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    ID_user = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    mail = db.Column(db.String(50), unique=True, nullable=False)
    commentaires = db.relationship('Commentaire', backref='user', lazy=True)

class Film(db.Model):
    __tablename__ = 'movies'
    ID_film = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200))
    name_movie = db.Column(db.String(100), nullable=False)
    year_movie = db.Column(db.Date)
    duration = db.Column(db.Time)
    category = db.Column(db.String(50))
    commentaires = db.relationship('Commentaire', backref='film', lazy=True)

class Commentaire(db.Model):
    __tablename__ = 'commentaires'
    ID_user = db.Column(db.Integer, db.ForeignKey('users.ID_user'), primary_key=True)
    ID_film = db.Column(db.Integer, db.ForeignKey('films.ID_film'), primary_key=True)
    watched = db.Column(db.Boolean, default=False)
    score_user = db.Column(db.Integer)
    avis_user = db.Column(db.String(255))
