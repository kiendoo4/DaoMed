from flask import Flask, session, jsonify
from flask_cors import CORS
from flask_session import Session
from sqlalchemy import create_engine
from .chat import chat_bp
from .kb import kb_bp
from .config import Config
from .dialog import dialog_bp

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Cấu hình SQLAlchemy cho Flask-Session
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cấu hình session lưu vào PostgreSQL để không bị mất khi restart
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = create_engine(
    f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24h

Session(app)

# Configure timeout for long operations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(kb_bp, url_prefix='/api/kb')
app.register_blueprint(dialog_bp, url_prefix='/api/dialog')

# Enable CORS
CORS(app, supports_credentials=True, origins=['http://localhost:3000'])

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Backend is running'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)