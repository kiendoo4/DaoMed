import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Qdrant
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')

    # PostgreSQL - ưu tiên environment variables từ Docker
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'daomed_db')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'daomed')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'daomed_pass')

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key_here')

    # Gemini API Key (nếu dùng)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    # MinIO - ưu tiên environment variables từ Docker
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9100')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'daomed')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'daomed_secret')
    MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'daomed-files')
    
    # Model path - ưu tiên environment variables từ Docker
    MODEL_PATH = os.getenv('MODEL_PATH', '/models/vietnamese-bi-encoder')