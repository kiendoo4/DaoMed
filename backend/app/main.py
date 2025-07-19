from flask import Flask, session, jsonify
from flask_cors import CORS
from .chat import chat_bp
from .kb import kb_bp
from .config import Config
from .dialog import dialog_bp

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Configure timeout for long operations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}}, supports_credentials=True)

# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(kb_bp, url_prefix='/api/kb')
app.register_blueprint(dialog_bp, url_prefix='/api/dialog')

@app.route("/test-cors", methods=["GET", "POST", "OPTIONS"])
def test_cors():
    return "CORS OK"

@app.route("/test-session", methods=["GET"])
def test_session():
    return jsonify({
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'session_data': dict(session)
    })