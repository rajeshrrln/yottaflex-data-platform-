import {
  LayoutDashboard,
  Workflow,
  Database,
  Activity,
  ShieldCheck,
  Settings,
  Layers
} from "lucide-react";

const navigation = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Pipelines", icon: Workflow },
  { name: "Datasets", icon: Database },
  { name: "Pipeline Runs", icon: Activity },
  { name: "Data Quality", icon: ShieldCheck }
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <Layers size={23} />
        </div>

        <div>
          <h2>YottaFlex</h2>
          <span>DATA PLATFORM</span>
        </div>
      </div>

      <div className="nav-section">
        <p className="nav-heading">WORKSPACE</p>

        {navigation.map(({ name, icon: Icon }) => (
          <button
            key={name}
            className={`nav-item ${
              activePage === name ? "active" : ""
            }`}
            onClick={() => onNavigate(name)}
          >
            <Icon size={18} />
            <span>{name}</span>
          </button>
        ))}
      </div>

      <div className="sidebar-bottom">
        <button className="nav-item">
          <Settings size={18} />
          <span>Settings</span>
        </button>

        <div className="user-profile">
          <div className="avatar">DE</div>
          <div>
            <strong>Data Engineer</strong>
            <span>Administrator</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
