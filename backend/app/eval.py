import os
from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmCategory,
    HarmBlockThreshold,
)
from ragas.metrics import (
    answer_correctness,
    answer_similarity,
    context_recall,
    faithfulness,
)
from flask import Blueprint, request, jsonify, session
from app.config import Config
import logging
from services.rag_service import RAGService

eval_pb = Blueprint("eval", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def require_auth():
    """Kiểm tra user đã đăng nhập chưa"""
    if "user_id" not in session:
        return False, "User not authenticated"
    return True, session["user_id"]


def get_default_config():
    config = {
        "system_prompt": """You are a knowledgeable and helpful chatbot specializing in Traditional Eastern Medicine.
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
If a question cannot be sufficiently answered using the available knowledge base, respond politely and gently, acknowledging the limitation and expressing your intent to help as much as possible.""",
        "model": "gemini-2.0-flash",
        "temperature": 0.1,
        "max_tokens": 1000,
        "max_chunks": 8,
        "cosine_threshold": 0.5,
    }
    return config


def normalize_data(input: list[dict]):
    formatted_input = []

    for item in input:
        formatted_input.append(
            {
                **item,
                "retrieved_contexts": [],
                "response": item.get("answer", ""),
                "ground_truth": item.get("expected_answer", ""),
                "reference": item.get("expected_answer", ""),
                "user_input": item.get("question", ""),
            }
        )

    dataset = EvaluationDataset.from_list(formatted_input)

    return dataset


os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")


def init_model():
    config = {
        "model": "gemini-2.0-flash",
        "temperature": 0.4,
        "max_tokens": None,
        "top_p": 0.8,
    }
    safety_settings = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # Wrap LLM
    llm = ChatGoogleGenerativeAI(
        model=config["model"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        top_p=config["top_p"],
        safety_settings=safety_settings,
    )
    wrapped_llm = LangchainLLMWrapper(llm)

    return wrapped_llm


def get_assistant_response(user_id: str, question: str):
    config = get_default_config()
    rag_service = RAGService(
        Config,
        system_prompt=config.get("system_prompt"),
        model_config=config.get("model_config"),
        max_chunks=config.get("max_chunks", 8),
        cosine_threshold=config.get("cosine_threshold", 0.5),
    )
    rag_result = rag_service.chat_with_rag(question, user_id)

    bot_response = rag_result["response"]
    return bot_response


@eval_pb.route("/evaluate", methods=["POST"])
def evaluate_data():
    is_auth, user_id = require_auth()
    if not is_auth:
        return jsonify({"error": "Authentication required"}), 401

    try:
        input: list[dict] = request.get_json()
        fully_data: list[dict] = []

        if not input:
            return jsonify({"error": "Input data is required"}), 400
        else:
            for item in input:
                question = dict(item).get("question").strip()
                answer = get_assistant_response(user_id, question)
                expected_answer = dict(item).get("expected_answer").strip()
                fully_data.append(
                    {
                        "question": question,
                        "expected_answer": expected_answer,
                        "answer": answer,
                    }
                )
        dataset = normalize_data(fully_data)
        print("Dataset loaded successfully")

        llm = init_model()
        result = evaluate(
            dataset=dataset,
            metrics=[
                answer_correctness,
                answer_similarity,
                context_recall,
                faithfulness,
            ],
            llm=llm,
        )
        evaluation_result = result.__dict__.get("scores", {})

        fully_result = [
            {**item, "score": score}
            for item, score in zip(fully_data, evaluation_result)
        ]
        return jsonify(fully_result), 200
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        return jsonify({"error": f"An error occurred during evaluation: {str(e)}"}), 500
