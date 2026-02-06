import {BotIcon, HomeIcon, LinkIcon, ExternalLinkIcon, HistoryIcon} from "./Icons.jsx";

const Sidebar = ({ currentPage, setCurrentPage, showSidebar, resources }) => {
  return (
    <aside className={`sidebar ${showSidebar ? 'show' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="logo"><BotIcon /></div>
          <h2 className="sidebar-title">AGU Chatbot</h2>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          <div className="nav-label">Navigation</div>
          <div
            className={`nav-item ${currentPage === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentPage('chat')}
          >
            <HomeIcon />
            <span>Chat</span>
          </div>
          <div
            className={`nav-item ${currentPage === 'history' ? 'active' : ''}`}
            onClick={() => setCurrentPage('history')}
          >
            <HistoryIcon />
            <span>History</span>
          </div>
          <div
            className={`nav-item ${currentPage === 'resources' ? 'active' : ''}`}
            onClick={() => setCurrentPage('resources')}
          >
            <LinkIcon />
            <span>Resources</span>
          </div>
        </div>

        <div className="nav-section">
          <div className="nav-label">Quick Links</div>
          {resources.map((resource, i) => (
            <a
              key={i}
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="resource-link"
            >
              <div className="resource-link-content">
                {resource.icon}
                <span>{resource.name}</span>
              </div>
              <ExternalLinkIcon />
            </a>
          ))}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar