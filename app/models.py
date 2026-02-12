from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from datetime import datetime
class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    note = db.Column(db.Text)
    date = db.Column(db.String(20))
    image_url = db.Column(db.Text)
    # --- 以下の2行を追加 ---
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    # ----------------------
    shop_name = db.Column(db.String(255)) # pages.pyで使っているのでこれも追加推奨
    shop_url = db.Column(db.Text)        # pages.pyで使っているのでこれも追加推奨
    created_at = db.Column(db.DateTime, default=datetime.utcnow)