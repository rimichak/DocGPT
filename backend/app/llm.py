from google import genai
from google.genai import types

from app.config import CHAT_MODEL, EMBED_MODEL, GEMINI_API_KEY

# One client for the whole app, created once at startup.
client = genai.Client(api_key=GEMINI_API_KEY)

BATCH_SIZE = 100  # the embedding API accepts up to 100 texts per request


def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:
    """Turn texts into vectors. task_type is RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY."""
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        vectors.extend(e.values for e in result.embeddings)
    return vectors


def generate_answer(question: str, chunks: list[dict]) -> str:
    """Ask Gemini to answer using only the retrieved chunks."""
    context = "\n\n".join(f"[Page {c['page']}]\n{c['text']}" for c in chunks)

    prompt = f"""You answer questions about a document.
Use ONLY the context below. If the answer is not in the context, say you could not find it in the document.
Be clear and concise.

Context:
{context}

Question: {question}"""

    response = client.models.generate_content(model=CHAT_MODEL, contents=prompt)
    return response.text or "I could not generate an answer."