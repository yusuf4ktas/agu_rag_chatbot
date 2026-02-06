import React from "react";

export const HistoryView = ({ chatHistory, loadHistoryItem, clearHistory }) => {
  return (
    <>
      <header className="header">
        <div className="header-content">
          <div>
            <h1 className="title">Chat History</h1>
            <p className="subtitle">Review your previous conversations</p>
          </div>
        </div>
        {chatHistory.length > 0 && (
          <button className="clear-btn" onClick={clearHistory}>
            Clear History
          </button>
        )}
      </header>

      {chatHistory.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h3 className="empty-state-title">No history yet</h3>
          <p>Your chat history will appear here after you start asking questions.</p>
        </div>
      ) : (
        <div>
          {chatHistory.map((item) => (
            <div key={item.id} className="history-item" onClick={() => loadHistoryItem(item)}>
              <div className="history-query">{item.query}</div>
              <div className="history-answer">{item.answer}</div>
              <div className="history-time">{item.timestamp}</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export default HistoryView