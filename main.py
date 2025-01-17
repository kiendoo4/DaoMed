from flask import Flask, render_template, url_for, request, jsonify, session
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.chains import LLMChain
from qdrant_client import QdrantClient, models
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, trim_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages.base import BaseMessage
from langchain.prompts import PromptTemplate
from typing import TypedDict, List, Annotated, Sequence
from langgraph.graph.message import add_messages
from sentence_transformers import SentenceTransformer
import psycopg2
import bcrypt
import database
from PIL import Image
import io
import base64

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    
    Args:
        password (str): The plaintext password to hash.
    
    Returns:
        str: The hashed password as a string.
    """
    # Convert the password to bytes
    password_bytes = password.encode('utf-8')
    # Generate a salt
    salt = bcrypt.gensalt()
    # Hash the password
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Return the hashed password as a string
    return hashed_password.decode('utf-8')

def check_password(provided_password, stored_hashed_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_hashed_password)

GEMINI_API_KEY = ""
llm = None
qdrant_client = None
first_rep = ""
check_first = False
user_avatar = None
first_message = """
Xin chào, tôi là DoctorQA, một trợ lý ảo thông minh có thể hỗ trợ bạn trả lời và giải đáp những câu hỏi liên quan đến Y học.\n\n
Tôi có thể giúp gì cho bạn không?
"""
trimmer = trim_messages(
    max_tokens = 10,
    strategy="last",
    token_counter=len,
    include_system=True,
    allow_partial=True,
    start_on="human",
)
model = SentenceTransformer('model/vietnamese-bi-encoder')

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
    retrieved_chunks = retrieve_relevant_chunks(input_text, qdrant_client, collection_name, model, 3)
    return "\n\n".join([chunk for chunk in retrieved_chunks])

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Vai trò: Bạn là DoctorQA, một trợ lý y tế thông minh được tạo ra bởi kiendoo4 với năng lực tư vấn chủ đề Y học

        NGUYÊN TẮC CHÍNH:
        1. Chính xác: CHỈ ĐƯỢC trả lời câu hỏi với những bằng chứng như sau:
        {context}
        Không được cung cấp câu trả lời nếu không có bằng chứng!
        2. Giao tiếp: Rõ ràng - Khoa học
        3. An toàn: Bảo vệ sức khỏe người dùng

        HƯỚNG DẪN TRẢ LỜI:

        Chào hỏi / Giao tiếp xã giao:
        - Trả lời lịch sự và thân thiện
        - Nhẹ nhàng chuyển hướng câu hỏi sang chủ đề y tế để tránh trả lời những vấn đề thuộc một chủ đề khác ngoài Y tế.

        Câu hỏi liên quan đến kiến thức Y học (người hỏi có thể đang học hoặc làm việc trong ngành Y)
        - Cung cấp thông tin có nguồn gốc, đáng tin cậy, trích nguồn nếu có
        - Giải thích một cách dễ hiểu

        Trường hợp nghi ngờ chẩn đoán:
        - KHÔNG chẩn đoán trực tiếp mà chỉ đưa ra phỏng đoán của mình
        - Phân tích triệu chứng một cách khoa học
        - Gợi ý hướng điều tra y tế tiếp theo

        Trường hợp hỏi bệnh nhưng thông tin không đầy đủ:
        - Xác định các chi tiết còn thiếu
        - Hướng dẫn người dùng cung cấp thông tin chi tiết hơn
        - Không đưa ra các giả định không có cơ sở

        NGUYÊN TẮC TỐI QUAN TRỌNG:
        - Sức khỏe và quyền lợi của người dùng là trên hết
        - Phương pháp: Tôn trọng - Chính xác - Nhân văn
        - Khuyến nghị tham vấn chuyên gia y tế KHI VÀ CHỈ KHI nhận thấy tình trạng bệnh nhân nghiêm trọng hoặc bản thân không biết câu trả lời

        CÂU HỎI CỤ THỂ: {input}

        NGUYÊN TẮC TỐI QUAN TRỌNG:
        - Quyền lợi và sức khỏe của người dùng là trên hết
        - Tôn trọng - Chính xác - Nhân văn
        - Luôn khuyến khích tham vấn chuyên gia y tế

        Đừng đề cập những nguyên tắc một cách chi tiết khi trả lời.

        Hãy sử dụng thông tin cá nhân được cung cấp từ người hỏi bệnh (nếu có) để phục vụ cho việc trao đổi.
        
        Hãy CHỈ sử dụng tên người hỏi để phục vụ việc trao đổi một cách lưu loát, CHỈ sử dụng năm sinh/tuổi và giới tính để phục vụ cho việc phỏng đoán tình trạng bệnh!

        CHÚ Ý: 
        
        - Tránh việc trả lời các câu hỏi không liên quan đến chủ đề Y học, hãy gợi ý người dùng hỏi các câu hỏi liên quan đến Y học!

        - Nếu người hỏi có câu hỏi mang tính xúc phạm, lăng mạ, chửi tục, hãy từ chối trả lời!
        """
    ),
    MessagesPlaceholder(variable_name="messages"),
])

