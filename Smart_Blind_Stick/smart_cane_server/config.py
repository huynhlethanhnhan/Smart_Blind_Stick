import os
from datetime import timedelta

class Config:
    # Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://username:password@localhost/smart_cane_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ThingSpeak config
    THINGSPEAK_CHANNEL_ID = 3226411
    THINGSPEAK_READ_API_KEY = 'YOUR_READ_API_KEY'
    THINGSPEAK_UPDATE_INTERVAL = 60  # seconds
    
    # WebSocket config
    WEBSOCKET_PORT = 5001
    
    # Upload config
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Debug config
    DEBUG = True
    TESTING = False