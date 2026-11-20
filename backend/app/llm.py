import time

from google import genai
from google.genai import errors, types

from app.config import CHAT_FALLBACK_MODEL, CHAT_MODEL, EMBED_MODEL, GEMINI_API_KEY

# One client for the whole app, created once at startup.
client = genai.Client(api_key=GEMINI_API_KEY)

BATCH_SIZE = 100  # the embedding API accepts up to 100 texts per request

# HTTP codes that mean "temporary problem, trying again can work".
RETRYABLE = {429, 500, 502, 503, 504}


def _call_with_retries(fn, attempts: int = 4):
    """Run fn(). On a temporary Google error, wait and try again."""
    last_error = None
    for i in range(attempts):
        try:
            return fn()
        except errors.APIError as e:
            if e.code not in RETRYABLE:
                raise  # a real error (bad key, bad model name), retrying will not help
            last_error = e
            if i < attempts - 1:
                time.sleep(2 * (i + 1))  # wait 2s, 4s, 6s
    raise last_error


def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:
    """Turn texts into vectors. task_type is RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY."""
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        result = _call_with_retries(
            lambda: client.models.embed_content(
                model=EMBED_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
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

    # Alternate between the main and fallback model, five tries in total.
    attempts = [CHAT_MODEL, CHAT_FALLBACK_MODEL, CHAT_MODEL, CHAT_FALLBACK_MODEL, CHAT_MODEL]
    last_error = None
    for i, model in enumerate(attempts):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text or "I could not generate an answer."
        except errors.APIError as e:
            if e.code not in RETRYABLE:
                raise
            last_error = e
            if i < len(attempts) - 1:
                time.sleep(2 * (i + 1))
    raise last_error