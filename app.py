import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import boto3
from botocore.client import Config
import logging
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid

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

# Log R2 configuration (without exposing sensitive information)
app.logger.debug(f"R2_ENDPOINT: {R2_ENDPOINT}")
app.logger.debug(f"R2_ACCESS_KEY_ID: {'Set' if R2_ACCESS_KEY_ID else 'Not set'}")
app.logger.debug(f"R2_SECRET_ACCESS_KEY: {'Set' if R2_SECRET_ACCESS_KEY else 'Not set'}")
app.logger.debug(f"R2_BUCKET_NAME: {R2_BUCKET_NAME}")

# Initialize R2 client
r2 = None
if all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME]):
    try:
        r2 = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4')
        )
        app.logger.debug("R2 client initialized successfully")
        
        # Check if the bucket exists, if not, create it
        try:
            r2.head_bucket(Bucket=R2_BUCKET_NAME)
            app.logger.info(f"Bucket {R2_BUCKET_NAME} exists.")
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                app.logger.info(f"Bucket {R2_BUCKET_NAME} does not exist. Creating it now.")
                try:
                    r2.create_bucket(Bucket=R2_BUCKET_NAME)
                    app.logger.info(f"Bucket {R2_BUCKET_NAME} created successfully.")
                except ClientError as create_error:
                    app.logger.error(f"Failed to create bucket: {str(create_error)}")
            elif error_code == 403:
                app.logger.error(f"No permission to access bucket {R2_BUCKET_NAME}")
            else:
                app.logger.error(f"Error checking bucket: {str(e)}")
    except Exception as e:
        app.logger.error(f"Failed to initialize R2 client: {str(e)}")
else:
    app.logger.error("One or more required R2 environment variables are not set")

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/songs')
def get_songs():
    if r2 is None:
        app.logger.error("R2 client is not initialized")
        return jsonify([]), 200  # Return empty list instead of error

    if not R2_BUCKET_NAME:
        app.logger.error("R2_BUCKET_NAME is not set")
        return jsonify([]), 200  # Return empty list instead of error

    try:
        app.logger.debug(f"Attempting to list objects from R2 bucket: {R2_BUCKET_NAME}")
        response = r2.list_objects_v2(Bucket=R2_BUCKET_NAME)
        app.logger.debug(f"R2 response: {response}")
        
        if 'Contents' not in response:
            app.logger.warning(f"No objects found in the bucket: {R2_BUCKET_NAME}")
            return jsonify([])

        songs = []
        for obj in response['Contents']:
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
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        app.logger.error(f"ClientError in get_songs: {error_code} - {error_message}")
        if error_code in ['NoSuchBucket', 'AccessDenied']:
            return jsonify([]), 200  # Return empty list for these specific errors
        return jsonify({'error': f"{error_code}: {error_message}"}), 500
    except Exception as e:
        app.logger.error(f"Error in get_songs: {str(e)}")
        return jsonify([]), 200  # Return empty list for any other exceptions

@app.route('/api/upload', methods=['POST'])
def upload_song():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        try:
            r2.upload_fileobj(file, R2_BUCKET_NAME, unique_filename)
            return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename}), 200
        except ClientError as e:
            app.logger.error(f"Error uploading file: {str(e)}")
            return jsonify({'error': 'Failed to upload file'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
