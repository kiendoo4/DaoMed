from flask import Blueprint, request, jsonify, session
import bcrypt
from db.database import (
    get_connection, create_conversations_table, create_dialogs_table, create_messages_table,
    create_conversation, create_dialog, add_message, get_conversations_by_user,
    get_dialogs_by_conversation, get_conversation_by_id, get_dialog_by_id,
    delete_conversation, delete_dialog, get_chat_history
)
from services.qdrant_service import QdrantService
from app.config import Config
import logging

chat_bp = Blueprint('chat', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo các bảng cần thiết
create_conversations_table()
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

# Conversation APIs
@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Lấy danh sách conversations của user"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        conversations = get_conversations_by_user(user_id)
        return jsonify({'conversations': conversations}), 200
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/conversations', methods=['POST'])
def create_new_conversation():
    """Tạo conversation mới"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    topic = data.get('topic', 'New Conversation')
    
    try:
        conversation = create_conversation(user_id, topic)
        return jsonify({
            'message': 'Conversation created successfully',
            'conversation': conversation
        }), 201
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Lấy thông tin conversation cụ thể"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        conversation = get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        return jsonify({'conversation': conversation}), 200
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation_endpoint(conversation_id):
    """Xóa conversation"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        deleted = delete_conversation(conversation_id, user_id)
        if not deleted:
            return jsonify({'error': 'Conversation not found'}), 404
        return jsonify({'message': 'Conversation deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

# Dialog APIs
@chat_bp.route('/dialogs', methods=['GET'])
def get_all_dialogs():
    """Lấy tất cả dialogs của user"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Lấy tất cả dialogs của user thông qua conversations
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT d.id, d.name, d.created_at, c.topic as conversation_topic,
                   COUNT(m.id) as message_count,
                   MAX(m.timestamp) as last_message_at
            FROM dialogs d
            JOIN conversations c ON d.conversation_id = c.id
            LEFT JOIN messages m ON d.id = m.dialog_id
            WHERE c.user_id = %s
            GROUP BY d.id, d.name, d.created_at, c.topic
            ORDER BY d.created_at DESC
        ''', (user_id,))
        rows = cur.fetchall()
        dialogs = [
            {
                'id': row[0],
                'name': row[1],
                'created_at': row[2].isoformat() if row[2] else None,
                'conversation_topic': row[3],
                'message_count': row[4],
                'last_message_at': row[5].isoformat() if row[5] else None
            }
            for row in rows
        ]
        cur.close()
        conn.close()
        
        return jsonify({'dialogs': dialogs}), 200
    except Exception as e:
        logger.error(f"Error getting all dialogs: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/dialogs', methods=['POST'])
def create_dialog_directly():
    """Tạo dialog trực tiếp (tự động tạo conversation nếu cần)"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    name = data.get('name', 'New Dialog')
    
    try:
        # Tạo conversation mặc định nếu chưa có
        conn = get_connection()
        cur = conn.cursor()
        
        # Kiểm tra xem có conversation mặc định chưa
        cur.execute("SELECT id FROM conversations WHERE user_id = %s AND topic = 'Default Conversation' LIMIT 1", (user_id,))
        result = cur.fetchone()
        
        if result:
            conversation_id = result[0]
        else:
            # Tạo conversation mặc định
            cur.execute("INSERT INTO conversations (user_id, topic) VALUES (%s, %s) RETURNING id", (user_id, 'Default Conversation'))
            conversation_id = cur.fetchone()[0]
        
        # Tạo dialog
        cur.execute("INSERT INTO dialogs (conversation_id, name) VALUES (%s, %s) RETURNING id, created_at", (conversation_id, name))
        row = cur.fetchone()
        dialog_id, created_at = row
        
        conn.commit()
        cur.close()
        conn.close()
        
        dialog = {
            'id': dialog_id,
            'name': name,
            'created_at': created_at.isoformat() if created_at else None,
            'conversation_id': conversation_id
        }
        
        return jsonify({
            'message': 'Dialog created successfully',
            'dialog': dialog
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating dialog directly: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/conversations/<int:conversation_id>/dialogs', methods=['GET'])
def get_dialogs(conversation_id):
    """Lấy danh sách dialogs của conversation"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Kiểm tra conversation thuộc về user
        conversation = get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        dialogs = get_dialogs_by_conversation(conversation_id)
        return jsonify({'dialogs': dialogs}), 200
    except Exception as e:
        logger.error(f"Error getting dialogs: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@chat_bp.route('/conversations/<int:conversation_id>/dialogs', methods=['POST'])
def create_new_dialog(conversation_id):
    """Tạo dialog mới trong conversation"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    name = data.get('name', 'New Dialog')
    
    try:
        # Kiểm tra conversation thuộc về user
        conversation = get_conversation_by_id(conversation_id, user_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        dialog = create_dialog(conversation_id, name)
        return jsonify({
            'message': 'Dialog created successfully',
            'dialog': dialog
        }), 201
    except Exception as e:
        logger.error(f"Error creating dialog: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

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
        bot_msg = add_message(dialog_id, 'bot', bot_response)
        
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