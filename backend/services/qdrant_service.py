from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import logging
import os

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self, config):
        self.client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT,
            api_key=config.QDRANT_API_KEY or None
        )
        
        # Use configurable model path
        model_path = config.MODEL_PATH
        logger.info(f"Loading model from: {model_path}")
        
        try:
            self.model = SentenceTransformer(model_path)
            logger.info(f"Successfully loaded model from {model_path}")
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {str(e)}")
            raise
        
        self.collection_name = "daomed_chunks"
        self.vector_size = 768  # Size của vietnamese-bi-encoder
        
        # Tạo collection nếu chưa có
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Đảm bảo collection tồn tại"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    def vectorize_chunks(self, chunks, kb_id, user_id):
        """
        Vectorize chunks và lưu vào Qdrant
        """
        try:
            if not chunks:
                logger.warning("No chunks to vectorize")
                return False, "No chunks provided"
            
            # Tạo points cho Qdrant
            points = []
            
            for chunk in chunks:
                # Vectorize chunk text
                chunk_text = chunk['text']
                vector = self.model.encode(chunk_text, show_progress_bar=False).tolist()
                
                # Tạo point ID dạng integer: kb_id * 10000 + chunk_id
                # Đảm bảo unique và Qdrant chấp nhận
                point_id = kb_id * 10000 + chunk['id']
                
                # Tạo point với metadata
                point = PointStruct(
                    id=point_id,  # Integer ID thay vì string
                    vector=vector,
                    payload={
                        'chunk_id': chunk['id'],
                        'kb_id': kb_id,
                        'user_id': user_id,
                        'text': chunk_text,
                        'row_index': chunk['row_index'],
                        'headers': chunk['headers']
                    }
                )
                points.append(point)
            
            # Upload points vào Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Successfully vectorized and stored {len(points)} chunks for KB {kb_id}")
            return True, f"Vectorized {len(points)} chunks"
            
        except Exception as e:
            logger.error(f"Error vectorizing chunks: {str(e)}")
            return False, str(e)
    
    def search_chunks(self, query, user_id, top_k=5, score_threshold=0.5):
        """
        Tìm kiếm chunks liên quan đến query
        """
        try:
            # Vectorize query
            query_vector = self.model.encode(query, show_progress_bar=False).tolist()
            
            # Search trong Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=None  # Có thể thêm filter theo user_id nếu cần
            )
            
            # Format kết quả
            results = []
            for result in search_results:
                results.append({
                    'chunk_id': result.payload['chunk_id'],
                    'kb_id': result.payload['kb_id'],
                    'text': result.payload['text'],
                    'row_index': result.payload['row_index'],
                    'headers': result.payload['headers'],
                    'score': result.score
                })
            
            logger.info(f"Found {len(results)} relevant chunks for query: {query}")
            return True, results
            
        except Exception as e:
            logger.error(f"Error searching chunks: {str(e)}")
            return False, str(e)
    
    def delete_kb_chunks(self, kb_id):
        """
        Xóa tất cả chunks của một knowledge base
        """
        try:
            # Tìm và xóa tất cả points có kb_id
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=f"kb_id:{kb_id}"
            )
            logger.info(f"Deleted all chunks for KB {kb_id}")
            return True, f"Deleted chunks for KB {kb_id}"
            
        except Exception as e:
            logger.error(f"Error deleting KB chunks: {str(e)}")
            return False, str(e)
    
    def get_collection_info(self):
        """
        Lấy thông tin collection
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return True, info
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return False, str(e)
    
    def get_chunk_vector(self, kb_id, chunk_id):
        """
        Lấy vector của một chunk cụ thể
        """
        try:
            # Tạo point ID dạng integer: kb_id * 10000 + chunk_id
            point_id = kb_id * 10000 + chunk_id
            
            # Lấy point từ Qdrant
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=True
            )
            
            if not points:
                return False, f"Chunk {chunk_id} not found in KB {kb_id}"
            
            point = points[0]
            
            # Format kết quả
            vector_data = {
                'vector': point.vector,
                'metadata': {
                    'chunk_id': point.payload['chunk_id'],
                    'kb_id': point.payload['kb_id'],
                    'user_id': point.payload['user_id'],
                    'text': point.payload['text'],
                    'row_index': point.payload['row_index'],
                    'headers': point.payload['headers']
                }
            }
            
            logger.info(f"Successfully retrieved vector for chunk {chunk_id} in KB {kb_id}")
            return True, vector_data
            
        except Exception as e:
            logger.error(f"Error getting chunk vector: {str(e)}")
            return False, str(e) 