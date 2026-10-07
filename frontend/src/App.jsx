import { useState, useRef, useEffect } from "react";
import { uploadDocument, askQuestion } from "./api";
import "./App.css";

export default function App() {
  // State: anything that changes what the screen shows
  const [doc, setDoc] = useState(null); // uploaded document info, or null
  const [uploading, setUploading] = useState(false);
  const [messages, setMessages] = useState([]); // [{ role, text, sources? }]
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false); // waiting for an answer
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  // Refs: handles to DOM elements, no re-render when they change
  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  // Scroll to the newest message whenever messages or thinking change
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
      setMessages([]); // a new document starts a fresh chat
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false); // runs on success and on failure
    }
  }

  async function handleSend(e) {
    e.preventDefault(); // stop the browser from reloading the page
    const question = input.trim();
    if (!question || thinking || !doc) return;

    // Show the user's message immediately, then wait for the answer
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

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  return (
    <div className="app">
      {/* Left panel: the document */}
      <aside className="sidebar">
        <h1 className="brand">DocGPT</h1>
        <p className="tagline">Upload a document, then ask questions about it.</p>

        <div
          className={`dropzone ${dragging ? "is-dragging" : ""}`}
          onClick={() => fileRef.current.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && fileRef.current.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf"
            hidden
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {uploading ? (
            <p>Reading your document...</p>
          ) : (
            <p>
              <strong>Choose a PDF</strong> or drop it here
            </p>
          )}
        </div>

        {doc && (
          <div className="doc-card">
            <p className="doc-name">{doc.filename}</p>
            <p className="doc-meta">{doc.chunks} sections indexed</p>
          </div>
        )}
      </aside>

      {/* Right panel: the chat */}
      <main className="chat">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty">
              {doc
                ? "Your document is ready. Ask a question below."
                : "Upload a PDF on the left to get started."}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`msg msg-${m.role}`}>
              <p>{m.text}</p>
              {m.sources?.length > 0 && (
                <details className="sources">
                  <summary>{m.sources.length} sources</summary>
                  {m.sources.map((s, j) => (
                    <blockquote key={j}>
                      <span className="page">Page {s.page}</span>
                      {s.text}
                    </blockquote>
                  ))}
                </details>
              )}
            </div>
          ))}

          {thinking && <div className="msg msg-assistant typing">Searching the document...</div>}
          <div ref={bottomRef} />
        </div>

        {error && <p className="error">{error}</p>}

        <form className="composer" onSubmit={handleSend}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={doc ? "Ask something about the document" : "Upload a PDF first"}
            disabled={!doc || thinking}
          />
          <button type="submit" disabled={!doc || thinking || !input.trim()}>
            Send
          </button>
        </form>
      </main>
    </div>
  );
}