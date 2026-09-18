"use client";

import { useEffect, useRef } from "react";

// Keep the fixed header and main content aligned after wrapping.
export default function HeaderHeightObserver() {
  const markerRef = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const header = markerRef.current?.parentElement;
    const page = header?.closest<HTMLElement>(".lib-page");
    if (!header || !page) return;
    const update = () => page.style.setProperty("--lib-header-height", `${header.getBoundingClientRect().height}px`);
    const observer = new ResizeObserver(update);
    observer.observe(header);
    update();
    return () => { observer.disconnect(); page.style.removeProperty("--lib-header-height"); };
  }, []);
  return <span ref={markerRef} hidden aria-hidden="true" />;
}
