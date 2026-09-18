"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./library.css";
import AddPaperButton from "@/components/papers/AddPaperButton";
import HeaderHeightObserver from "@/components/papers/HeaderHeightObserver";
import KeywordSearch from "@/components/papers/KeywordSearch";

type SummaryItem = { value: string; count: number };
type Summary = { years: SummaryItem[]; conferences: SummaryItem[]; keywords: SummaryItem[] };
type PaperMetadata = {
  title: string | null;
  authors: string[];
  year: number | null;
  conference: string | null;
  journal: string | null;
  keywords: string[];
};
type PaperItem = { relative_path: string; name: string; note_preview: string; metadata: PaperMetadata };
type SearchResponse = { total: number; page: number; total_pages: number; items: PaperItem[] };

function sortHeaderFilters(summary: Summary): Summary {
  return {
    ...summary,
    years: [...summary.years].sort((a, b) => Number(b.value) - Number(a.value)),
    conferences: [...summary.conferences].sort((a, b) =>
      a.value.localeCompare(b.value, undefined, { numeric: true, sensitivity: "base" }),
    ),
  };
}

function paperHref(path: string): string {
  return `/papers/${encodeURIComponent(path)}`;
}

function PaperRow({ paper }: { paper: PaperItem }) {
  const venue = [paper.metadata.year, paper.metadata.conference || paper.metadata.journal].filter((value) => value != null && value !== "").join(" ") || "Year / Conference / Journal: –";
  return (
    <Link className="lib-paper-row" href={paperHref(paper.relative_path)}>
      <div className="lib-paper-main">
        <h3 className="lib-paper-title">{paper.metadata.title || paper.name}</h3>
        <p className="lib-paper-meta">{paper.metadata.authors.length ? paper.metadata.authors.join(", ") : "Authors: –"}</p>
        <p className="lib-paper-meta">{venue}</p>
      </div>
      <div className="lib-paper-note" aria-label="paper memo area">
        {paper.note_preview ? (
          <article className="lib-paper-note-content"><ReactMarkdown remarkPlugins={[remarkGfm]}>{paper.note_preview}</ReactMarkdown></article>
        ) : <span className="lib-paper-note-empty">No memo</span>}
      </div>
    </Link>
  );
}

export default function LibraryPage() {
  const [query, setQuery] = useState("");
  const [year, setYear] = useState("");
  const [conference, setConference] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [summary, setSummary] = useState<Summary>({ years: [], conferences: [], keywords: [] });
  const [papers, setPapers] = useState<PaperItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);

  const searchParams = useMemo(() => {
    const params = new URLSearchParams({ page: String(page), per_page: "50" });
    if (query.trim()) params.set("q", query.trim());
    if (year) params.set("year", year);
    if (conference) params.set("conference", conference);
    if (keywords.length) params.set("keywords", keywords.join(","));
    return params.toString();
  }, [conference, keywords, page, query, year]);

  function updateKeywords(value: string[]) {
    setKeywords(value);
    setPage(1);
  }

  useEffect(() => {
    let cancelled = false;
    fetch("/api/v1/tags/local-summary", { cache: "no-store" })
      .then((response) => { if (!response.ok) throw new Error(); return response.json(); })
      .then((data: Summary) => { if (!cancelled) setSummary(sortHeaderFilters(data)); })
      .catch(() => { if (!cancelled) setError("Keyword and filter data could not be loaded."); });
    return () => { cancelled = true; };
  }, [revision]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`/api/v1/papers/local-search?${searchParams}`, { cache: "no-store" })
      .then((response) => { if (!response.ok) throw new Error(); return response.json(); })
      .then((data: SearchResponse) => {
        if (!cancelled) {
          setPapers(data.items);
          setTotal(data.total);
          setTotalPages(data.total_pages);
          setPage(data.page);
        }
      })
      .catch(() => { if (!cancelled) setError("Papers could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [revision, searchParams]);

  return (
    <main className="lib-page">
      <header className="lib-topbar">
        <HeaderHeightObserver />
        <Link className="lib-brand" href="/library">Research Paper Manager</Link>
        <div className="lib-filters" aria-label="search and filter">
          <input className="lib-input-shell" onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Search" type="search" value={query} />
          <select className="lib-input-shell" onChange={(event) => { setYear(event.target.value); setPage(1); }} value={year}>
            <option value="">Year</option>{summary.years.map((item) => <option key={item.value}>{item.value}</option>)}
          </select>
          <select className="lib-input-shell" onChange={(event) => { setConference(event.target.value); setPage(1); }} value={conference}>
            <option value="">Conference/Journal</option>{summary.conferences.map((item) => <option key={item.value}>{item.value}</option>)}
          </select>
          <KeywordSearch options={summary.keywords} value={keywords} onChange={updateKeywords} />
        </div>
        <div className="lib-actions" aria-label="action icons">
          <AddPaperButton onUploaded={() => setRevision((value) => value + 1)} />
        </div>
      </header>

      <div className="lib-layout">
        <section className="lib-content" aria-label="paper library list">
          {keywords.length > 0 && <div className="lib-keyword-panel">
            <p className="lib-section-label">Selected Keywords</p>
            <div className="lib-keyword-list">
              {keywords.map((keyword) => (
                <button aria-label={`Remove keyword ${keyword}`} className="lib-slot lib-slot-chip lib-keyword-chip" key={keyword} onClick={() => updateKeywords(keywords.filter((item) => item !== keyword))} type="button">
                  {keyword} ×
                </button>
              ))}
            </div>
          </div>}

          <div className="lib-content-head"><h1 className="lib-content-title">All Papers</h1><p className="lib-content-caption">{total} papers</p></div>
          {loading && <p className="lib-state">Loading papers…</p>}
          {error && <p className="lib-state is-error">{error}</p>}
          {!loading && !error && !papers.length && <p className="lib-state">No papers found.</p>}
          {!loading && !error && <div className="lib-paper-list">{papers.map((paper) => <PaperRow key={paper.relative_path} paper={paper} />)}</div>}

          {totalPages > 1 && (
            <div className="lib-pagination">
              <button className="lib-page-button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} type="button">Previous</button>
              <p className="lib-content-caption">Page {page} / {totalPages}</p>
              <button className="lib-page-button" disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)} type="button">Next</button>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
