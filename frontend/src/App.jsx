import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "./api";

const domains = ["general", "security", "compliance", "risk", "operations"];

export default function App() {
  const [health, setHealth] = useState(null);
  const [activeTab, setActiveTab] = useState("query");
  const [domain, setDomain] = useState("general");
  const [query, setQuery] = useState("List users");
  const [queryResult, setQueryResult] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [loadingScan, setLoadingScan] = useState(false);

  useEffect(() => {
    apiGet("/health").then(setHealth).catch(() => setHealth({ success: false }));
  }, []);

  const runQuery = async () => {
    setLoadingQuery(true);
    try {
      const result = await apiPost("/api/v1/query", { query, domain });
      setQueryResult(result);
    } finally {
      setLoadingQuery(false);
    }
  };

  const runScan = async () => {
    setLoadingScan(true);
    try {
      const result = await apiGet(`/api/v1/sentinel/scan?domain=${domain}`);
      setScanResult(result);
    } finally {
      setLoadingScan(false);
    }
  };

  const statusLabel = useMemo(() => {
    if (!health) return "Checking API";
    return health.success ? "API Online" : "API Offline";
  }, [health]);

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Nexus AI Platform</p>
          <h1>Natural Language Insights for Risk & Ops</h1>
          <p className="subhead">
            Ask questions in plain English, get explainable SQL, results, and actionable insights.
          </p>
        </div>
        <div className={`status-pill ${health?.success ? "ok" : "down"}`}>
          <span className="dot" />
          {statusLabel}
        </div>
      </header>

      <section className="controls">
        <div className="tab-group">
          <button
            className={activeTab === "query" ? "tab active" : "tab"}
            onClick={() => setActiveTab("query")}
          >
            NL2SQL Query
          </button>
          <button
            className={activeTab === "sentinel" ? "tab active" : "tab"}
            onClick={() => setActiveTab("sentinel")}
          >
            Sentinel Scan
          </button>
        </div>
        <div className="domain-select">
          <label htmlFor="domain">Domain</label>
          <select id="domain" value={domain} onChange={(e) => setDomain(e.target.value)}>
            {domains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
      </section>

      {activeTab === "query" && (
        <section className="grid">
          <div className="card">
            <h2>Ask a Question</h2>
            <p className="muted">Try: "Show failed logins this week" or "Sum transactions last 30 days".</p>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={4}
              placeholder="Type your question..."
            />
            <button className="primary" onClick={runQuery} disabled={loadingQuery}>
              {loadingQuery ? "Running..." : "Run Query"}
            </button>
          </div>
          <div className="card">
            <h2>Result</h2>
            <pre className="output">{JSON.stringify(queryResult, null, 2)}</pre>
          </div>
        </section>
      )}

      {activeTab === "sentinel" && (
        <section className="grid">
          <div className="card">
            <h2>Run Sentinel Scan</h2>
            <p className="muted">Automated missions with risk scoring and correlations.</p>
            <button className="primary" onClick={runScan} disabled={loadingScan}>
              {loadingScan ? "Scanning..." : "Start Scan"}
            </button>
          </div>
          <div className="card">
            <h2>Scan Output</h2>
            <pre className="output">{JSON.stringify(scanResult, null, 2)}</pre>
          </div>
        </section>
      )}

      <footer className="footer">
        <span>Environment: {health?.data?.env || "unknown"}</span>
        <span>Build: prototype</span>
      </footer>
    </div>
  );
}
