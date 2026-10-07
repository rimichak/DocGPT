// All backend communication lives in this one file.

// Flip to false once the FastAPI backend is running.
const USE_MOCK = true;

// "/api" is a relative URL. Vite's proxy forwards it to FastAPI.
const BASE = "/api";

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Reads the error message FastAPI sends back, or uses a fallback.
async function readError(res, fallback) {
  try {
    const data = await res.json();
    return data.detail || fallback;
  } catch {
    return fallback;
  }
}

export async function uploadDocument(file) {
  if (USE_MOCK) {
    await wait(1200);
    return { doc_id: "mock-1", filename: file.name, chunks: 42 };
  }

  // FormData is the browser's way to send a file in a request body.
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res, "Upload failed."));
  return res.json(); // { doc_id, filename, chunks }
}

export async function askQuestion(docId, question) {
  if (USE_MOCK) {
    await wait(1500);
    return {
      answer:
        "This is a sample answer from the mock backend. Once FastAPI is connected, this text will be written by the LLM using only the parts of your document that match the question.",
      sources: [
        { page: 3, text: "Sample passage from page 3 that the answer was based on." },
        { page: 7, text: "Another sample passage, this one from page 7." },
      ],
    };
  }

  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id: docId, question }),
  });
  if (!res.ok) throw new Error(await readError(res, "Could not get an answer."));
  return res.json(); // { answer, sources: [{ page, text }] }
}