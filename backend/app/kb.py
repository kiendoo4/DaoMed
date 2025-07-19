from flask import Blueprint, request, jsonify, session
from db.database import get_connection, create_knowledge_base_table, insert_knowledge_base_file, get_knowledge_base_files_by_user
from app.config import Config
from services.minio_service import MinioService
from services.qdrant_service import QdrantService
import logging
import pandas as pd
import os
import json
from werkzeug.utils import secure_filename
from io import BytesIO

kb_bp = Blueprint('kb', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo bảng knowledge_base_files nếu chưa có
create_knowledge_base_table()

def require_auth():
    """Kiểm tra user đã đăng nhập chưa"""
    if 'user_id' not in session:
        return False, 'User not authenticated'
    return True, session['user_id']

@kb_bp.route('/list', methods=['GET'])
def list_kb():
    logger.info("list_kb endpoint called")
    
    # Kiểm tra authentication
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        files = get_knowledge_base_files_by_user(user_id)
        logger.info(f"Found {len(files)} knowledge base files for user {user_id}")
        return jsonify({'files': files}), 200
    except Exception as e:
        logger.error(f"Error in list_kb: {str(e)}")
        return jsonify({'error': 'Database error'}), 500

@kb_bp.route('/upload', methods=['POST'])
def upload_kb():
    # Kiểm tra authentication
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    
    # Hỗ trợ cả Excel và CSV
    if ext not in ['.xlsx', '.xls', '.csv']:
        return jsonify({'error': 'Only Excel (.xlsx, .xls) and CSV (.csv) files are allowed'}), 400

    # Lưu file vào MinIO
    minio_service = MinioService(Config)
    
    # Đọc toàn bộ file content trước
    file_content = file.read()
    
    # Tính file size chính xác
    file_size = len(file_content)
    
    # Upload to MinIO
    file_stream = BytesIO(file_content)
    success, msg = minio_service.upload_file(file_stream, filename, file.mimetype)
    if not success:
        return jsonify({'error': f'Failed to upload to MinIO: {msg}'}), 500

    # Đọc file và thực hiện chunking
    try:
        file_stream = BytesIO(file_content)
        if ext == '.csv':
            # Đọc CSV với TAB delimiter như yêu cầu
            df = pd.read_csv(file_stream, encoding='utf-8', sep='\t')
        elif ext == '.xlsx':
            # Đọc XLSX với openpyxl engine
            df = pd.read_excel(file_stream, engine='openpyxl')
        else:
            # Đọc XLS với xlrd engine
            df = pd.read_excel(file_stream, engine='xlrd')
        
        logger.info(f"Successfully read file: {filename}, shape: {df.shape}")
        
        # Thực hiện chunking
        chunks = perform_chunking(df)
        num_chunks = len(chunks)
        
        logger.info(f"Created {num_chunks} chunks from file {filename}")
        
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 400

    minio_path = filename
    
    # Lưu chunks vào MinIO
    try:
        chunks_filename = f"{os.path.splitext(filename)[0]}_chunks.json"
        chunks_data = {
            'filename': filename,
            'total_chunks': num_chunks,
            'chunks': chunks
        }
        
        chunks_json = json.dumps(chunks_data, indent=2, ensure_ascii=False)
        chunks_stream = BytesIO(chunks_json.encode('utf-8'))
        
        success, msg = minio_service.upload_file(chunks_stream, chunks_filename, 'application/json')
        if not success:
            logger.warning(f"Failed to save chunks to MinIO: {msg}")
        
        logger.info(f"Successfully saved chunks to MinIO: {chunks_filename}")
        
    except Exception as e:
        logger.error(f"Error saving chunks to MinIO: {str(e)}")

    # Lưu metadata vào DB trước
    try:
        meta = insert_knowledge_base_file(
            filename=filename,
            minio_path=minio_path,
            num_chunks=num_chunks,
            file_size=file_size,
            description=None,
            user_id=user_id
        )
        
        logger.info(f"Successfully saved metadata for {filename}")
        
    except Exception as e:
        logger.error(f"Error saving metadata: {str(e)}")
        return jsonify({'error': f'Failed to save metadata: {str(e)}'}), 500

    # Vectorize chunks và lưu vào Qdrant
    try:
        qdrant_service = QdrantService(Config)
        success, msg = qdrant_service.vectorize_chunks(chunks, meta['id'], user_id)
        if not success:
            logger.warning(f"Failed to vectorize chunks: {msg}")
        else:
            logger.info(f"Successfully vectorized chunks: {msg}")
    except Exception as e:
        logger.error(f"Error vectorizing chunks: {str(e)}")
        # Không fail upload nếu vectorize thất bại

    return jsonify({
        'message': 'File uploaded and processed successfully',
        'filename': filename,
        'num_chunks': num_chunks,
        'file_size': file_size,
        'metadata': meta
    }), 200

def perform_chunking(df):
    """
    Thực hiện chunking dữ liệu từ DataFrame theo từng row
    Mỗi row sẽ trở thành một chunk riêng biệt
    """
    chunks = []
    
    # Lấy headers (column names)
    headers = df.columns.tolist()
    
    # Xử lý từng row trong DataFrame
    for index, row in df.iterrows():
        # Tạo chunk text từ header và data của row
        chunk_parts = []
        
        # Thêm headers và values
        for header, value in zip(headers, row):
            # Xử lý giá trị NaN
            if pd.isna(value):
                value = ""
            else:
                value = str(value).strip()
            
            chunk_parts.append(f"{header}: {value}")
        
        # Tạo chunk text
        chunk_text = " | ".join(chunk_parts)
        
        chunks.append({
            'id': index,
            'text': chunk_text,
            'row_index': index,
            'headers': headers
        })
    
    return chunks

@kb_bp.route('/<int:kb_id>', methods=['DELETE'])
def delete_kb(kb_id):
    # Kiểm tra authentication
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        logger.info(f"Deleting knowledge base with ID: {kb_id} by user {user_id}")
        
        # Lấy thông tin file từ database và kiểm tra ownership
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT filename, minio_path FROM knowledge_base_files WHERE id = %s AND user_id = %s", (kb_id, user_id))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': 'Knowledge base not found or access denied'}), 404
        
        filename, minio_path = result
        
        # Xóa file từ MinIO
        minio_service = MinioService(Config)
        minio_service.delete_file(minio_path)
        
        # Xóa chunks khỏi Qdrant
        try:
            qdrant_service = QdrantService(Config)
            qdrant_service.delete_kb_chunks(kb_id)
        except Exception as e:
            logger.warning(f"Failed to delete chunks from Qdrant: {str(e)}")
        
        # Xóa record từ database
        cur.execute("DELETE FROM knowledge_base_files WHERE id = %s", (kb_id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        logger.info(f"Successfully deleted knowledge base: {filename}")
        return jsonify({'message': f'Knowledge base {filename} deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting knowledge base {kb_id}: {str(e)}")
        return jsonify({'error': f'Failed to delete knowledge base: {str(e)}'}), 500

@kb_bp.route('/<int:kb_id>/chunks', methods=['GET'])
def get_kb_chunks(kb_id):
    """
    Lấy chunks của một knowledge base từ MinIO với pagination
    """
    # Kiểm tra authentication
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Lấy pagination parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 100, type=int)
    
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 1000:
        page_size = 100
    
    try:
        logger.info(f"Getting chunks for knowledge base ID: {kb_id} by user {user_id}, page {page}, size {page_size}")
        
        # Lấy thông tin file từ database và kiểm tra ownership
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT filename, minio_path FROM knowledge_base_files WHERE id = %s AND user_id = %s", (kb_id, user_id))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': 'Knowledge base not found or access denied'}), 404
        
        filename, minio_path = result
        
        # Tạo tên file chunks
        chunks_filename = f"{os.path.splitext(filename)[0]}_chunks.json"
        
        # Đọc chunks từ MinIO
        minio_service = MinioService(Config)
        chunks_file = minio_service.get_file(chunks_filename)
        
        if not chunks_file:
            return jsonify({'error': 'Chunks file not found in MinIO'}), 404
        
        # Parse JSON chunks
        chunks_data = json.loads(chunks_file.read().decode('utf-8'))
        all_chunks = chunks_data.get('chunks', [])
        total_chunks = len(all_chunks)
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_chunks = all_chunks[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total_chunks + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        logger.info(f"Loaded {len(paginated_chunks)} chunks (page {page}/{total_pages}) for {filename}")
        
        return jsonify({
            'filename': filename,
            'total_chunks': total_chunks,
            'chunks': paginated_chunks,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev,
                'start_idx': start_idx + 1,
                'end_idx': min(end_idx, total_chunks)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting chunks for KB {kb_id}: {str(e)}")
        return jsonify({'error': f'Failed to get chunks: {str(e)}'}), 500

@kb_bp.route('/<int:kb_id>/chunks/<int:chunk_id>/vector', methods=['GET'])
def get_chunk_vector(kb_id, chunk_id):
    """
    Lấy vector của một chunk cụ thể từ Qdrant
    """
    # Kiểm tra authentication
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        logger.info(f"Getting vector for chunk {chunk_id} in KB {kb_id} by user {user_id}")
        
        # Kiểm tra ownership của KB
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT filename FROM knowledge_base_files WHERE id = %s AND user_id = %s", (kb_id, user_id))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': 'Knowledge base not found or access denied'}), 404
        
        # Lấy vector từ Qdrant
        qdrant_service = QdrantService(Config)
        success, vector_data = qdrant_service.get_chunk_vector(kb_id, chunk_id)
        
        if not success:
            return jsonify({'error': f'Failed to get vector: {vector_data}'}), 500
        
        return jsonify({
            'kb_id': kb_id,
            'chunk_id': chunk_id,
            'vector': vector_data['vector'],
            'vector_size': len(vector_data['vector']),
            'metadata': vector_data['metadata']
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting vector for chunk {chunk_id} in KB {kb_id}: {str(e)}")
        return jsonify({'error': f'Failed to get vector: {str(e)}'}), 500

@kb_bp.route('/search', methods=['POST'])
def search_chunks():
    """
    Tìm kiếm chunks liên quan đến query (internal use only)
    """
    # Kiểm tra authentication
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    query = data.get('query', '').strip()
    top_k = data.get('top_k', 5)
    score_threshold = data.get('score_threshold', 0.5)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        qdrant_service = QdrantService(Config)
        success, results = qdrant_service.search_chunks(query, user_id, top_k, score_threshold)
        
        if not success:
            return jsonify({'error': f'Search failed: {results}'}), 500
        
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching chunks: {str(e)}")
        return jsonify({'error': f'Search error: {str(e)}'}), 500 