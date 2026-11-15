
import React, { useState } from "react";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";

import Dashboard from "./pages/Dashboard";
import PipelineConfiguration from "./pages/PipelineConfiguration";
import DatasetManagement from "./pages/DatasetManagement";
import DataQuality from "./pages/DataQuality";
import PipelineRuns from "./pages/PipelineRuns";

export default function App() {
  const [activePage, setActivePage] = useState("Dashboard");

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return <Dashboard />;

      case "Pipelines":
        return <PipelineConfiguration />;

      case "Datasets":
        return <DatasetManagement />;

      case "Pipeline Runs":
        return <PipelineRuns />;

      case "Data Quality":
        return <DataQuality />;

      default:
        return (
          <section className="coming-soon">
            <h2>{activePage}</h2>
            <p>
              This module will be implemented in the next development phase.
            </p>
          </section>
        );
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
      />

      <main className="main-content">
        <Header activePage={activePage} />
        {renderPage()}
      </main>
    </div>
  );
}
