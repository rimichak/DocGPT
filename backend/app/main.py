import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app import config  # noqa: F401  (importing it validates the .env key at startup)
from app.pdf_utils import chunk_pages, extract_pages

app = FastAPI(title="DocGPT API")

# Temporary storage: doc_id -> {"filename": ..., "chunks": [...]}.
# It is lost on restart. We replace it with ChromaDB in the next step.
DOCS: dict[str, dict] = {}

MAX_MB = 20


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    data = await file.read()  # the whole file as bytes
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
    DOCS[doc_id] = {"filename": file.filename, "chunks": chunks}

    # This shape matches what the React app expects.
    return {"doc_id": doc_id, "filename": file.filename, "chunks": len(chunks)}


class ChatRequest(BaseModel):
    doc_id: str
    question: str


@app.post("/chat")
def chat(req: ChatRequest):
    doc = DOCS.get(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found. Please upload it again.")

    # Placeholder until we add embeddings and the LLM. It returns the first two chunks as "sources".
    sources = [{"page": c["page"], "text": c["text"][:300]} for c in doc["chunks"][:2]]
    return {
        "answer": "Your document was uploaded and split into chunks. The real AI answer comes in the next step.",
        "sources": sources,
    }