"use client";

import { FormEvent, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type Repo = {
  id: string; owner: string; name: string; url: string; branch: string;
  commit_sha?: string; status: string; file_count: number; created_at: string;
  chunk_count?: number;
};
type Citation = {
  file_path: string; start_line: number; end_line: number;
  content: string; score?: number;
};
type ChatResult = { answer: string; citations: Citation[] };

export default function Home() {
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selected, setSelected] = useState<Repo | null>(null);
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<{ question: string; result: ChatResult }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadRepos() {
    try {
      const res = await fetch(`${API}/api/repositories`);
      if (!res.ok) throw new Error("Backend request failed");
      const data: Repo[] = await res.json();
      setRepos(data);
      if (!selected && data.length) setSelected(data[0]);
    } catch {
      setError("Cannot connect to the API. Start the FastAPI backend on port 8000.");
    }
  }
  useEffect(() => { void loadRepos(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function importRepo(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const res = await fetch(`${API}/api/repositories`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, branch: branch || "main" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Import failed");
      await loadRepos();
      setSelected(data);
      setHistory([]);
      setUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally { setBusy(false); }
  }

  async function askQuestion(e: FormEvent) {
    e.preventDefault();
    if (!selected || !question.trim()) return;
    const q = question.trim(); setQuestion(""); setBusy(true); setError("");
    try {
      const res = await fetch(`${API}/api/repositories/${selected.id}/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Question failed");
      setHistory(old => [...old, { question: q, result: data as ChatResult }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed");
      setQuestion(q);
    } finally { setBusy(false); }
  }

  async function deleteRepo(repo: Repo) {
    if (!confirm(`Delete the local index for ${repo.owner}/${repo.name}?`)) return;
    try {
      await fetch(`${API}/api/repositories/${repo.id}`, { method: "DELETE" });
      if (selected?.id === repo.id) { setSelected(null); setHistory([]); }
      await loadRepos();
    } catch { setError("Could not delete repository."); }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">⌘ CodeBase AI</div>
        <div className="pill">RAG · Repository intelligence</div>
      </header>

      <section className="hero">
        <div className="eyebrow">Your codebase, searchable</div>
        <h1>Ask your code<br />anything.</h1>
        <p className="muted">Connect a public GitHub repository. Get answers grounded in its source code, with file and line references.</p>
        <form className="formrow" onSubmit={importRepo}>
          <input aria-label="GitHub repository URL" placeholder="https://github.com/owner/repository" value={url} onChange={e => setUrl(e.target.value)} required />
          <input aria-label="Branch" placeholder="Branch" value={branch} onChange={e => setBranch(e.target.value)} style={{maxWidth:140, flex:"0 0 140px"}} />
          <button className="primary" disabled={busy}>{busy ? "Working…" : "Index repository"}</button>
        </form>
        {error && <div className="error">{error}</div>}
      </section>

      <section className="grid">
        <aside className="panel">
          <h2>Repositories</h2>
          {repos.length === 0 && <p className="muted">No repositories yet. Import a public GitHub repository above.</p>}
          {repos.map(repo => (
            <div key={repo.id} className={`repo ${selected?.id === repo.id ? "active" : ""}`} onClick={() => {setSelected(repo); setHistory([]);}}>
              <strong>{repo.owner}/{repo.name}</strong>
              <div className="status">{repo.status} · {repo.file_count} files</div>
              <div className="small">Branch: {repo.branch}</div>
              <div style={{display:"flex", gap:8, marginTop:10}}>
                <a className="small" href={repo.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}>Open GitHub ↗</a>
                <button className="secondary" onClick={e => {e.stopPropagation(); void deleteRepo(repo);}}>Delete</button>
              </div>
            </div>
          ))}
          <p className="small">MVP supports public repositories only.</p>
        </aside>

        <section className="panel">
          <h2>{selected ? `${selected.owner}/${selected.name}` : "Repository chat"}</h2>
          {!selected ? <p className="muted">Import a repository to start asking questions.</p> : <>
            <p className="small">Indexed commit: <code>{selected.commit_sha?.slice(0, 12) || "unknown"}</code></p>
            <div className="chatbox">
              {history.length === 0 && <div className="bubble answerbubble muted">Try asking: “Where is the application initialized?” or “Explain the authentication flow.”</div>}
              {history.map((item, idx) => (
                <div key={idx}>
                  <div className="bubble userbubble">{item.question}</div>
                  <div className="bubble answerbubble" style={{marginTop:8}}>{item.result.answer}
                    <div className="citations">
                      {item.result.citations.map((c, i) => (
                        <details className="citation" key={`${c.file_path}-${c.start_line}-${i}`}>
                          <summary><code>{c.file_path}:{c.start_line}-{c.end_line}</code> <span className="small">· similarity {c.score ?? "n/a"}</span></summary>
                          <pre>{c.content}</pre>
                        </details>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <form className="formrow" onSubmit={askQuestion}>
              <input aria-label="Question" placeholder="Ask a question about this repository…" value={question} onChange={e => setQuestion(e.target.value)} required />
              <button className="primary" disabled={busy}>{busy ? "Thinking…" : "Ask"}</button>
            </form>
          </>}
        </section>
      </section>
      <footer className="small" style={{marginTop:24}}>CodeBase AI · Read-only repository analysis · Do not upload repositories you are not authorized to access.</footer>
    </main>
  );
}
