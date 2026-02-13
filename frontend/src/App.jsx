import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiPost } from "./api";

const domains = ["general", "security", "compliance", "risk", "operations"];
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

function toCsv(rows) {
  if (!rows || rows.length === 0) return "";
  const headers = Array.from(
    rows.reduce((acc, row) => {
      Object.keys(row).forEach((key) => acc.add(key));
      return acc;
    }, new Set())
  );
  const lines = [headers.join(",")];
  rows.forEach((row) => {
    const line = headers.map((key) => {
      const raw = row[key] ?? "";
      const escaped = String(raw).replace(/"/g, '""');
      return `"${escaped}"`;
    });
    lines.push(line.join(","));
  });
  return lines.join("\n");
}

function downloadCsv(rows, filename) {
  const csv = toCsv(rows);
  if (!csv) return;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function DataTable({ rows }) {
  if (!rows || rows.length === 0) {
    return <div className="empty">No rows returned.</div>;
  }
  const headers = Array.from(
    rows.reduce((acc, row) => {
      Object.keys(row).forEach((key) => acc.add(key));
      return acc;
    }, new Set())
  );
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {headers.map((h) => (
                <td key={h}>{String(row[h] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function BarChart({ rows, xKey, yKey }) {
  if (!rows || rows.length === 0 || !xKey || !yKey) return null;
  const max = Math.max(...rows.map((row) => Number(row[yKey] || 0)), 1);
  return (
    <div className="bar-chart">
      {rows.slice(0, 10).map((row, idx) => {
        const value = Number(row[yKey] || 0);
        const width = Math.round((value / max) * 100);
        return (
          <div className="bar-row" key={`${row[xKey]}-${idx}`}>
            <span className="bar-label">{String(row[xKey])}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${width}%` }} />
            </div>
            <span className="bar-value">{value}</span>
          </div>
        );
      })}
    </div>
  );
}

function RiskGauge({ score }) {
  const normalized = Math.min(Math.max(score ?? 0, 0), 100);
  const angle = (normalized / 100) * 180;
  return (
    <div className="gauge">
      <svg viewBox="0 0 200 110">
        <path d="M10 100 A90 90 0 0 1 190 100" className="gauge-track" />
        <path
          d="M10 100 A90 90 0 0 1 190 100"
          className="gauge-value"
          style={{ strokeDasharray: `${(angle / 180) * 283} 283` }}
        />
        <circle cx="100" cy="100" r="6" className="gauge-center" />
        <line
          x1="100"
          y1="100"
          x2={100 + 80 * Math.cos((Math.PI * (180 - angle)) / 180)}
          y2={100 - 80 * Math.sin((Math.PI * (180 - angle)) / 180)}
          className="gauge-needle"
        />
      </svg>
      <div className="gauge-value-text">{normalized}</div>
      <div className="gauge-label">Risk Score</div>
    </div>
  );
}

function ChatMessage({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`chat-message ${isUser ? "user" : "assistant"}`}>
      <div className="chat-bubble">
        <p>{message.text}</p>
        {message.meta && message.meta.type === "query" && (
          <div className="chat-meta">
            <div className="chip">SQL</div>
            <code>{message.meta.sql || ""}</code>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [activeTab, setActiveTab] = useState("query");
  const [domain, setDomain] = useState("general");
  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [scanEvents, setScanEvents] = useState([]);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [loadingScan, setLoadingScan] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Ask a question about users, logins, or transactions." }
  ]);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    apiGet("/health").then(setHealth).catch(() => setHealth({ success: false }));
  }, []);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const runQuery = async () => {
    if (!query.trim()) return;
    const userMessage = { role: "user", text: query.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setLoadingQuery(true);
    try {
      const result = await apiPost("/api/v1/query", { query, domain });
      setQueryResult(result);
      const resultData = result?.data?.result;
      const assistantMessage = {
        role: "assistant",
        text: resultData?.clarification_needed
          ? `I need more info: ${resultData?.clarification_questions?.join(" ")}`
          : `Here is what I found in ${domain}.`,
        meta: { type: "query", sql: resultData?.sql }
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setQuery("");
    } finally {
      setLoadingQuery(false);
    }
  };

  const startStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    const es = new EventSource(`${API_BASE}/api/v1/sentinel/scan/stream?domain=${domain}`);
    eventSourceRef.current = es;
    setScanEvents([]);
    es.addEventListener("status", (event) => {
      setScanEvents((prev) => [...prev, { type: "status", payload: JSON.parse(event.data) }]);
    });
    es.addEventListener("mission", (event) => {
      setScanEvents((prev) => [...prev, { type: "mission", payload: JSON.parse(event.data) }]);
    });
    es.addEventListener("deep_dive", (event) => {
      setScanEvents((prev) => [...prev, { type: "deep_dive", payload: JSON.parse(event.data) }]);
    });
    es.addEventListener("correlation", (event) => {
      setScanEvents((prev) => [...prev, { type: "correlation", payload: JSON.parse(event.data) }]);
    });
    es.addEventListener("complete", (event) => {
      const payload = JSON.parse(event.data);
      setScanResult({ success: true, data: payload });
      setLoadingScan(false);
      es.close();
    });
    es.onerror = () => {
      setLoadingScan(false);
      es.close();
    };
  };

  const runScan = async () => {
    setLoadingScan(true);
    setScanResult(null);
    startStream();
  };

  const statusLabel = useMemo(() => {
    if (!health) return "Checking API";
    return health.success ? "API Online" : "API Offline";
  }, [health]);

  const resultData = queryResult?.data?.result;
  const scanData = scanResult?.data;

  return (
    <div className="app">
      <div className="sky-glow" />
      <header className="hero">
        <div>
          <p className="eyebrow">Nexus AI Platform</p>
          <h1>Nightwatch Analytics</h1>
          <p className="subhead">
            Explore your data with guided NL2SQL, Sentinel scans, and actionable insights.
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
            Chat Query
          </button>
          <button
            className={activeTab === "sentinel" ? "tab active" : "tab"}
            onClick={() => setActiveTab("sentinel")}
          >
            Sentinel Dashboard
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

      <section className="env-panel">
        <div>
          <h3>Environment</h3>
          <p>API: {API_BASE}</p>
          <p>Mode: {health?.data?.env || "unknown"}</p>
        </div>
        <div className="env-grid">
          <MetricCard label="Domain" value={domain} />
          <MetricCard label="Status" value={health?.success ? "Online" : "Offline"} />
        </div>
      </section>

      {activeTab === "query" && (
        <section className="grid">
          <div className="card chat-card">
            <h2>Chat</h2>
            <div className="chat-window">
              {messages.map((message, idx) => (
                <ChatMessage key={idx} message={message} />
              ))}
            </div>
            <div className="chat-input">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about users, transactions, logins..."
              />
              <button className="primary" onClick={runQuery} disabled={loadingQuery}>
                {loadingQuery ? "Running..." : "Send"}
              </button>
            </div>
          </div>

          <div className="card">
            <h2>Query Results</h2>
            {resultData?.sql && (
              <div className="sql-box">
                <span>SQL</span>
                <code>{resultData.sql}</code>
              </div>
            )}
            {resultData?.insights && resultData.insights.length > 0 && (
              <div className="insights">
                {resultData.insights.map((insight, idx) => (
                  <div key={idx} className="insight">
                    {insight}
                  </div>
                ))}
              </div>
            )}
            <div className="viz-block">
              <h4>Visualization</h4>
              {resultData?.visualization?.type === "metric" && (
                <MetricCard
                  label={resultData.visualization.value}
                  value={
                    resultData?.rows?.[0]?.count ??
                    resultData?.rows?.[0]?.total_amount ??
                    resultData?.rows?.[0]?.avg_amount ??
                    "-"
                  }
                />
              )}
              {resultData?.visualization?.type === "bar" && (
                <BarChart
                  rows={resultData?.rows || []}
                  xKey={resultData.visualization.x}
                  yKey={resultData.visualization.y}
                />
              )}
            </div>
            <div className="table-header">
              <h4>Data Table</h4>
              <button
                className="ghost"
                onClick={() => downloadCsv(resultData?.rows || [], "query-results.csv")}
              >
                Export CSV
              </button>
            </div>
            <DataTable rows={resultData?.rows || []} />
          </div>
        </section>
      )}

      {activeTab === "sentinel" && (
        <section className="grid">
          <div className="card">
            <h2>Sentinel Scan</h2>
            <p className="muted">Streamed missions with risk scoring and correlation highlights.</p>
            <button className="primary" onClick={runScan} disabled={loadingScan}>
              {loadingScan ? "Scanning..." : "Start Scan"}
            </button>
            <div className="scan-events">
              {scanEvents.map((event, idx) => (
                <div key={idx} className="scan-event">
                  <span>{event.type}</span>
                  <code>{formatJson(event.payload)}</code>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <h2>Risk Overview</h2>
            <RiskGauge score={scanData?.risk_score ?? 0} />
            <div className="insights">
              <div className="insight">{scanData?.narrative || "No scan yet."}</div>
            </div>
            <div className="table-header">
              <h4>Findings</h4>
              <button
                className="ghost"
                onClick={() => downloadCsv(scanData?.findings || [], "sentinel-findings.csv")}
              >
                Export CSV
              </button>
            </div>
            <DataTable rows={scanData?.findings || []} />
          </div>
        </section>
      )}

      <footer className="footer">
        <span>Environment: {health?.data?.env || "unknown"}</span>
        <span>API: {API_BASE}</span>
      </footer>
    </div>
  );
}
