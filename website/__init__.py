from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager


db = SQLAlchemy()
DB_NAME = "blameeve.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'this is my secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://blameeverender_user:ArgFnIEejNZa0FJrDME8YbWxe63090tH@dpg-clvlk65a73kc73br508g-a.oregon-postgres.render.com/blameeverender'
    #postgres://blameeverender_user:ArgFnIEejNZa0FJrDME8YbWxe63090tH@dpg-clvlk65a73kc73br508g-a.oregon-postgres.render.com/blameeverender
    db.init_app(app)

    from .views import views
    from . auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note, Period, Symptoms, Reminders

    with app.app_context():
        db.create_all()


    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')




        