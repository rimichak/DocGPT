import os
from pathlib import Path

from dotenv import load_dotenv

# Read backend/.env and put each line into the process environment.
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Fail fast: stop at startup if the key is missing, not halfway through a request.
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")

# Model names live here so they can be changed without touching other code.
# Optional overrides can be set in .env (EMBED_MODEL, CHAT_MODEL).
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")

# ChromaDB saves its files here: backend/chroma_db (already in .gitignore).
CHROMA_PATH = str(Path(__file__).resolve().parent.parent / "chroma_db")