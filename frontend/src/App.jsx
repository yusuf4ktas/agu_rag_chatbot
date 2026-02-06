import React, { useState } from "react";
import "./App.css";

import Sidebar from "./components/Sidebar";
import { HomeIcon, BookIcon, LinkIcon } from "./components/Icons";

// --- Views ---
import ChatView from "./views/ChatView";
import HistoryView from "./views/HistoryView";
import ResourcesView from "./views/ResourcesView";

const API_URL = "http://127.0.0.1:8000/chat";

export default function App() {
  const [currentPage, setCurrentPage] = useState("chat");
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [showSidebar, setShowSidebar] = useState(true);

  const resources = [
    { name: "AGU Website", url: "https://w3.agu.edu.tr/", icon: <HomeIcon /> },
    { name: "Student Portal", url: "https://oidb-tr.agu.edu.tr/", icon: <BookIcon /> },
    { name: "Academic Calendar", url: "https://oidb-tr.agu.edu.tr/uploads/akademik_takvim/2026/10.09.2025%20Akademik%20Takvim%20Tasla%C4%9F%C4%B1%20%20T.pdf", icon: <BookIcon /> },
    { name: "Library", url: "https://kutuphane.agu.edu.tr", icon: <BookIcon /> },
    { name: "Career Center", url: "https://career.agu.edu.tr/", icon: <LinkIcon /> },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const currentQuery = query;
    setLoading(true);
    setAnswer("");
    setSources([]);
    setError(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: currentQuery }),
      });
      if (!response.ok) throw new Error(`API error: ${response.status} ${response.statusText}`);
      const data = await response.json();

      const newAnswer = data.answer || "";
      const newSources = Array.isArray(data.sources) ? data.sources : [];

      setAnswer(newAnswer);
      setSources(newSources);

      setChatHistory(prev => [{
        id: Date.now(),
        query: currentQuery,
        answer: newAnswer,
        sources: newSources,
        timestamp: new Date().toLocaleString()
      }, ...prev].slice(0, 10));

    } catch (err) {
      console.error(err);
      setError("Failed to get an answer. Please check the console and ensure the backend API is running.");
    } finally {
      setLoading(false);
      setQuery("");
    }
  };

  const loadHistoryItem = (item) => {
    setAnswer(item.answer);
    setSources(item.sources);
    setCurrentPage("chat");
  };

  const clearHistory = () => {
    setChatHistory([]);
    setAnswer("");
    setSources([]);
  };

  return (
    <div className="page">
      {/* Background accents */}
      <div className="bg-accent" aria-hidden>
        <div className="blob1" />
        <div className="blob2" />
        <div className="blob3" />
      </div>

      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        showSidebar={showSidebar}
        resources={resources}
      />

      <main className="main-content">
        <div className="container">
          {currentPage === 'chat' && (
            <ChatView
              answer={answer}
              sources={sources}
              loading={loading}
              error={error}
              query={query}
              setQuery={setQuery}
              handleSubmit={handleSubmit}
            />
          )}

          {currentPage === 'history' && (
            <HistoryView
              chatHistory={chatHistory}
              loadHistoryItem={loadHistoryItem}
              clearHistory={clearHistory}
            />
          )}

          {currentPage === 'resources' && (
            <ResourcesView
              resources={resources}
              goToChat={() => setCurrentPage('chat')}
            />
          )}
        </div>
      </main>
    </div>
  );
}