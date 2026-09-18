"use client";

import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy, RenderTask, TextLayer } from "pdfjs-dist";

function PdfPageCanvas({ document, pageNumber, width, zoom }: {
  document: PDFDocumentProxy;
  pageNumber: number;
  width: number;
  zoom: number;
}) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const textLayerRef = useRef<HTMLDivElement>(null);
  const [shouldRender, setShouldRender] = useState(false);
  const [aspectRatio, setAspectRatio] = useState(1.414);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setShouldRender(true);
        observer.disconnect();
      }
    }, { rootMargin: "800px 0px" });
    observer.observe(wrapper);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let active = true;
    document.getPage(pageNumber).then((page) => {
      if (!active) return;
      const viewport = page.getViewport({ scale: 1 });
      setAspectRatio(viewport.height / viewport.width);
    });
    return () => { active = false; };
  }, [document, pageNumber]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!shouldRender || !canvas || !width) return;
    let task: RenderTask | null = null;
    let active = true;
    document.getPage(pageNumber).then((page) => {
      if (!active) return;
      const base = page.getViewport({ scale: 1 });
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const viewport = page.getViewport({ scale: (width / base.width) * zoom * dpr });
      const context = canvas.getContext("2d", { alpha: false });
      if (!context) return;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${viewport.width / dpr}px`;
      canvas.style.height = `${viewport.height / dpr}px`;
      task = page.render({ canvas, canvasContext: context, viewport });
      task.promise.catch(() => undefined);
    });
    return () => { active = false; task?.cancel(); };
  }, [document, pageNumber, shouldRender, width, zoom]);

  useEffect(() => {
    const host = textLayerRef.current;
    if (!shouldRender || !host || !width) return;
    let active = true;
    let textLayer: TextLayer | null = null;
    const container = host.ownerDocument.createElement("div");
    container.className = "textLayer";
    host.appendChild(container);

    async function renderText() {
      const [page, pdfjs] = await Promise.all([
        document.getPage(pageNumber),
        import("pdfjs-dist"),
      ]);
      if (!active) return;
      const base = page.getViewport({ scale: 1 });
      // Text uses CSS pixels, not the canvas's device-pixel resolution.
      const viewport = page.getViewport({ scale: (width / base.width) * zoom });
      container.style.setProperty("--total-scale-factor", String(viewport.scale * viewport.userUnit));
      container.style.setProperty("--scale-round-x", "1px");
      container.style.setProperty("--scale-round-y", "1px");
      textLayer = new pdfjs.TextLayer({
        textContentSource: page.streamTextContent(),
        container,
        viewport,
      });
      await textLayer.render();
    }

    renderText().catch(() => undefined);
    return () => {
      active = false;
      textLayer?.cancel();
      container.remove();
    };
  }, [document, pageNumber, shouldRender, width, zoom]);

  const displayWidth = width * zoom;
  return (
    <div
      className="paper-viewer-page"
      ref={wrapperRef}
      style={{ width: displayWidth, minHeight: displayWidth * aspectRatio }}
    >
      <canvas ref={canvasRef} />
      <div className="paper-viewer-text-layer" ref={textLayerRef} />
      {!shouldRender && <span>Page {pageNumber}</span>}
    </div>
  );
}

export default function PdfCanvasViewer({ url }: { url: string }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [zoom, setZoom] = useState(1);
  const [width, setWidth] = useState(0);
  const [pageAspectRatio, setPageAspectRatio] = useState(1.414);
  const [error, setError] = useState(false);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(1, entry.contentRect.width - 12)));
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let active = true;
    let loaded: PDFDocumentProxy | null = null;
    async function load() {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
        loaded = await pdfjs.getDocument({ url }).promise;
        if (active) setDocument(loaded);
      } catch { if (active) setError(true); }
    }
    load();
    return () => { active = false; loaded?.destroy(); };
  }, [url]);

  useEffect(() => {
    if (!document) return;
    let active = true;
    document.getPage(1).then((page) => {
      if (!active) return;
      const viewport = page.getViewport({ scale: 1 });
      setPageAspectRatio(viewport.height / viewport.width);
    });
    return () => { active = false; };
  }, [document]);

  return (
    <section className="paper-viewer-panel" aria-label="paper pdf preview">
      <div className="paper-viewer-toolbar">
        <span>{document ? `${document.numPages} pages` : "– pages"}</span>
        <button disabled={zoom <= 0.7} onClick={() => setZoom((value) => Math.max(0.7, value - 0.1))} type="button">-</button>
        <span>{Math.round(zoom * 100)}%</span>
        <button disabled={zoom >= 2} onClick={() => setZoom((value) => Math.min(2, value + 0.1))} type="button">+</button>
        <a href={url}>Open</a>
      </div>
      <div
        className="paper-viewer-canvas"
        ref={hostRef}
        style={{ height: width > 0 ? width * pageAspectRatio : 800 }}
      >
        {!document && !error && <p>Loading PDF…</p>}
        {error && <p>PDF could not be loaded. <a href={url}>Open PDF</a></p>}
        {document && width > 0 && Array.from({ length: document.numPages }, (_, index) => (
          <PdfPageCanvas document={document} key={index + 1} pageNumber={index + 1} width={width} zoom={zoom} />
        ))}
      </div>
    </section>
  );
}
