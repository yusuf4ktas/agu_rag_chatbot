import React from "react";
import {LoaderIcon, SendIcon} from "../components/Icons.jsx";
import SourcePill from "../components/SourcePill.jsx";

const ChatView = ({
  answer,
  sources,
  loading,
  error,
  query,
  setQuery,
  handleSubmit
}) => {
  return (
    <>
      <header className="header">
        <div className="header-content">
          <div>
            <h1 className="title">AGU College Chatbot</h1>
            <p className="subtitle">Ask anything about AGU. Fast, friendly, and accurate.</p>
          </div>
        </div>
      </header>

      {/* Answer Area */}
      <section className="section-wrapper">
        <label className="section-label">Answer</label>
        <div className="card answer-box" aria-live="polite" aria-busy={loading}>
          {loading ? (
            <div className="loader-container">
              <LoaderIcon />
              <span className="loader-text">Generating answer...</span>
            </div>
          ) : answer ? (
            <div className="answer-text">{answer}</div>
          ) : (
            <p className="answer-placeholder">Your answer will appear here...</p>
          )}
        </div>
      </section>

      {/* Sources Area */}
      {sources.length > 0 && (
        <section className="section-wrapper">
          <label className="section-label">Sources</label>
          <div className="sources">
            {sources.map((src, i) => (
              <SourcePill key={i} src={src} />
            ))}
          </div>
        </section>
      )}

      {/* Error Area */}
      {error && (
        <div role="alert" className="alert">
          <p className="alert-title">Error</p>
          <p className="alert-text">{error}</p>
        </div>
      )}

      {/* Input Form Area */}
      <section>
        <form onSubmit={handleSubmit} className="form">
          <label className="section-label" htmlFor="query">Ask a question</label>
          <div className="input-row">
            <input
              id="query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What is Erasmus+ study mobility?"
              className="input"
              disabled={loading}
              autoComplete="off"
              aria-label="Your question"
            />
            <button type="submit" className="btn" disabled={loading} aria-label={loading ? "Sending" : "Send"}>
              {loading ? <LoaderIcon /> : <SendIcon />}
              <span className="sr-only">Send</span>
            </button>
          </div>
          <p className="help">Powered by AGU knowledge. Be concise and specific in your question for best results.</p>
        </form>
      </section>
    </>
  );
};

export default ChatView;