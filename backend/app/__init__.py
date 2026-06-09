from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "100 per hour"])

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    limiter.init_app(app)
    CORS(app, origins=app.config['ALLOWED_ORIGINS'], supports_credentials=True)

    # Create dynamic asset directories if they don't exist
    import os
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, '..', 'uploads'), exist_ok=True)

    # Register blueprints
    from app.routes.auth       import auth_bp
    from app.routes.meetings   import meetings_bp
    from app.routes.transcript import transcript_bp
    from app.routes.reports    import reports_bp
    from app.routes.tasks      import tasks_bp
    from app.routes.dashboard  import dashboard_bp
    from app.routes.ai_chat    import ai_chat_bp

    app.register_blueprint(auth_bp,       url_prefix='/api/auth')
    app.register_blueprint(meetings_bp,   url_prefix='/api/meetings')
    app.register_blueprint(transcript_bp, url_prefix='/api/transcript')
    app.register_blueprint(reports_bp,    url_prefix='/api/reports')
    app.register_blueprint(tasks_bp,      url_prefix='/api/tasks')
    app.register_blueprint(dashboard_bp,  url_prefix='/api/dashboard')
    app.register_blueprint(ai_chat_bp,     url_prefix='/api/ai')

    with app.app_context():
        db.create_all()

    # Serve uploaded static reports locally
    @app.route('/uploads/<filename>')
    def serve_upload(filename):
        from flask import send_from_directory
        return send_from_directory(os.path.join(app.root_path, '..', 'uploads'), filename)

    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'service': 'SmartMeet AI Backend'}

    return app

