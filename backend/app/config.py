import os
from dotenv import load_dotenv

# Read backend/.env and put each line into the process environment.
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Fail fast: stop at startup if the key is missing, not halfway through a request.
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")