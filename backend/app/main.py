import logging
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app import vector_store
from app.llm import embed_texts, generate_answer
from app.pdf_utils import chunk_pages, extract_pages

log = logging.getLogger("docgpt")
app = FastAPI(title="DocGPT API")

MAX_MB = 20


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    data = await file.read()
    if len(data) > MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File is larger than {MAX_MB} MB.")

    try:
        pages = extract_pages(data)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read this PDF.")

    if not pages:
        raise HTTPException(status_code=422, detail="No text found. Scanned PDFs are not supported yet.")

    chunks = chunk_pages(pages)
    doc_id = uuid.uuid4().hex

    try:
        # embed_texts is a blocking network call, so run it in a worker thread
        # to keep the async server free for other requests.
        vectors = await run_in_threadpool(embed_texts, [c["text"] for c in chunks], "RETRIEVAL_DOCUMENT")
    except Exception:
        log.exception("Embedding failed")
        raise HTTPException(status_code=502, detail="Embedding service failed. Check your API key and quota.")

    vector_store.add_chunks(doc_id, file.filename, chunks, vectors)
    return {"doc_id": doc_id, "filename": file.filename, "chunks": len(chunks)}


class ChatRequest(BaseModel):
    doc_id: str
    question: str


@app.post("/chat")
def chat(req: ChatRequest):  # plain def: FastAPI runs it in a thread pool automatically
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        query_vector = embed_texts([question], "RETRIEVAL_QUERY")[0]
    except Exception:
        log.exception("Query embedding failed")
        raise HTTPException(status_code=502, detail="Embedding service failed. Check your API key and quota.")

    sources = vector_store.search(req.doc_id, query_vector, k=4)
    if not sources:
        raise HTTPException(status_code=404, detail="Document not found. Please upload it again.")

    try:
        answer = generate_answer(question, sources)
    except Exception:
        log.exception("Answer generation failed")
        raise HTTPException(status_code=502, detail="The AI service failed. Check the model name and quota.")

    return {"answer": answer, "sources": sources}