name_chatlog_prompt = PromptTemplate(
    input_variables=["first_rep"],
    template=(
        """Đây là câu chat đầu tiên của người dùng trong chat log mới: '{first_rep}'
        
        Hãy đặt một tiêu đề tổng quát cho nội dung của chatlog mới dựa trên câu chat đầu tiên ở trên.
        
        Lưu ý: tốt nhất là nhiều hơn 4 từ và ít hơn 8 từ."""
    ),
)

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_query: str

def call_model(state: State):
    # Trim the messages using the trimmer
    trimmed_messages = trimmer.invoke(state["messages"])
    context = retriever(state["current_query"])
    # Construct the prompt with the trimmed messages
    formatted_prompt = prompt.invoke(
        {"context": context,  # Pass the context to the template
        "input": state["current_query"],   # Replace with the actual user query
        "messages": trimmed_messages}  # Include the trimmed messages
    )
    # Call the LLM with the formatted prompt
    response = llm.invoke(formatted_prompt)
    # Append the AI response to the state
    return {"messages": [response], "current_query": state["current_query"]}

global config, messages, current_user, current_chatlog
current_user = ""
config = {"configurable": {"thread_id": "1"}}
messages = []
workflow = StateGraph(state_schema=State)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
memory = MemorySaver()
wapp = workflow.compile(checkpointer=memory)

app = Flask(__name__)
app.secret_key = 'lmeo'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mainUI')
def mainUI():
    user_avatar = session.get('user_avatar', None)
    return render_template('chatUI.html', user_avatar=user_avatar)

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/backLogin')
def backLogin():
    return render_template('index.html')

@app.route('/process-text', methods=['POST'])
def process_text():
    # Get the text from the POST request
    data = request.get_json()
    user_message = data.get('message', '')

    # Perform processing with the text
    response = {
        'processed_message': f'Processed: {user_message}'  # Example response
    }

    return jsonify(response)

@app.route('/new-chat-log', methods=['POST'])
def new_chat_log():
    global check_first
    data = request.get_json()
    message = data.get('message', '')
    check_first = False
    return jsonify({"status": "success", "received_message": message})

