# This version is inspired by: https://arxiv.org/pdf/2403.04890

import pandas as pd
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

### Tra dữ liệu từ MedQA-no-option
# Đọc dữ liệu
df = pd.read_excel("dataset\MedQA no-opt dataset with reasoning.xlsx")
df["Modified Questions"] = df["Modified Questions"].fillna("").astype(str)
tokenized_corpus = [jieba.lcut(q) for q in df["Modified Questions"]]  # Tokenize câu hỏi

# Khởi tạo BM25
bm25 = BM25Okapi(tokenized_corpus)

def find_best_match(user_query):
    tokenized_query = jieba.lcut(user_query)
    scores = bm25.get_scores(tokenized_query)
    best_match_idx = scores.argmax()
    return df["Reasonings"].iloc[best_match_idx] if scores[best_match_idx] > 0.5 else ""

fi_template = """Vai trò: Bạn là DoctorQA, một trợ lý y tế thông minh được tạo ra bởi kiendoo4 với năng lực tư vấn chủ đề Y học

            NGUYÊN TẮC CHÍNH:
            1. Chính xác: CHỈ ĐƯỢC trả lời câu hỏi với những bằng chứng như sau, SỬ DỤNG VỚI MỨC ĐỘ ƯU TIÊN CAO NHẤT:
            {context}
            2. Giao tiếp: Rõ ràng - Khoa học
            3. An toàn: Bảo vệ sức khỏe người dùng

            CÂU HỎI: {input}

            Đừng đề cập những nguyên tắc một cách chi tiết khi trả lời.

            CHÚ Ý: 
            
            - Tránh việc trả lời các câu hỏi không liên quan đến chủ đề Y học, hãy gợi ý người dùng hỏi các câu hỏi liên quan đến Y học!

            - Nếu người hỏi có câu hỏi mang tính xúc phạm, lăng mạ, chửi tục, hãy từ chối trả lời!
"""

### Bắt đầu Chain-of-thought

def chain_of_thought(llm, user_query):
    ### Các bước CoT
    # Bước 1: Dịch câu hỏi sau sang tiếng Anh
    engsub_template = "Translate to English, no Vietnamese or any other languages: {question}"
    engsub_prompt = PromptTemplate(input_variables=["question"], template=engsub_template)
    engsub_chain = LLMChain(llm=llm, prompt=engsub_prompt, output_key="eng_question")
    engsub_ans = engsub_chain.run(user_query)

    # Bước 2: Trả về các kết quả tốt nhất từ BM25 và dịch sang tiếng Việt
    related_ans_from_MedQA = find_best_match(engsub_ans)
    vi_template = "Translate to Vietnamese, no other languages: {eng_response}"
    vi_prompt = PromptTemplate(input_variables=["eng_response"], template=vi_template)
    vi_chain = LLMChain(llm=llm, prompt=vi_prompt, output_key="vi_related")
    vi_ans = vi_chain.run(related_ans_from_MedQA)

    # Bước 3: Sử dụng thông tin từ final_ans để trả lời câu hỏi
    prompt = PromptTemplate(input_variables=["context", "input"], template=fi_template)
    final_chain = LLMChain(llm = llm, prompt_template = prompt, output_key = "final_ans")
    
    final_ans = final_chain.run({'context': vi_ans, 'input': user_query})
    return final_ans, engsub_ans, vi_ans, related_ans_from_MedQA