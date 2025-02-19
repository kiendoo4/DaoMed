# This version is inspired by: https://arxiv.org/pdf/2403.04890
import pandas as pd
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
import json
from qdrant_client import QdrantClient, models

def setup():
    global GEMINI_API_KEY1, GEMINI_API_KEY2, QDRANT_API_KEY, qdrant_client
    with open("apikey\\apikey2.txt", 'r') as file:
        apikey_list = [line.strip() for line in file.readlines()]
    GEMINI_API_KEY1 = apikey_list[0]
    GEMINI_API_KEY2 = apikey_list[1]
    QDRANT_LINK = apikey_list[2]
    QDRANT_API_KEY = apikey_list[3]
    qdrant_client = QdrantClient(QDRANT_LINK, api_key=QDRANT_API_KEY)

setup()

model = SentenceTransformer('model/vietnamese-bi-encoder')
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=GEMINI_API_KEY1  # Replace with your API key
)

llm2 = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=GEMINI_API_KEY2  # Replace with your API key
)

def retrieve_relevant_chunks(question, qdrant_client, collection_name, model, top_n):
    # Encode the question to a vector
    question_vector = model.encode(question, show_progress_bar=False).tolist()
    # Perform the search
    search_results = qdrant_client.query_points(
        collection_name=collection_name,
        query=question_vector,
        limit=top_n,
        with_payload=True,
        score_threshold=0.5
    )
    # Extract and return the 'content' field from the payload
    contents = [result.payload['chunks'] for result in search_results.points]
    return contents

def retriever(input_text):
    # Replace with your collection name and model
    collection_name = "doctor"
    retrieved_chunks = retrieve_relevant_chunks(input_text, qdrant_client, collection_name, model, 4)
    return "\n\n".join([chunk for chunk in retrieved_chunks])

# Tìm các chẩn đoán bệnh trước đây giống với câu hỏi của người dùng
df = pd.read_excel("dataset/MedQA no-opt dataset with reasoning.xlsx")
df["Modified Questions"] = df["Modified Questions"].fillna("").astype(str)
tokenized_corpus = [jieba.lcut(q) for q in df["Modified Questions"]]
bm25 = BM25Okapi(tokenized_corpus)
def find_best_match(user_query):
    tokenized_query = jieba.lcut(user_query)
    scores = bm25.get_scores(tokenized_query)
    best_match_idx = scores.argmax()
    return df["Reasonings"].iloc[best_match_idx] if scores[best_match_idx] > 0.5 else ""
#----------------------------------------------------------------------------------------------------------------------------------------
# Prompt template
fi_template = """

    Vai trò: Bạn là DoctorQA, một trợ lý y tế thông minh được tạo ra bởi kiendoo4 với năng lực tư vấn chủ đề Y học

    NGUYÊN TẮC CHÍNH:
        1. Chính xác: 
            Đây là các khái niệm Y học, CHỈ ĐƯỢC trả lời câu hỏi với các khái niệm Y học như sau:

            {context}
            
            Đây là một số các tình trạng tương tự của các bệnh nhân đã từng mắc phải (sử dụng BM25 để truy vấn), dùng các kết quả này như một nguồn tham khảo cho việc trả lời câu hỏi:
            
            {similar_case}
        
        2. Giao tiếp: Rõ ràng - Khoa học
        3. An toàn: Bảo vệ sức khỏe người dùng

    CÂU HỎI: {input}

    Let's think step by step. 

    Nếu cảm thấy chưa thể kết luận được gì cho trường hợp của người dùng, hãy xác định những thông tin cần thiết khác và hỏi người dùng.
    
    Đừng đề cập những nguyên tắc một cách chi tiết khi trả lời.

    CHÚ Ý: 
            
         - Tránh việc trả lời các câu hỏi không liên quan đến chủ đề Y học, hãy gợi ý người dùng hỏi các câu hỏi liên quan đến Y học!

        - Nếu người hỏi có câu hỏi mang tính xúc phạm, lăng mạ, chửi tục, hãy từ chối trả lời!
        
"""

