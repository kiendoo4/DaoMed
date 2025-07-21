from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class KnowledgeBaseFile(Base):
    __tablename__ = 'knowledge_base_files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    minio_path = Column(String(255), nullable=False)
    uploaded_by = Column(String(64), nullable=True)  # Có thể liên kết user sau
    uploaded_at = Column(DateTime, default=func.now())
    num_chunks = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=True)
    description = Column(Text, nullable=True) 