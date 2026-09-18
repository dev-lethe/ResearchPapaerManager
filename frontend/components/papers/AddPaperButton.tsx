'use client';

import { FormEvent, useEffect, useRef, useState } from "react";

const paperFields = [
  "authors",
  "title",
  "booktitle",
  "journal",
  "year",
  "volume",
  "month",
  "number",
  "pages",
  "url",
  "project page",
  "keywords",
] as const;

type AddPaperButtonProps = { onUploaded?: () => void };

type DoiMetadata = {
  title: string | null;
  authors: string[];
  affiliations: string[];
  year: number | null;
  journal: string | null;
  doi: string | null;
  abstract: string | null;
  publisher_url: string | null;
};

export default function AddPaperButton({ onUploaded }: AddPaperButtonProps) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const formRef = useRef<HTMLFormElement>(null);

  function setField(name: string, value: string) {
    const field = formRef.current?.elements.namedItem(name);
    if (field instanceof HTMLInputElement) field.value = value;
  }

  async function autofill() {
    const doiField = formRef.current?.elements.namedItem("doi");
    const doi = doiField instanceof HTMLInputElement ? doiField.value.trim() : "";
    if (!doi) { setMessage("DOI is required."); return; }
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch("/api/v1/metadata/doi", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ doi }),
      });
      if (!response.ok) throw new Error();
      const data = (await response.json()) as DoiMetadata;
      setField("doi", data.doi || doi);
      setField("title", data.title || "");
      setField("authors", data.authors.join(", "));
      setField("year", data.year == null ? "" : String(data.year));
      setField("journal", data.journal || "");
      setField("booktitle", data.journal || "");
      setField("url", data.publisher_url || "");
      setField("affiliations", data.affiliations.join(", "));
      setField("abstract", data.abstract || "");
      setMessage("Metadata filled.");
    } catch {
      setMessage("Metadata could not be fetched.");
    } finally { setBusy(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const source = new FormData(event.currentTarget);
    const file = source.get("file");
    if (!(file instanceof File) || !file.size) { setMessage("PDF is required."); return; }
    const payload = new FormData();
    payload.append("file", file);
    const mapping: Record<string, string> = {
      title: "title", authors: "authors", affiliations: "affiliations", doi: "doi", year: "year",
      booktitle: "conference", journal: "journal", volume: "volume", month: "month", number: "number",
      pages: "pages", abstract: "abstract", url: "publisher_url", "project page": "project_page", keywords: "keywords",
    };
    Object.entries(mapping).forEach(([sourceName, targetName]) => {
      const value = source.get(sourceName);
      if (typeof value === "string" && value.trim()) payload.append(targetName, value.trim());
    });
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch("/api/v1/papers/upload", { method: "POST", body: payload });
      if (!response.ok) throw new Error();
      onUploaded?.();
      setOpen(false);
    } catch {
      setMessage("Paper could not be uploaded.");
    } finally { setBusy(false); }
  }

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  return (
    <>
      <button type="button" className="lib-icon-button is-framed" aria-label="add paper" onClick={() => setOpen(true)}>
        <img src="/library-icons/add-button.svg" alt="Add" className="lib-icon-asset is-add" />
      </button>

      {open && (
        <div className="add-paper-overlay" role="presentation" onMouseDown={() => setOpen(false)}>
          <section
            className="add-paper-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-paper-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="add-paper-modal-head">
              <h2 id="add-paper-title">Add Paper</h2>
            </div>

            <form className="add-paper-form" onSubmit={submit} ref={formRef}>
              <div className="add-paper-row">
                <label htmlFor="paper-pdf">PDF</label>
                <input id="paper-pdf" name="file" type="file" accept="application/pdf,.pdf" />
              </div>

              <div className="add-paper-row">
                <label htmlFor="paper-doi">DOI</label>
                <div className="add-paper-inline-field">
                  <input id="paper-doi" name="doi" type="text" />
                  <button type="button" className="add-paper-secondary-button" disabled={busy} onClick={autofill}>
                    {busy ? "Working…" : "Autofill"}
                  </button>
                </div>
              </div>

              {paperFields.map((field) => (
                <div className="add-paper-row" key={field}>
                  <label htmlFor={`paper-${field.replace(" ", "-")}`}>{field}</label>
                  <input id={`paper-${field.replace(" ", "-")}`} name={field} type="text" />
                </div>
              ))}

              <input name="affiliations" type="hidden" />
              <input name="abstract" type="hidden" />
              {message && <p className="add-paper-message" role="status">{message}</p>}

              <div className="add-paper-form-actions">
                <button type="button" className="add-paper-cancel" onClick={() => setOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="add-paper-submit" disabled={busy}>
                  {busy ? "Adding…" : "Add Paper"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </>
  );
}
