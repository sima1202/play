from dotenv import load_dotenv
load_dotenv()   # ← これが無いと一生 None

from flask import Flask
from app.config import Config
from app.models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)  
    with app.app_context():
        db.create_all() 
    from app.routes.pages import pages
    app.register_blueprint(pages)

    return app
