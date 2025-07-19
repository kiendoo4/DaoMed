import os
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from .qdrant_service import QdrantService
from .minio_service import MinioService

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, config, system_prompt=None, model_config=None, max_chunks=8, cosine_threshold=0.5):
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Use provided model config or default
        if model_config:
            if isinstance(model_config, str):
                import json
                model_config = json.loads(model_config)
            
            model_name = model_config.get('model', 'gemini-2.0-flash')
            temperature = model_config.get('temperature', 0.7)
            max_tokens = model_config.get('max_tokens', 1000)
        else:
            model_name = 'gemini-2.0-flash'
            temperature = 0.1
            max_tokens = 1000
        
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens
            }
        )
        
        # Initialize services with config
        self.qdrant_service = QdrantService(config)
        self.minio_service = MinioService(config)
        
        # RAG configuration
        self.max_chunks = max_chunks
        self.cosine_threshold = cosine_threshold
        
        # Use provided system prompt or default
        self.system_prompt = system_prompt or """You are a knowledgeable and helpful chatbot specializing in Traditional Eastern Medicine.
You answer user questions by retrieving and reasoning over information from the following six classical medical texts:

Shennong Bencao Jing (Thần Nông Bản Thảo)
Shanghan Lun (Thương Hàn Luận)
Nanjing (Nan Kinh)
Huangdi Neijing – Lingshu (Hoàng Đế Nội Kinh - Linh Khu)
Jingui Yaolue (Kim Quỹ Yếu Lược)
Qianjin Yaofang (Thiên Kim Yếu Phương)

Language Handling Rules:
If the user asks a question in Classical Chinese (chữ Hán), you must respond in Classical Chinese.
If the user uses Vietnamese, Modern Chinese, or English, respond in that language accordingly.
Always adapt your language based on the user's current usage.

Your Role:
Provide accurate, faithful answers based only on the content from the six books listed above.
Quote, summarize, or explain relevant passages as needed, but never fabricate information.
If a question cannot be sufficiently answered using the available knowledge base, respond politely and gently, acknowledging the limitation and expressing your intent to help as much as possible."""

    def search_knowledge_base(self, query: str, user_id: int = None, limit: int = None) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        try:
            # Use instance max_chunks if limit not provided
            if limit is None:
                limit = self.max_chunks
            
            # Search in Qdrant with cosine threshold
            success, search_results = self.qdrant_service.search_chunks(
                query, 
                user_id=user_id, 
                top_k=limit, 
                score_threshold=self.cosine_threshold
            )
            
            if not success:
                logger.error(f"Search failed: {search_results}")
                return []
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    'content': result.get('text', ''),
                    'source': f"KB_{result.get('kb_id', 'unknown')}",
                    'score': result.get('score', 0.0),
                    'metadata': {
                        'chunk_id': result.get('chunk_id'),
                        'kb_id': result.get('kb_id'),
                        'row_index': result.get('row_index'),
                        'headers': result.get('headers', [])
                    }
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []

    def generate_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Generate context from search results"""
        if not search_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            content = result['content']
            source = result['source']
            score = result['score']
            
            context_parts.append(f"**Tài liệu {i}** (Độ liên quan: {score:.2f})\n")
            context_parts.append(f"Nguồn: {source}\n")
            context_parts.append(f"Nội dung: {content}\n")
            context_parts.append("-" * 50 + "\n")
        
        return "\n".join(context_parts)

    def generate_response(self, user_message: str, context: str = "") -> str:
        """Generate response using Gemini with RAG"""
        try:
            # Prepare prompt
            if context:
                prompt = f"""Dựa trên thông tin từ knowledge base và kiến thức y học cổ truyền, hãy trả lời câu hỏi sau:

**Thông tin từ Knowledge Base:**
{context}

**Câu hỏi của người dùng:**
{user_message}

Hãy trả lời dựa trên thông tin có sẵn và kiến thức y học cổ truyền."""
            else:
                prompt = f"""Dựa trên kiến thức y học cổ truyền, hãy trả lời câu hỏi sau:

**Câu hỏi của người dùng:**
{user_message}

Hãy trả lời dựa trên kiến thức y học cổ truyền."""

            # Generate response
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text
            else:
                return "Xin lỗi, tôi không thể tạo câu trả lời. Vui lòng thử lại."
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Xin lỗi, có lỗi xảy ra: {str(e)}"

    def chat_with_rag(self, user_message: str, user_id: int = None) -> Dict[str, Any]:
        """Main RAG workflow for chat"""
        try:
            # Step 1: Search knowledge base
            logger.info(f"Searching knowledge base for: {user_message}")
            search_results = self.search_knowledge_base(user_message, user_id=user_id)
            
            # Step 2: Generate context
            context = self.generate_context(search_results)
            logger.info(f"Found {len(search_results)} relevant documents")
            
            # Step 3: Generate response with RAG
            logger.info("Generating response with Gemini")
            response = self.generate_response(user_message, context)
            
            # Step 4: Return structured response
            return {
                'response': response,
                'context_used': context,
                'sources': [result['source'] for result in search_results],
                'search_results_count': len(search_results)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG workflow: {str(e)}")
            return {
                'response': f"Xin lỗi, có lỗi xảy ra trong quá trình xử lý: {str(e)}",
                'context_used': "",
                'sources': [],
                'search_results_count': 0
            }

    def get_system_prompt(self) -> str:
        """Get system prompt"""
        return self.system_prompt

    def update_system_prompt(self, new_prompt: str):
        """Update system prompt"""
        self.system_prompt = new_prompt
        logger.info("System prompt updated") 