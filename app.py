from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from routes.auth_routes import auth_bp
from routes.movie_routes import movie_bp
from routes.watchlist_routes import watchlist_bp

app.register_blueprint(auth_bp) 
app.register_blueprint(movie_bp)
app.register_blueprint(watchlist_bp)

@app.route('/')
def index():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
