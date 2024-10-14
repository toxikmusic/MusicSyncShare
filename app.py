import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import boto3
from botocore.client import Config
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Setup secret key
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///songs.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# R2 bucket configuration
R2_ENDPOINT = os.environ.get("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")

# Initialize R2 client
r2 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4')
)

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/songs')
def get_songs():
    try:
        app.logger.debug("Attempting to list objects from R2 bucket")
        response = r2.list_objects_v2(Bucket=R2_BUCKET_NAME)
        app.logger.debug(f"R2 response: {response}")
        songs = []
        for obj in response.get('Contents', []):
            song_info = {
                'key': obj['Key'],
                'title': obj['Key'].split('/')[-1].rsplit('.', 1)[0],
                'artist': 'Unknown',  # You may want to extract this from metadata or filename
                'upload_date': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                'url': f"{R2_ENDPOINT}/{R2_BUCKET_NAME}/{obj['Key']}"
            }
            songs.append(song_info)
        app.logger.debug(f"Returning {len(songs)} songs")
        return jsonify(songs)
    except Exception as e:
        app.logger.error(f"Error in get_songs: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
