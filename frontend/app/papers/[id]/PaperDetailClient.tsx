"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import AddPaperButton from "@/components/papers/AddPaperButton";
import HeaderHeightObserver from "@/components/papers/HeaderHeightObserver";
import PdfCanvasViewer from "@/components/papers/PdfCanvasViewer";

type ReadingStatus = "INBOX" | "TO_READ" | "READING" | "READ";
type Metadata = {
  status: ReadingStatus; title: string | null; authors: string[]; affiliations: string[];
  year: number | null; conference: string | null; journal: string | null; doi: string | null;
  volume: string | null; month: string | null; number: string | null; pages: string | null;
  abstract: string | null; publisher_url: string | null; project_page: string | null;
  keywords: string[]; updated_at: string | null;
};
type MetadataResponse = { metadata: Metadata };
type NoteResponse = { content: string };

const emptyMetadata: Metadata = {
  status: "INBOX", title: null, authors: [], affiliations: [], year: null, conference: null,
  journal: null, volume: null, month: null, number: null, pages: null, doi: null,
  abstract: null, publisher_url: null, project_page: null, keywords: [], updated_at: null,
};

function encodePath(path: string): string {
  return path.split("/").filter(Boolean).map(encodeURIComponent).join("/");
}

function parseCommaSeparated(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export default function PaperDetailClient({ id }: { id: string }) {
  const relativePath = useMemo(() => {
    let decoded = id;
    try { decoded = decodeURIComponent(id); } catch { /* use raw id */ }
    return decoded.toLowerCase().endsWith(".pdf") ? decoded : `${decoded}.pdf`;
  }, [id]);
  const encodedPath = useMemo(() => encodePath(relativePath), [relativePath]);
  const metadataUrl = `/api/v1/papers/local-metadata/${encodedPath}`;
  const notesUrl = `/api/v1/papers/local-notes/${encodedPath}`;
  const pdfUrl = `/api/v1/papers/local-files/content/${encodedPath}`;
  const [metadata, setMetadata] = useState<Metadata>(emptyMetadata);
  const [memo, setMemo] = useState("");
  const [memoMode, setMemoMode] = useState<"editor" | "viewer">("editor");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState("Loading…");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [metadataBusy, setMetadataBusy] = useState(false);
  const [metadataMessage, setMetadataMessage] = useState<string | null>(null);
  const [metadataDraft, setMetadataDraft] = useState<Metadata>(emptyMetadata);
  const [metadataListInputs, setMetadataListInputs] = useState({ authors: "", keywords: "" });
  const lastSavedMemo = useRef("");
  const memoReady = useRef(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch(metadataUrl, { cache: "no-store" }).then((response) => { if (!response.ok) throw new Error(); return response.json() as Promise<MetadataResponse>; }),
      fetch(notesUrl, { cache: "no-store" }).then((response) => { if (!response.ok) throw new Error(); return response.json() as Promise<NoteResponse>; }),
    ]).then(([metadataData, noteData]) => {
      if (cancelled) return;
      setMetadata(metadataData.metadata);
      setMetadataDraft(metadataData.metadata);
      setMetadataListInputs({
        authors: metadataData.metadata.authors.join(", "),
        keywords: metadataData.metadata.keywords.join(", "),
      });
      setMemo(noteData.content);
      lastSavedMemo.current = noteData.content;
      memoReady.current = true;
      setSaveState("Saved");
    }).catch(() => { if (!cancelled) setError("Paper data could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [metadataUrl, notesUrl]);

  useEffect(() => {
    if (!memoReady.current || memo === lastSavedMemo.current) return;
    setSaveState("Saving…");
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch(notesUrl, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: memo }) });
        if (!response.ok) throw new Error();
        const data = (await response.json()) as NoteResponse;
        lastSavedMemo.current = data.content;
        setSaveState("Saved");
      } catch { setSaveState("Save error"); }
    }, 800);
    return () => window.clearTimeout(timer);
  }, [memo, notesUrl]);

  async function saveMetadata(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMetadataMessage(null);
    setMetadataBusy(true);
    try {
      const response = await fetch(metadataUrl, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...metadataDraft,
          authors: parseCommaSeparated(metadataListInputs.authors),
          keywords: parseCommaSeparated(metadataListInputs.keywords),
          updated_at: null,
        }),
      });
      if (!response.ok) throw new Error();
      const data = (await response.json()) as MetadataResponse;
      setMetadata(data.metadata);
      setMetadataDraft(data.metadata);
      setMetadataListInputs({ authors: data.metadata.authors.join(", "), keywords: data.metadata.keywords.join(", ") });
      setSettingsOpen(false);
    } catch { setMetadataMessage("Metadata could not be saved."); }
    finally { setMetadataBusy(false); }
  }

  function setDraftField(field: keyof Metadata, value: string) {
    if (field === "authors" || field === "keywords") {
      setMetadataListInputs((current) => ({ ...current, [field]: value }));
    } else if (field === "affiliations") {
      setMetadataDraft((draft) => ({ ...draft, [field]: value.split(",").map((item) => item.trim()).filter(Boolean) }));
    } else if (field === "year") {
      setMetadataDraft((draft) => ({ ...draft, year: value ? Number(value) : null }));
    } else {
      setMetadataDraft((draft) => ({ ...draft, [field]: value || null }));
    }
  }

  async function autofillMetadata() {
    if (!metadataDraft.doi?.trim()) { setMetadataMessage("DOI is required."); return; }
    setMetadataBusy(true);
    setMetadataMessage(null);
    try {
      const response = await fetch("/api/v1/metadata/doi", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doi: metadataDraft.doi }),
      });
      if (!response.ok) throw new Error();
      const data = await response.json() as {
        title: string | null; authors: string[]; affiliations: string[]; year: number | null;
        journal: string | null; doi: string | null; abstract: string | null; publisher_url: string | null;
      };
      setMetadataDraft((draft) => ({ ...draft, title: data.title, authors: data.authors,
        affiliations: data.affiliations, year: data.year, journal: data.journal,
        conference: data.journal, doi: data.doi || draft.doi, abstract: data.abstract,
        publisher_url: data.publisher_url }));
      setMetadataListInputs((current) => ({ ...current, authors: data.authors.join(", ") }));
      setMetadataMessage("Metadata filled. Save to apply changes.");
    } catch { setMetadataMessage("Metadata could not be fetched."); }
    finally { setMetadataBusy(false); }
  }

  const title = metadata.title || relativePath.replace(/\.pdf$/i, "");
  const venue = [metadata.year, metadata.conference || metadata.journal].filter(Boolean).join(" ");
  const memoToggleIcon = memoMode === "editor" ? "/library-icons/edit.svg" : "/library-icons/view.svg";

  return (
    <main className="lib-page paper-page">
      <header className="lib-topbar">
        <HeaderHeightObserver />
        <Link className="lib-brand" href="/library">Research Paper Manager</Link>
        <div className="lib-filters" aria-label="paper information">
          <div className="lib-input-shell" title={title}>{title}</div>
          <div className="lib-input-shell">{metadata.year || "Year"}</div>
          <div className="lib-input-shell">{metadata.conference || metadata.journal || "Conference/Journal"}</div>
          <div className="lib-input-shell">{metadata.keywords.join(", ") || "Keywords"}</div>
        </div>
        <div className="lib-actions"><AddPaperButton /><button className="lib-icon-button is-framed" onClick={() => { setMetadataDraft(metadata); setMetadataListInputs({ authors: metadata.authors.join(", "), keywords: metadata.keywords.join(", ") }); setMetadataMessage(null); setSettingsOpen(true); }} type="button" aria-label="edit metadata"><img src="/library-icons/settings.svg" alt="Settings" className="lib-icon-asset is-settings" /></button></div>
      </header>

      <div className="lib-layout paper-layout">
        <section className="paper-content" aria-label="paper view and memo">
          {loading && <p className="paper-status">Loading paper…</p>}
          {error && <p className="paper-status is-error">{error}</p>}
          <div className="paper-header-block">
            <h1 className="paper-detail-title" title={title}>{title}</h1>
            <p className="paper-authors">{metadata.authors.length ? metadata.authors.join(", ") : "Authors: –"}</p>
            <div className="paper-meta-row"><p className="paper-meta">{venue || "Year / Conference: –"}</p></div>
            {metadata.publisher_url && <p className="paper-meta">URL: <a href={metadata.publisher_url} rel="noreferrer" target="_blank">{metadata.publisher_url}</a></p>}
            {metadata.project_page && <p className="paper-meta">Project page: <a href={metadata.project_page} rel="noreferrer" target="_blank">{metadata.project_page}</a></p>}
            {metadata.doi && <p className="paper-meta">DOI: {metadata.doi}</p>}
            <p className="paper-meta">Keywords: {metadata.keywords.join(", ") || "–"}</p>
          </div>

          <div className="paper-workspace">
            <PdfCanvasViewer url={pdfUrl} />
            <aside className="paper-memo-panel" aria-label="paper memo area">
              <div className="paper-memo-head"><span className="paper-save-state">{saveState}</span><button className="paper-memo-action is-active" aria-label={`switch to ${memoMode === "editor" ? "viewer" : "editor"} mode`} aria-pressed={memoMode === "viewer"} onClick={() => setMemoMode((mode) => mode === "editor" ? "viewer" : "editor")} type="button"><img src={memoToggleIcon} alt="" className="paper-memo-action-icon" /></button></div>
              <div className={`paper-memo-body ${memoMode === "editor" ? "is-editor" : "is-viewer"}`}>
                {memoMode === "editor" ? <textarea className="paper-memo-editor" aria-label="memo editor" onChange={(event) => setMemo(event.target.value)} value={memo} /> : <article className="paper-memo-viewer" aria-label="memo viewer"><ReactMarkdown remarkPlugins={[remarkGfm]}>{memo || "No memo"}</ReactMarkdown></article>}
              </div>
            </aside>
          </div>
        </section>
      </div>

      {settingsOpen && (
        <div className="add-paper-overlay" onMouseDown={() => setSettingsOpen(false)}>
          <section className="add-paper-modal paper-metadata-modal" onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="add-paper-modal-head"><h2>Edit Metadata</h2></div>
            <form className="add-paper-form" onSubmit={saveMetadata}>
              <div className="add-paper-row"><label htmlFor="edit-doi">DOI</label><div className="add-paper-inline-field"><input id="edit-doi" type="text" value={metadataDraft.doi || ""} onChange={(e) => setDraftField("doi", e.target.value)} /><button type="button" className="add-paper-secondary-button" disabled={metadataBusy} onClick={autofillMetadata}>{metadataBusy ? "Working…" : "Autofill"}</button></div></div>
              {([
                ["authors", "authors"], ["title", "title"], ["booktitle", "conference"], ["journal", "journal"],
                ["year", "year"], ["volume", "volume"], ["month", "month"], ["number", "number"],
                ["pages", "pages"], ["url", "publisher_url"], ["project page", "project_page"], ["keywords", "keywords"],
              ] as const).map(([label, field]) => (
                <div className="add-paper-row" key={field}><label htmlFor={`edit-${field}`}>{label}</label><input id={`edit-${field}`} type="text" value={field === "authors" || field === "keywords" ? metadataListInputs[field] : String(metadataDraft[field] ?? "")} onChange={(e) => setDraftField(field, e.target.value)} /></div>
              ))}
              {metadataMessage && <p className="add-paper-message" role="status">{metadataMessage}</p>}
              <div className="add-paper-form-actions"><button className="add-paper-cancel" onClick={() => setSettingsOpen(false)} type="button">Cancel</button><button className="add-paper-submit" disabled={metadataBusy} type="submit">{metadataBusy ? "Saving…" : "Save"}</button></div>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}
