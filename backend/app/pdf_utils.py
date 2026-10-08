import fitz  # PyMuPDF is imported under the name "fitz"


def extract_pages(pdf_bytes: bytes) -> list[dict]:
    """Return [{"page": 1, "text": "..."}, ...] for every page that has text."""
    pages = []
    # Open the PDF straight from memory, no file needs to be saved to disk.
    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        for number, page in enumerate(pdf, start=1):  # page numbers start at 1
            text = page.get_text().strip()
            if text:  # skip blank pages and image-only pages
                pages.append({"page": number, "text": text})
    return pages


def chunk_pages(pages: list[dict], chunk_size: int = 200, overlap: int = 40) -> list[dict]:
    """Split each page into overlapping word chunks, keeping the page number."""
    chunks = []
    step = chunk_size - overlap  # how far the window moves each time
    for p in pages:
        words = p["text"].split()
        for start in range(0, len(words), step):
            piece = words[start : start + chunk_size]
            chunks.append({"page": p["page"], "text": " ".join(piece)})
            if start + chunk_size >= len(words):
                break  # this window already reached the end of the page
    return chunks