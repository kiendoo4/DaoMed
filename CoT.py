### Sử dụng để thực hiện Chain-of-thought cho việc trả lời hiệu quả hơn

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

### Các bước CoT
# Bước 1: Xác định loại câu hỏi 
classify_template = """
Phân loại câu hỏi y học: {question}
Loại câu hỏi có thể là: [xã giao, triệu chứng, điều trị, kiến thức y học, dự phòng].
Trả lời ngắn gọn (chỉ chọn 1 trong 5 khả năng): """

# Bước 2: Xử lý theo từng loại câu hỏi
# 2.1 Phân tích triệu chứng
symptom_template = """
Phân tích triệu chứng từ câu hỏi sau:
Câu hỏi: {question}
Hãy liệt kê:
1. Các nguyên nhân y học có thể
2. Khuyến nghị có nên đi khám ngay không
Trả lời chi tiết: """

# 2.2 Hướng dẫn điều trị
treatment_template = """
Đề xuất phương pháp điều trị cho vấn đề:
Câu hỏi: {question}
Hãy cung cấp:
1. Các phương pháp điều trị phổ biến
2. Lưu ý khi điều trị
3. Thời gian điều trị dự kiến
4. Khuyến nghị về việc thăm khám bác sĩ
Trả lời chi tiết: """

# 2.3 Cung cấp kiến thức y học
medical_knowledge_template = """
Cung cấp kiến thức y học về:
Câu hỏi: {question}
Hãy giải thích ngắn gọn về vấn đề
Trả lời chi tiết: """

# 2.4 Hướng dẫn dự phòng
prevention_template = """
Đề xuất biện pháp dự phòng cho:
Câu hỏi: {question}
Hãy đưa ra:
1. Các biện pháp dự phòng chính
2. Thói quen sinh hoạt cần điều chỉnh
3. Chế độ ăn uống phù hợp
4. Các xét nghiệm tầm soát nên thực hiện
Trả lời chi tiết: """

# 2.5 Trả lời xã giao
social_template = """
Trả lời xã giao cho câu hỏi:
Câu hỏi: {question}
Hãy:
1. Thể hiện sự đồng cảm và thấu hiểu
2. Đưa ra lời khuyên chung
3. Khuyến khích tìm kiếm hỗ trợ y tế nếu cần
Trả lời thân thiện: """

# Bước 3: Template đề xuất hướng xử lý cho từng loại
symptom_recommendation_template = """
Dựa trên phân tích triệu chứng, đề xuất hướng xử lý:
Câu hỏi: {question}
Kết quả phân tích: {analysis}
Hãy đưa ra:
1. Các biện pháp xử lý khẩn cấp (nếu cần)
2. Hướng dẫn chăm sóc tại nhà
3. Thời điểm cần đến cơ sở y tế
4. Các xét nghiệm cần thực hiện
5. Chuyên khoa cần thăm khám
Hướng dẫn chi tiết: """

treatment_recommendation_template = """
Dựa trên phương pháp điều trị đề xuất:
Câu hỏi: {question}
Phân tích điều trị: {analysis}
Hãy hướng dẫn:
1. Các bước thực hiện điều trị cụ thể
2. Lịch trình điều trị chi tiết
3. Cách theo dõi và đánh giá hiệu quả
4. Dấu hiệu cần điều chỉnh phương pháp
5. Phương án dự phòng nếu điều trị không hiệu quả
Hướng dẫn chi tiết: """

knowledge_recommendation_template = """
Dựa trên kiến thức y học đã cung cấp:
Câu hỏi: {question}
Thông tin y học: {analysis}
Hãy đề xuất:
1. Cách áp dụng kiến thức vào thực tế
2. Những điều cần lưu ý đặc biệt
3. Nguồn tham khảo thêm
4. Các chuyên gia cần tư vấn
5. Kế hoạch theo dõi và cập nhật kiến thức
Hướng dẫn chi tiết: """

