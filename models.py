from app import db

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False)
    file_key = db.Column(db.String(200), nullable=False)
