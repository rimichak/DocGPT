import { useState, useRef, useEffect } from "react";
import { uploadDocument, askQuestion } from "./api";
import "./App.css";

const SUGGESTIONS = [
  "Summarize this document",
  "What are the key points?",
  "List important dates or numbers",
];

function FileIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5M9 13h6M9 17h4" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 19V5M5 12l7-7 7 7" />
    </svg>
  );
}

export default function App() {
  const [doc, setDoc] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  async function handleFile(file) {
    if (!file) return;
    if (file.type !== "application/pdf") {
      setError("Please choose a PDF file.");
      return;
    }
    setError("");
    setUploading(true);
    try {
      const result = await uploadDocument(file);
      setDoc(result);
      setMessages([]);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  // One function sends a question, whether typed or clicked from a suggestion.
  async function sendQuestion(question) {
    if (!question || thinking || !doc) return;
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setThinking(true);
    setError("");
    try {
      const { answer, sources } = await askQuestion(doc.doc_id, question);
      setMessages((prev) => [...prev, { role: "assistant", text: answer, sources }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setThinking(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    sendQuestion(input.trim());
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-mark">D</span>
          <span className="logo-name">DocGPT</span>
        </div>
        <p className="tagline">Upload a PDF and ask it questions. Every answer shows where it came from.</p>

        <div
          className={`dropzone ${dragging ? "is-dragging" : ""}`}
          onClick={() => fileRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && fileRef.current.click()}
        >
          <input ref={fileRef} type="file" accept="application/pdf" hidden onChange={(e) => handleFile(e.target.files[0])} />
          <FileIcon />
          <p>{uploading ? "Reading your document..." : <><strong>Choose a PDF</strong> or drop it here</>}</p>
        </div>

        {doc && (
          <div className="doc-card">
            <span className="doc-icon"><FileIcon /></span>
            <div>
              <p className="doc-name">{doc.filename}</p>
              <p className="doc-meta"><span className="dot" /> Ready, {doc.chunks} sections</p>
            </div>
          </div>
        )}
      </aside>

      <main className="chat">
        <header className="topbar">{doc ? doc.filename : "No document yet"}</header>

        <div className="messages">
          <div className="thread">
            {messages.length === 0 && (
              <div className="empty">
                <h2>{doc ? "Ask your document anything" : "Start with a PDF"}</h2>
                <p>{doc ? "Try one of these, or write your own question." : "Add a file on the left and it will be ready to chat in seconds."}</p>
                {doc && (
                  <div className="chips">
                    {SUGGESTIONS.map((s) => (
                      <button key={s} className="chip" onClick={() => sendQuestion(s)}>{s}</button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {messages.map((m, i) =>
              m.role === "user" ? (
                <div key={i} className="msg-user">{m.text}</div>
              ) : (
                <div key={i} className="msg-ai">
                  <span className="avatar">D</span>
                  <div className="ai-body">
                    <p>{m.text}</p>
                    {m.sources?.length > 0 && (
                      <details className="sources">
                        <summary>View sources ({m.sources.length})</summary>
                        {m.sources.map((s, j) => (
                          <blockquote key={j}>
                            <span className="page">p. {s.page}</span>
                            {s.text}
                          </blockquote>
                        ))}
                      </details>
                    )}
                  </div>
                </div>
              )
            )}

            {thinking && (
              <div className="msg-ai">
                <span className="avatar">D</span>
                <div className="dots"><i /><i /><i /></div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="composer-wrap">
          {error && <p className="error">{error}</p>}
          <form className="composer" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={doc ? "Ask a question about this document" : "Upload a PDF first"}
              disabled={!doc || thinking}
            />
            <button type="submit" aria-label="Send" disabled={!doc || thinking || !input.trim()}>
              <SendIcon />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}