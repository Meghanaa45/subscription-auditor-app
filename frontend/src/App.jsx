import React, { useEffect, useState } from "react";
import UploadPanel from "./components/UploadPanel.jsx";
import StatementTotal from "./components/StatementTotal.jsx";
import LedgerList from "./components/LedgerList.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import { checkHealth, runAudit, runSampleAudit } from "./api/client.js";

export default function App() {
  const [health, setHealth] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable", agent_configured: false }));
  }, []);

  async function handleFilesChosen(files) {
    setLoading(true);
    setError(null);
    try {
      const audit = await runAudit(files);
      setResult(audit);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUseSample() {
    setLoading(true);
    setError(null);
    try {
      const audit = await runSampleAudit();
      setResult(audit);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="masthead">
        <div className="masthead__eyebrow">Subscription Auditor</div>
        <h1 className="masthead__title">Find what's quietly draining your account.</h1>
        <p className="masthead__sub">
          Upload a bank statement export. Every recurring charge gets found, priced, and checked
          for silent increases &mdash; nothing here is guessed.
        </p>
      </header>

      {health?.status === "unreachable" && (
        <div className="banner banner--error">
          Can't reach the backend API. Make sure it's running (see the README) and that
          VITE_API_URL points to it.
        </div>
      )}

      {!result && (
        <UploadPanel onFilesChosen={handleFilesChosen} onUseSample={handleUseSample} loading={loading} />
      )}

      {error && <div className="banner banner--error">{error}</div>}

      {result && (
        <div className="results">
          <div className="results__ledger-column">
            <StatementTotal summary={result.summary} />
            <LedgerList subscriptions={result.subscriptions} />
            <button className="link-button" onClick={() => setResult(null)}>
              &larr; Run a different audit
            </button>
          </div>
          <div className="results__chat-column">
            <ChatPanel auditId={result.audit_id} agentConfigured={Boolean(health?.agent_configured)} />
          </div>
        </div>
      )}
    </div>
  );
}
