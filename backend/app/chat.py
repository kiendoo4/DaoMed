from flask import Blueprint, request, jsonify, session
import bcrypt
from db.database import (
    get_connection, create_dialogs_table, create_messages_table,
    create_dialog, add_message, get_dialogs_by_user, get_dialog_by_id,
    delete_dialog, get_chat_history
)
from services.qdrant_service import QdrantService
from app.config import Config
import logging

chat_bp = Blueprint('chat', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo các bảng cần thiết
create_dialogs_table()
create_messages_table()

def require_auth():
    """Kiểm tra user đã đăng nhập chưa"""
    if 'user_id' not in session:
        return False, 'User not authenticated'
    return True, session['user_id']

@chat_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({'error': 'Sai tài khoản hoặc mật khẩu'}), 401
    user_id, hashed = row
    if not bcrypt.checkpw(password.encode(), hashed.encode() if isinstance(hashed, str) else hashed):
        cur.close()
        conn.close()
        return jsonify({'error': 'Sai tài khoản hoặc mật khẩu'}), 401
    session['user_id'] = user_id
    session['username'] = username
    cur.close()
    conn.close()
    return jsonify({'message': 'Đăng nhập thành công!', 'username': username}), 200

@chat_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': 'User đã tồn tại'}), 409
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed.decode()))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Đăng ký thành công!'}), 200

@chat_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Đăng xuất thành công!'}), 200

# Removed conversation APIs as conversations table is not used

# Dialog APIs
@chat_bp.route('/dialogs', methods=['GET'])
def get_all_dialogs():
    """Lấy tất cả dialogs"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        dialogs = get_dialogs_by_user(user_id)
        return jsonify({'dialogs': dialogs}), 200
    except Exception as e:
        logger.error(f"Error getting all dialogs: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/dialogs', methods=['POST'])
def create_dialog_directly():
    """Tạo dialog trực tiếp"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    name = data.get('name', 'New Dialog')
    
    try:
        dialog = create_dialog(name)
        
        # Tạo dialog object với thông tin đầy đủ như khi lấy danh sách
        dialog_with_stats = {
            'id': dialog['id'],
            'name': dialog['name'],
            'created_at': dialog['created_at'],
            'message_count': 0,  # Dialog mới tạo nên chưa có messages
            'last_message_at': None
        }
        
        return jsonify({
            'message': 'Dialog created successfully',
            'dialog': dialog_with_stats
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating dialog directly: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

# Removed conversation-related dialog APIs as conversations table is not used

@chat_bp.route('/dialogs/<int:dialog_id>', methods=['GET'])
def get_dialog(dialog_id):
    """Lấy thông tin dialog cụ thể"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        dialog = get_dialog_by_id(dialog_id, user_id)
        if not dialog:
            return jsonify({'error': 'Dialog not found'}), 404
        return jsonify({'dialog': dialog}), 200
    except Exception as e:
        logger.error(f"Error getting dialog: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/dialogs/<int:dialog_id>', methods=['DELETE'])
def delete_dialog_endpoint(dialog_id):
    """Xóa dialog"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        deleted = delete_dialog(dialog_id, user_id)
        if not deleted:
            return jsonify({'error': 'Dialog not found'}), 404
        return jsonify({'message': 'Dialog deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting dialog: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

# Message APIs
@chat_bp.route('/dialogs/<int:dialog_id>/messages', methods=['GET'])
def get_messages(dialog_id):
    """Lấy lịch sử messages của dialog"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Kiểm tra dialog thuộc về user
        dialog = get_dialog_by_id(dialog_id, user_id)
        if not dialog:
            return jsonify({'error': 'Dialog not found'}), 404
        
        conn = get_connection()
        cur = conn.cursor()
        messages = get_chat_history(cur, dialog_id)
        cur.close()
        conn.close()
        
        return jsonify({'messages': messages}), 200
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/dialogs/<int:dialog_id>/messages', methods=['POST'])
def send_message(dialog_id):
    """Gửi message trong dialog và nhận phản hồi từ knowledge base"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Kiểm tra dialog thuộc về user
        dialog = get_dialog_by_id(dialog_id, user_id)
        if not dialog:
            return jsonify({'error': 'Dialog not found'}), 404
        
        # Lưu message của user
        user_msg = add_message(dialog_id, 'user', message)
        
        # Tìm kiếm trong knowledge base
        qdrant_service = QdrantService(Config)
        success, search_results = qdrant_service.search_chunks(message, user_id, top_k=3, score_threshold=0.5)
        
        if success and search_results:
            # Tạo phản hồi dựa trên kết quả tìm kiếm
            context = "\n".join([result['text'] for result in search_results[:2]])
            bot_response = f"Dựa trên knowledge base của bạn, tôi tìm thấy thông tin liên quan:\n\n{context}\n\nBạn có cần thêm thông tin gì không?"
        else:
            bot_response = "Tôi không tìm thấy thông tin liên quan trong knowledge base. Bạn có thể thử câu hỏi khác hoặc upload thêm tài liệu vào knowledge base."
        
        # Lưu phản hồi của bot
        bot_msg = add_message(dialog_id, 'assistant', bot_response)
        
        return jsonify({
            'message': 'Message sent successfully',
            'user_message': {
                'id': user_msg['id'],
                'content': message,
                'timestamp': user_msg['timestamp'].isoformat()
            },
            'bot_response': {
                'id': bot_msg['id'],
                'content': bot_response,
                'timestamp': bot_msg['timestamp'].isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

# Legacy endpoints for backward compatibility
@chat_bp.route('/message', methods=['POST'])
def send_message_legacy():
    return jsonify({'error': 'Use /dialogs/{dialog_id}/messages instead'}), 400

@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages_legacy(conversation_id):
    return jsonify({'error': 'Use /dialogs/{dialog_id}/messages instead'}), 400

@chat_bp.route('/send', methods=['POST'])
def chat_send():
    return jsonify({'error': 'Use /dialogs/{dialog_id}/messages instead'}), 400

@chat_bp.route('/history', methods=['GET'])
def chat_history():
    return jsonify({'error': 'Use /dialogs/{dialog_id}/messages instead'}), 400 