from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
import os
from datetime import timedelta

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
ma = Marshmallow()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config=None):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///neofi.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'jwt_dev_key'),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
        JWT_JSON_KEY_ENABLED=True,
        JWT_DECODE_SUBJECT_AS_STRING=False,  # Allow numeric subjects
    )
    
    if config:
        app.config.from_mapping(config)
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    CORS(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    with app.app_context():
        # Import models
        from app.models import user, event, permission, version
        
        # Import and register blueprints
        from app.routes.auth import auth_bp
        from app.routes.events import events_bp
        from app.routes.collaboration import collab_bp
        from app.routes.versioning import version_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(events_bp, url_prefix='/api/events')
        app.register_blueprint(collab_bp, url_prefix='/api/events')
        app.register_blueprint(version_bp, url_prefix='/api/events')
        
        # Create database tables
        db.create_all()
        
    return app 