prevention_recommendation_template = """
Dựa trên biện pháp dự phòng đã đề xuất:
Câu hỏi: {question}
Phân tích dự phòng: {analysis}
Hãy hướng dẫn:
1. Lịch trình thực hiện các biện pháp dự phòng
2. Cách đánh giá hiệu quả dự phòng
3. Điều chỉnh kế hoạch khi cần
4. Tần suất kiểm tra sức khỏe
5. Các dấu hiệu cần chú ý đặc biệt
Hướng dẫn chi tiết: """

social_recommendation_template = """
Dựa trên tình huống xã giao:
Câu hỏi: {question}
Phân tích ban đầu: {analysis}
Hãy đề xuất:
1. Các bước tiếp theo cụ thể
2. Cách tìm kiếm hỗ trợ phù hợp
3. Những nguồn thông tin đáng tin cậy
4. Cộng đồng hỗ trợ liên quan
5. Thời điểm cần tìm đến chuyên gia
Hướng dẫn chi tiết: """

classify_prompt = PromptTemplate(input_variables=["question"], template=classify_template)

# Hàm tổng hợp cập nhật
def create_medical_qa_chain(llm):
    # Tạo các chain riêng cho từng loại
    symptom_chain = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["question"], template=symptom_template), 
        output_key="response")

    treatment_chain = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["question"], template=treatment_template),
        output_key="response")

    knowledge_chain = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["question"], template=medical_knowledge_template),
        output_key="response")

    prevention_chain = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["question"], template=prevention_template),
        output_key="response")

    social_chain = LLMChain(llm=llm, prompt=PromptTemplate(
        input_variables=["question"], template=social_template),
        output_key="response")
    
    classify_chain = LLMChain(llm=llm, prompt=classify_prompt, output_key="category")

    # Tạo các chain recommendation
    def create_recommendation_chain(template, llm):
        prompt = PromptTemplate(
            input_variables=["question", "analysis"],
            template=template)
        return LLMChain(llm=llm, prompt=prompt, output_key="recommendation")

    # Map recommendation chains
    recommendation_chains = {
        "triệu chứng": create_recommendation_chain(symptom_recommendation_template, llm),
        "điều trị": create_recommendation_chain(treatment_recommendation_template, llm),
        "kiến thức y học": create_recommendation_chain(knowledge_recommendation_template, llm),
        "dự phòng": create_recommendation_chain(prevention_recommendation_template, llm),
        "xã giao": create_recommendation_chain(social_recommendation_template, llm)
    }

    # Hàm chọn chain phù hợp dựa trên category
    def select_chain(category):
        chain_map = {
            "triệu chứng": symptom_chain,
            "điều trị": treatment_chain,
            "kiến thức y học": knowledge_chain,
            "dự phòng": prevention_chain,
            "xã giao": social_chain
        }
        return chain_map.get(category.strip().lower())
    
    def combine_chains(inputs):
        question = inputs["question"]
        
        # Bước 1: Phân loại
        category_result = classify_chain.run(question)
        
        # Bước 2: Phân tích theo loại
        selected_chain = select_chain(category_result)
        if selected_chain:
            analysis = selected_chain.run(question)
        else:
            return {
                "category": category_result,
                "analysis": "Không thể xác định loại câu hỏi phù hợp.",
                "recommendation": "Không có đề xuất."
            }
            
        # Bước 3: Đề xuất hướng xử lý
        recommendation_chain = recommendation_chains.get(category_result.strip().lower())
        if recommendation_chain:
            recommendation = recommendation_chain.run({
                "question": question,
                "analysis": analysis
            })
        else:
            recommendation = "Không có đề xuất cụ thể."
            
        return {
            "category": category_result,
            "analysis": analysis,
            "recommendation": recommendation
        }
    
    return combine_chains
"""
print("let's CoT")
# Sử dụng chain tổng hợp
medical_qa = create_medical_qa_chain()
result = medical_qa({
    "question": "Tôi bị đau đầu liên tục 3 ngày nay"})

print(f"Loại câu hỏi: {result['category']}")
print(f"Phân tích: {result['analysis']}")
print(f"Đề xuất: {result['recommendation']}")
"""