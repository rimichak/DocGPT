import chromadb

from app.config import CHROMA_PATH

# PersistentClient saves data to disk, so documents survive a server restart.
_client = chromadb.PersistentClient(path=CHROMA_PATH)

# A collection is like a table. One collection holds the chunks of all documents.
_collection = _client.get_or_create_collection(name="documents")


def add_chunks(doc_id: str, filename: str, chunks: list[dict], vectors: list[list[float]]) -> None:
    _collection.add(
        ids=[f"{doc_id}-{i}" for i in range(len(chunks))],  # unique id per chunk
        documents=[c["text"] for c in chunks],  # the original text
        embeddings=vectors,  # the vectors we computed
        metadatas=[{"doc_id": doc_id, "filename": filename, "page": c["page"]} for c in chunks],
    )


def search(doc_id: str, query_vector: list[float], k: int = 4) -> list[dict]:
    """Return the k chunks of this document closest in meaning to the query."""
    result = _collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where={"doc_id": doc_id},  # only search inside the chosen document
    )
    texts = result["documents"][0]  # results come as a list per query, we sent one query
    metas = result["metadatas"][0]
    return [{"page": m["page"], "text": t} for t, m in zip(texts, metas)]