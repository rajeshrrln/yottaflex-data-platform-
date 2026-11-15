import {
  Bell,
  Search,
  CircleHelp
} from "lucide-react";

export default function Header({ activePage }) {
  return (
    <header className="header">
      <div>
        <p className="breadcrumb">
          Workspace / Overview
        </p>

        <h2>{activePage}</h2>
      </div>

      <div className="header-actions">
        <div className="search-box">
          <Search size={16} />
          <input placeholder="Search workspace..." />
        </div>

        <button className="icon-button" aria-label="Help">
          <CircleHelp size={19} />
        </button>

        <button className="icon-button" aria-label="Notifications">
          <Bell size={19} />
          <span className="notification-dot" />
        </button>
      </div>
    </header>
  );
}