@app.route('/get-response', methods = ['POST'])
def get_response():
    global llm, first_rep, check_first, current_chatlog
    data = request.json
    user_message = data.get("message", "")
    conversation_details = None
    if not llm:
        return jsonify({"error": "Gemini API key is not set."}), 400
    query = HumanMessage(content=user_message)
    if check_first is False:
        messages.append(AIMessage(first_message))
        first_rep = user_message
        check_first = True
        chain = LLMChain(llm=llm, prompt=name_chatlog_prompt)
        chatlog_name = chain.run({"first_rep": first_rep}).strip()
        cur.execute("""
        INSERT INTO conversations (user_id, topic)
        VALUES (%s, %s)
        """, (current_user[0], chatlog_name))

        cur.execute("""
            SELECT id FROM conversations WHERE topic = %s AND user_id = %s
                    
        """, (chatlog_name, current_user[0]))
        conversation_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO messages (conversation_id, sender, message)
            VALUES (%s, %s, %s)
        """, (conversation_id, 'bot', first_message))

        # Insert the first message into the messages table
        cur.execute("""
            INSERT INTO messages (conversation_id, sender, message)
            VALUES (%s, %s, %s)
        """, (conversation_id, 'user', first_rep))

        # Commit the changes to the database
        con.commit()
        current_chatlog = conversation_id
        conversation_details = {
            "id": conversation_id,
            "topic": chatlog_name
        }
    else:
        conversation_details = None
        cur.execute("""
            INSERT INTO messages (conversation_id, sender, message)
            VALUES (%s, %s, %s)
        """, (current_chatlog, 'user', user_message))
        con.commit()

    messages.append(query)
    state = {
        "messages": messages,
        "current_query": user_message
    }
    full_response = ""
    for chunk, metadata in wapp.stream(state, config, stream_mode="messages"):
        if isinstance(chunk, AIMessage):
            full_response += chunk.content
        else:
            full_response = "Tôi bị khùm"
    messages.append(AIMessage(full_response))
    cur.execute("""
            INSERT INTO messages (conversation_id, sender, message)
            VALUES (%s, %s, %s)
        """, (current_chatlog, 'bot', full_response))
    con.commit()
    return jsonify({"response": full_response, "conversation": conversation_details})

@app.route('/get-initial-message', methods=['GET'])
def get_initial_message():
    global first_message
    return jsonify({"response": first_message})

@app.route('/get-gemini-apikey', methods = ['GET'])
def get_gemini_apikey():
    global GEMINI_API_KEY, llm
    data = request.get_json()
    if data and "apiKey" in data:
        GEMINI_API_KEY = data["apiKey"]
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=GEMINI_API_KEY
        )
        return jsonify({"success": True, "apiKey": GEMINI_API_KEY})
    else:
        return jsonify({"success": False, "error": "API key is missing"}), 400

@app.route('/validate-account', methods = ["POST"])
def validate_account():
    global current_user
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"isValid": False, "message": "Something is missing"}), 400
        else:
            cur.execute("SELECT id, password_hash, profile_image FROM users WHERE username = %s or email = %s", (username, username,))
            user = cur.fetchone()
            if user:
                current_user = user
                stored_hashed_password = user[1].encode('utf-8')
                if check_password(password, stored_hashed_password):
                    user_avatar_base64 = base64.b64encode(user[2]).decode('utf-8')
                    session['user_avatar'] = user_avatar_base64
                    return jsonify({"isValid": True, "message": "Đăng nhập thành công", "user": {"username": username}})
                return jsonify({"isValid": False, "message": "Tài khoản hoặc mật khẩu đăng nhập không đúng"}), 401
            return jsonify({"isValid": False, "message": "Tài khoản hoặc mật khẩu đăng nhập không đúng"}), 401
            
    except Exception as e:
        print("Có lỗi xảy ra trong quá trình đăng nhập", str(e))
        return jsonify({"isValid": False, "message": "Có lỗi xảy ra trong quá trình đăng nhập"}), 500

# Registration
@app.route('/check_username', methods=['POST'])
def check_username_route():
    data = request.json
    username = data.get('username')
    if not username:
        return jsonify({'exists': False})
    
    check_acc = database.check_username(cur, username);
    if check_acc:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@app.route('/conversations', methods=['GET'])
def get_conversations():
    user_id = current_user[0]
    cur.execute("SELECT id, topic FROM conversations WHERE user_id = %s ORDER BY started_at ASC", (user_id,))
    rows = cur.fetchall()
    conversations = [{"id": row[0], "topic": row[1]} for row in rows]
    return jsonify(conversations)

@app.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    global current_chatlog
    # Check if the conversation belongs to the current user
    user_id = current_user[0]  # Replace with your logic to get the current user's ID
    cur.execute("SELECT id FROM conversations WHERE id = %s AND user_id = %s", (conversation_id, user_id))
    conversation = cur.fetchone()
    current_chatlog = conversation_id
    if not conversation:
        return jsonify({"error": "Conversation not found or access denied"}), 404

    # Fetch messages for the conversation
    cur.execute("""
        SELECT sender, message, timestamp
        FROM messages
        WHERE conversation_id = %s
        ORDER BY timestamp ASC
    """, (conversation_id,))
    rows = cur.fetchall()

    messages = [
        {"sender": row[0], "message": row[1], "timestamp": row[2].isoformat(), "nameUser": current_user[1]} for row in rows
    ]
    return jsonify(messages)

def setup():
    global apikey_list, GEMINI_API_KEY, QDRANT_LINK, QDRANT_API_KEY, POSTGRES_KEY, con, cur, qdrant_client, llm
    with open("apikey\\apikey.txt", 'r') as file:
        apikey_list = [line.strip() for line in file.readlines()]
    GEMINI_API_KEY = apikey_list[0]
    POSTGRES_KEY = apikey_list[1]
    QDRANT_LINK = apikey_list[2]
    QDRANT_API_KEY = apikey_list[3]
    con = psycopg2.connect(POSTGRES_KEY)
    cur = con.cursor()
    qdrant_client = QdrantClient(QDRANT_LINK, api_key=QDRANT_API_KEY)
    llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=GEMINI_API_KEY
        )

if __name__ == "__main__":
    setup()
    app.run(debug=True)
    cur.close()
    con.close()