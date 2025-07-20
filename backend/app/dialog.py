# DoctorQA/backend/app/dialog.py
from flask import Blueprint, request, jsonify, session
from db.database import (
    get_dialog_by_id, add_message, get_chat_history, get_connection, update_dialog_config
)
from services.rag_service import RAGService
from services.qdrant_service import QdrantService
from app.config import Config
import logging
import json

dialog_bp = Blueprint('dialog', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def require_auth():
    """Kiểm tra user đã đăng nhập chưa"""
    if 'user_id' not in session:
        return False, 'User not authenticated'
    return True, session['user_id']

@dialog_bp.route('/<int:dialog_id>/chat', methods=['POST'])
def chat_with_kb(dialog_id):
    """
    Chat với knowledge base trong dialog cụ thể
    Sử dụng toàn bộ knowledge base của user
    """
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Kiểm tra dialog thuộc về user và lấy config
        dialog = get_dialog_by_id(dialog_id, user_id)
        if not dialog:
            return jsonify({'error': 'Dialog not found'}), 404
        
        # Lưu message của user
        user_msg = add_message(dialog_id, 'user', message)
        
        # Sử dụng RAG service với dialog config
        rag_service = RAGService(
            Config, 
            system_prompt=dialog.get('system_prompt'),
            model_config=dialog.get('model_config'),
            max_chunks=dialog.get('max_chunks', 8),
            cosine_threshold=dialog.get('cosine_threshold', 0.5)
        )
        rag_result = rag_service.chat_with_rag(message, user_id)
        
        bot_response = rag_result['response']
        
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
            },
            'search_results_count': rag_result.get('search_results_count', 0),
            'sources': rag_result.get('sources', []),
            'rag_details': {
                'query': message,
                'chunks_used': rag_result.get('search_results', []),
                'context_used': rag_result.get('context_used', ''),
                'used_rag': True  # RAG luôn được sử dụng, chỉ là có thể không tìm thấy chunks
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in chat_with_kb: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@dialog_bp.route('/<int:dialog_id>/config', methods=['PUT'])
def update_dialog_config_endpoint(dialog_id):
    """
    Cập nhật system prompt, model config, max_chunks và cosine_threshold cho dialog
    """
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    system_prompt = data.get('system_prompt')
    model_config = data.get('model_config')
    max_chunks = data.get('max_chunks')
    cosine_threshold = data.get('cosine_threshold')
    
    if all(v is None for v in [system_prompt, model_config, max_chunks, cosine_threshold]):
        return jsonify({'error': 'At least one configuration parameter must be provided'}), 400
    
    try:
        # Kiểm tra dialog thuộc về user
        dialog = get_dialog_by_id(dialog_id, user_id)
        if not dialog:
            return jsonify({'error': 'Dialog not found'}), 404
        
        # Validate max_chunks
        if max_chunks is not None:
            try:
                max_chunks = int(max_chunks)
                if max_chunks < 1 or max_chunks > 30:
                    return jsonify({'error': 'max_chunks must be between 1 and 30'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'max_chunks must be a valid integer'}), 400
        
        # Validate cosine_threshold
        if cosine_threshold is not None:
            try:
                cosine_threshold = float(cosine_threshold)
                if cosine_threshold < 0.0 or cosine_threshold > 1.0:
                    return jsonify({'error': 'cosine_threshold must be between 0.0 and 1.0'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'cosine_threshold must be a valid float'}), 400
        
        # Validate model_config temperature if provided
        if model_config is not None:
            try:
                if isinstance(model_config, str):
                    model_config_dict = json.loads(model_config)
                else:
                    model_config_dict = model_config
                
                if 'temperature' in model_config_dict:
                    temp = float(model_config_dict['temperature'])
                    if temp < 0.0 or temp > 1.0:
                        return jsonify({'error': 'temperature must be between 0.0 and 1.0'}), 400
            except (ValueError, TypeError, json.JSONDecodeError):
                return jsonify({'error': 'Invalid model_config format'}), 400
        
        # Convert model_config dict to JSON string if provided
        if model_config is not None:
            model_config = json.dumps(model_config)
        
        # Update config
        success = update_dialog_config(dialog_id, user_id, system_prompt, model_config, max_chunks, cosine_threshold)
        
        if success:
            return jsonify({
                'message': 'Dialog configuration updated successfully',
                'dialog_id': dialog_id
            }), 200
        else:
            return jsonify({'error': 'Failed to update dialog configuration'}), 500
            
    except Exception as e:
        logger.error(f"Error updating dialog config: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@dialog_bp.route('/<int:dialog_id>', methods=['GET'])
def get_dialog(dialog_id):
    """Lấy thông tin dialog và config"""
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Kiểm tra dialog thuộc về user
        dialog = get_dialog_by_id(dialog_id, user_id)
        if not dialog:
            return jsonify({'error': 'Dialog not found'}), 404
        
        return jsonify(dialog), 200
    except Exception as e:
        logger.error(f"Error getting dialog: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@dialog_bp.route('/<int:dialog_id>/messages', methods=['GET'])
def get_dialog_messages(dialog_id):
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
        logger.error(f"Error getting dialog messages: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@dialog_bp.route('/<int:dialog_id>/search', methods=['POST'])
def search_in_dialog(dialog_id):
    """
    Tìm kiếm trong knowledge base từ dialog
    """
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    query = data.get('query', '').strip()
    top_k = data.get('top_k', 5)
    score_threshold = data.get('score_threshold', 0.3)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        # Kiểm tra dialog thuộc về user
        dialog = get_dialog_by_id(dialog_id, user_id)
        if not dialog:
            return jsonify({'error': 'Dialog not found'}), 404
        
        # Tìm kiếm trong knowledge base
        qdrant_service = QdrantService(Config)
        success, results = qdrant_service.search_chunks(query, user_id, top_k, score_threshold)
        
        if not success:
            return jsonify({'error': f'Search failed: {results}'}), 500
        
        return jsonify({
            'dialog_id': dialog_id,
            'query': query,
            'results': results,
            'total_found': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching in dialog: {str(e)}")
        return jsonify({'error': f'Search error: {str(e)}'}), 500
