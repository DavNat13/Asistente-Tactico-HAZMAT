from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from src.utils.prompts import HAZMAT_SYSTEM_PROMPT, format_context


class Generator:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if Generator._initialized:
            return

        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY
        )
        Generator._initialized = True

    @traceable(name="hazmat_generation")
    def generate(self, query: str, context_chunks: list[dict], history: list[dict] = None) -> dict:
        context_text = format_context(context_chunks)
        formatted_prompt = HAZMAT_SYSTEM_PROMPT.format(context=context_text)

        messages = [{"role": "system", "content": formatted_prompt}]

        if history:
            messages.extend(history[-6:])

        messages.append({"role": "user", "content": query})

        response = self.llm.invoke(messages)

        sources = []
        for chunk in context_chunks:
            metadata = chunk.get("metadata", {})
            sources.append({
                "page": metadata.get("page_number", "N/A"),
                "source": metadata.get("source", "GRE"),
                "score": chunk.get("score", 0)
            })

        return {
            "answer": response.content,
            "sources": sources,
            "context_used": len(context_chunks)
        }


generator = Generator()