engsub_template = "Translate to English, no Vietnamese or any other languages: {question}"
vi_template = "Translate to Vietnamese, no other languages: {eng_response}"
EXTRACTION_TEMPLATE = """Bạn là một trợ lý chuyên trích xuất các vấn đề cần tra cứu từ câu hỏi y học. 
Nhiệm vụ của bạn là xác định các khái niệm y học quan trọng cần tìm kiếm trong cơ sở dữ liệu.

### INPUT:
{user_question}

### YÊU CẦU:
- Xác định các khái niệm y học chính cần tra cứu.
- **Chỉ trả về danh sách hợp lệ**, không thêm bất kỳ nội dung nào khác.

### OUTPUT FORMAT:
[
    "<khái niệm 1>",
    "<khái niệm 2>",
    "<khái niệm 3>"
]

### VÍ DỤ:

#### Input:
"Tại sao bệnh nhân tiểu đường type 2 dễ bị nhiễm trùng?"

#### Output:
[
    "tiểu đường type 2 nhiễm trùng cơ chế",
    "đái tháo đường type 2 biến chứng nhiễm trùng"
]

#### Input:
"Triệu chứng của viêm gan B là gì? Làm sao để phòng tránh?"

#### Output:
[
    "viêm gan B triệu chứng",
    "viêm gan B phòng ngừa"
]

**Hãy trích xuất từ khóa tìm kiếm dưới dạng danh sách hợp lệ:**"""


def parse_llm_response(llm_response):
    """Chuyển đổi output của LLM từ string thành list."""
    try:
        if isinstance(llm_response, list):  # Nếu LLM trả về list thì dùng luôn
            return llm_response
        elif hasattr(llm_response, "content"):  # Nếu LLM trả về object có `content`
            return json.loads(llm_response.content)  # Chuyển thành list
        elif isinstance(llm_response, str):  # Nếu là string
            return json.loads(llm_response)
        else:
            raise ValueError("Unexpected response format")
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return []


#---------------------------------------------------------------------------------------------------------------------------------------
def chain_of_thought(user_query):
    # Step 1: Extract keyword or medical knowledge that need to be looked into the vectordb
    extraction_prompt = PromptTemplate(input_variables=["user_question"], template=EXTRACTION_TEMPLATE)   
    concept_response = llm2.invoke(extraction_prompt.invoke({"user_question": user_query}))
    print("Raw LLM2 Response:", concept_response)
    parsed_concepts = parse_llm_response(concept_response)
    # Step 2: Extract information from vectordb
    context_parts = []
    for concept in parsed_concepts:
        retrieved_info = retriever(concept)  # Gọi retriever với từng concept
        if retrieved_info:
            context_parts.append(retrieved_info)
    context = "\n".join(context_parts)
    
    # Step 3: Translate question to English
    engsub_prompt = PromptTemplate(input_variables=["question"], template=engsub_template)
    engsub_chain = LLMChain(llm=llm, prompt=engsub_prompt)
    engsub_ans = engsub_chain.run(question=user_query)

    # Step 4: Get best matches from BM25 and translate to Vietnamese
    related_ans_from_MedQA = find_best_match(engsub_ans)
    vi_prompt = PromptTemplate(input_variables=["eng_response"], template=vi_template)
    vi_chain = LLMChain(llm=llm, prompt=vi_prompt)
    vi_ans = vi_chain.run(eng_response=related_ans_from_MedQA)

    # Step 5: Use final_ans information to answer the question
    fi_prompt = PromptTemplate(input_variables=["context", "similar_case", "input"], template=fi_template)
    final_chain = LLMChain(llm=llm, prompt=fi_prompt)
    final_ans = final_chain.run(context=context, similar_case = vi_ans, input=user_query)
    
    return final_ans

# Test the chain
result = chain_of_thought("Tôi đang gặp vấn đề về Tiêu hóa, nôn ói liên tục")
print(result)