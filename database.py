# Table Scripts
from flask import Flask, url_for, request, jsonify

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

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INT REFERENCES conversations(id) ON DELETE CASCADE,
    sender VARCHAR(50), -- 'user' or 'bot'
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def validate_account():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"isValid": False, "message": "Something is missing"}), 400
        
    except Exception as e:
        print("Error validating API key:", str(e))
        return jsonify({"isValid": False, "message": "Error validating API key"}), 500
    
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
    
def get_chat_history(cur, conversation_id, limit=10):
    cur.execute(""" 
        SELECT * FROM messages 
        WHERE conversation_id = %s
        LIMIT %s
        """, (int(conversation_id), int(limit)))
    chat_history = cur.fetchall()
    return [{"role": "user" if row[2] == "user" else "assistant", "content": row[3]} for row in chat_history]
