import { useEffect, useState } from "react";
import { apiGet, apiPost } from "./api";

export default function App() {
  const [health, setHealth] = useState(null);
  const [query, setQuery] = useState("List users");
  const [queryResult, setQueryResult] = useState(null);
  const [scanResult, setScanResult] = useState(null);

  useEffect(() => {
    apiGet("/health").then(setHealth).catch(() => setHealth({ success: false }));
  }, []);

  const runQuery = async () => {
    const result = await apiPost("/api/v1/query", { query, domain: "general" });
    setQueryResult(result);
  };

  const runScan = async () => {
    const result = await apiGet("/api/v1/sentinel/scan?domain=general");
    setScanResult(result);
  };

  return (
    <div className="app">
      <header className="top-bar">
        <div>
          <h1>Nexus AI</h1>
          <p>NL2SQL + Sentinel prototype</p>
        </div>
        <div className={health?.success ? "status ok" : "status down"}>
          {health?.success ? "API OK" : "API DOWN"}
        </div>
      </header>

      <section className="panel">
        <h2>NL2SQL Query</h2>
        <div className="row">
          <input value={query} onChange={(e) => setQuery(e.target.value)} />
          <button onClick={runQuery}>Run Query</button>
        </div>
        <pre className="output">{JSON.stringify(queryResult, null, 2)}</pre>
      </section>

      <section className="panel">
        <h2>Sentinel Scan</h2>
        <button onClick={runScan}>Run Scan</button>
        <pre className="output">{JSON.stringify(scanResult, null, 2)}</pre>
      </section>
    </div>
  );
}
