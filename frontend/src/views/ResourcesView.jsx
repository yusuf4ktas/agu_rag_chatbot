import React from "react";
import {HomeIcon} from "../components/Icons.jsx";

export const ResourcesView = ({ resources, goToChat }) => {
  return (
    <>
      <header className="header">
        <div className="header-content">
          <div>
            <h1 className="title">AGU Resources</h1>
            <p className="subtitle">Quick access to important university resources</p>
          </div>
        </div>
      </header>

      <div className="resource-grid">
        {resources.map((resource, i) => (
          <a
            key={i}
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="resource-card"
          >
            <div className="resource-card-icon">
              {resource.icon}
            </div>
            <h3 className="resource-card-title">{resource.name}</h3>
            <div className="resource-card-url">{resource.url}</div>
          </a>
        ))}
      </div>

      <section className="need-help-section">
        <label className="section-label">Need help?</label>
        <div className="card">
          <p className="help-text">
            Can't find what you're looking for? Go back to the chat page and ask me any question about AGU.
            I'm here to help with admissions, programs, campus life, and more!
          </p>
          <button
            className="btn btn-help"
            onClick={goToChat}
          >
            <HomeIcon />
            Go to Chat
          </button>
        </div>
      </section>
    </>
  );
};

export default ResourcesView