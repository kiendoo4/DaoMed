from app.config import Config
import psycopg2

def init_database():
    """Khởi tạo database với tất cả các bảng cần thiết"""
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        dbname=Config.POSTGRES_DB,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD
    )
    
    cur = conn.cursor()
    
    # Tạo bảng users
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100),
            date_of_birth DATE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Removed conversations table as it's not used
    
    # Tạo bảng dialogs
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
    
    # Tạo bảng messages
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            dialog_id INT REFERENCES dialogs(id) ON DELETE CASCADE,
            sender VARCHAR(50),
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Tạo bảng knowledge_base_files
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
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database() 