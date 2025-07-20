# Table Scripts
from app.config import Config
import psycopg2
from flask import jsonify

"""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    date_of_birth DATE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dialogs (
    id SERIAL PRIMARY KEY,
    conversation_id INT REFERENCES conversations(id) ON DELETE CASCADE,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    dialog_id INT REFERENCES dialogs(id) ON DELETE CASCADE,
    sender VARCHAR(50), -- 'user' or 'bot'
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Removed validate_account function as it uses Flask request
    
### Registration: 
# Check if username exist first, if yes: decline
# otherwise, insert into table users

def check_username(cur, username):
    cur.execute("SELECT username FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if user:
        return True
    return False

def user_registration(cur, username, hashed_password, email, avatar):
    if (check_username(cur, username)):
        return jsonify({'error': "Username exists"})
    else:
        cur.execute("""
            INSERT INTO users (username, password, email, avatar) 
            VALUES (%s, %s, %s, %s)
        """, (username, hashed_password, email, avatar))
        return jsonify({'success': "User registered successfully"})
    
def get_chat_history(cur, dialog_id, limit=50):
    cur.execute(""" 
        SELECT * FROM messages 
        WHERE dialog_id = %s
        ORDER BY timestamp ASC
        LIMIT %s
        """, (int(dialog_id), int(limit)))
    chat_history = cur.fetchall()
    return [{"role": "user" if row[2] == "user" else "assistant", "content": row[3], "timestamp": row[4].isoformat()} for row in chat_history]

# Removed create_conversations_table function as conversations table is not used

def create_dialogs_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS dialogs (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            system_prompt TEXT DEFAULT 'You are a knowledgeable and helpful chatbot specializing in Traditional Eastern Medicine.',
            model_config JSONB DEFAULT '{"model": "gemini-2.0-flash", "temperature": 0.7, "max_tokens": 1000}',
            max_chunks INTEGER DEFAULT 8,
            cosine_threshold FLOAT DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def create_messages_table():
    conn = get_connection()
    cur = conn.cursor()
    
    # Chỉ tạo table nếu chưa tồn tại, không drop table cũ
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            dialog_id INT REFERENCES dialogs(id) ON DELETE CASCADE,
            sender VARCHAR(50),
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Removed create_conversation function as conversations table is not used

def create_dialog(name=None, system_prompt=None, model_config=None, max_chunks=8, cosine_threshold=0.5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO dialogs (name, system_prompt, model_config, max_chunks, cosine_threshold)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, created_at, system_prompt, model_config, max_chunks, cosine_threshold;
    ''', (name, system_prompt, model_config, max_chunks, cosine_threshold))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {
        'id': row[0], 
        'name': row[1],
        'created_at': row[2],
        'system_prompt': row[3],
        'model_config': row[4],
        'max_chunks': row[5],
        'cosine_threshold': row[6]
    }

def add_message(dialog_id, sender, message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO messages (dialog_id, sender, message)
        VALUES (%s, %s, %s)
        RETURNING id, timestamp;
    ''', (dialog_id, sender, message))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {'id': row[0], 'timestamp': row[1]}

# Removed get_conversations_by_user function as conversations table is not used

def get_dialogs_by_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT d.id, d.name, d.created_at,
               COUNT(m.id) as message_count,
               MAX(m.timestamp) as last_message_at
        FROM dialogs d
        LEFT JOIN messages m ON d.id = m.dialog_id
        GROUP BY d.id, d.name, d.created_at
        ORDER BY d.created_at DESC
    ''')
    rows = cur.fetchall()
    dialogs = [
        {
            'id': row[0],
            'name': row[1],
            'created_at': row[2].isoformat() if row[2] else None,
            'message_count': row[3],
            'last_message_at': row[4].isoformat() if row[4] else None
        }
        for row in rows
    ]
    cur.close()
    conn.close()
    return dialogs

# Removed get_conversation_by_id function as conversations table is not used

def get_dialog_by_id(dialog_id, user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT d.id, d.name, d.created_at, d.system_prompt, d.model_config, d.max_chunks, d.cosine_threshold
        FROM dialogs d
        WHERE d.id = %s
    ''', (dialog_id,))
    row = cur.fetchone()
    if row:
        dialog = {
            'id': row[0],
            'name': row[1],
            'created_at': row[2].isoformat() if row[2] else None,
            'system_prompt': row[3],
            'model_config': row[4],
            'max_chunks': row[5],
            'cosine_threshold': row[6]
        }
    else:
        dialog = None
    cur.close()
    conn.close()
    return dialog

def update_dialog_config(dialog_id, user_id, system_prompt=None, model_config=None, max_chunks=None, cosine_threshold=None):
    conn = get_connection()
    cur = conn.cursor()
    
    # Build dynamic query based on what's provided
    updates = []
    params = []
    
    if system_prompt is not None:
        updates.append("system_prompt = %s")
        params.append(system_prompt)
    
    if model_config is not None:
        updates.append("model_config = %s")
        params.append(model_config)
    
    if max_chunks is not None:
        updates.append("max_chunks = %s")
        params.append(max_chunks)
    
    if cosine_threshold is not None:
        updates.append("cosine_threshold = %s")
        params.append(cosine_threshold)
    
    if not updates:
        return False
    
    params.append(dialog_id)
    
    query = f'''
        UPDATE dialogs 
        SET {', '.join(updates)}
        WHERE id = %s
    '''
    
    cur.execute(query, params)
    updated = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return updated

# Removed delete_conversation function as conversations table is not used

def delete_dialog(dialog_id, user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        DELETE FROM dialogs 
        WHERE id = %s
    ''', (dialog_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return deleted

def create_knowledge_base_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base_files (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            minio_path VARCHAR(255) NOT NULL,
            user_id INT REFERENCES users(id) ON DELETE CASCADE,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            num_chunks INT NOT NULL,
            file_size INT,
            description TEXT
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def insert_knowledge_base_file(filename, minio_path, num_chunks, file_size, description=None, user_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO knowledge_base_files (filename, minio_path, num_chunks, file_size, description, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, uploaded_at;
    ''', (filename, minio_path, num_chunks, file_size, description, user_id))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {'id': row[0], 'uploaded_at': row[1]}

def get_knowledge_base_files_by_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, filename, minio_path, num_chunks, file_size, uploaded_at
        FROM knowledge_base_files 
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
    ''', (user_id,))
    rows = cur.fetchall()
    files = [
        {
            'id': row[0],
            'filename': row[1],
            'minio_path': row[2],
            'num_chunks': row[3],
            'file_size': row[4],
            'uploaded_at': row[5].isoformat() if row[5] else None
        }
        for row in rows
    ]
    cur.close()
    conn.close()
    return files

def get_connection():
    return psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        dbname=Config.POSTGRES_DB,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD
    )
