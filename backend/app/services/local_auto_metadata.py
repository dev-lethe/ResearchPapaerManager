from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from app.schemas.local_metadata import LocalPaperMetadata


_VENUE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bCVPR\b", re.IGNORECASE), "CVPR"),
    (re.compile(r"\bICCV\b", re.IGNORECASE), "ICCV"),
    (re.compile(r"\bECCV\b", re.IGNORECASE), "ECCV"),
    (re.compile(r"\bNEURIPS\b|\bNIPS\b", re.IGNORECASE), "NeurIPS"),
    (re.compile(r"\bICLR\b", re.IGNORECASE), "ICLR"),
    (re.compile(r"\bICML\b", re.IGNORECASE), "ICML"),
    (re.compile(r"\bAAAI\b", re.IGNORECASE), "AAAI"),
    (re.compile(r"\bACL\b", re.IGNORECASE), "ACL"),
    (re.compile(r"\bEMNLP\b", re.IGNORECASE), "EMNLP"),
    (re.compile(r"\bNAACL\b", re.IGNORECASE), "NAACL"),
    (re.compile(r"\bKDD\b", re.IGNORECASE), "KDD"),
    (re.compile(r"\bWWW\b", re.IGNORECASE), "WWW"),
    (re.compile(r"\bSIGIR\b", re.IGNORECASE), "SIGIR"),
    (re.compile(r"\bCHI\b", re.IGNORECASE), "CHI"),
    (re.compile(r"\bTPAMI\b", re.IGNORECASE), "TPAMI"),
    (re.compile(r"\bIJCV\b", re.IGNORECASE), "IJCV"),
]

_CROSSREF_API_BASE = "https://api.crossref.org/works"


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    normalized = re.sub(r"^https?://(dx\.)?doi\.org/", "", normalized)
    return normalized or None


def _safe_get_year(message: dict[str, Any]) -> int | None:
    published = message.get("published-print") or message.get("published-online") or message.get("issued")
    if not isinstance(published, dict):
        return None

    parts = published.get("date-parts")
    if not isinstance(parts, list) or not parts:
        return None

    first = parts[0]
    if not isinstance(first, list) or not first:
        return None

    raw_year = first[0]
    if not isinstance(raw_year, int):
        return None
    if 1900 <= raw_year <= 2100:
        return raw_year
    return None


def _safe_get_title(message: dict[str, Any]) -> str | None:
    titles = message.get("title")
    if not isinstance(titles, list) or not titles:
        return None
    title = titles[0]
    if isinstance(title, str) and title.strip():
        return title.strip()
    return None


def _safe_get_venue(message: dict[str, Any]) -> str | None:
    containers = message.get("container-title")
    if isinstance(containers, list) and containers:
        first = containers[0]
        if isinstance(first, str) and first.strip():
            return first.strip()
    return None


def _safe_get_doi(message: dict[str, Any]) -> str | None:
    raw = message.get("DOI")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _safe_get_abstract(message: dict[str, Any]) -> str | None:
    raw = message.get("abstract")
    if not isinstance(raw, str) or not raw.strip():
        return None
    cleaned = re.sub(r"<[^>]+>", " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def _safe_get_authors(message: dict[str, Any]) -> list[str]:
    authors = message.get("author")
    if not isinstance(authors, list):
        return []

    names: list[str] = []
    for item in authors:
        if not isinstance(item, dict):
            continue
        given = str(item.get("given") or "").strip()
        family = str(item.get("family") or "").strip()
        full = " ".join(part for part in [given, family] if part).strip()
        if full:
            names.append(full)
    return names


def _safe_get_affiliations(message: dict[str, Any]) -> list[str]:
    authors = message.get("author")
    if not isinstance(authors, list):
        return []

    seen: set[str] = set()
    values: list[str] = []
    for item in authors:
        if not isinstance(item, dict):
            continue

        affiliations = item.get("affiliation")
        if not isinstance(affiliations, list):
            continue

        for affiliation in affiliations:
            if not isinstance(affiliation, dict):
                continue
            name = str(affiliation.get("name") or "").strip()
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            values.append(name)

    return values


def resolve_doi_metadata(doi: str, crossref_mailto: str | None) -> dict[str, Any] | None:
    crossref_message = _fetch_crossref_by_doi(doi, crossref_mailto)
    if crossref_message is None:
        return None

    return {
        "title": _safe_get_title(crossref_message),
        "authors": _safe_get_authors(crossref_message),
        "affiliations": _safe_get_affiliations(crossref_message),
        "year": _safe_get_year(crossref_message),
        "journal": _safe_get_venue(crossref_message),
        "doi": _safe_get_doi(crossref_message),
        "abstract": _safe_get_abstract(crossref_message),
        "publisher_url": crossref_message.get("URL") if isinstance(crossref_message.get("URL"), str) else None,
    }


def _crossref_headers(crossref_mailto: str | None) -> dict[str, str]:
    if crossref_mailto and crossref_mailto.strip():
        return {"User-Agent": f"research-paper-manager/0.1 (mailto:{crossref_mailto.strip()})"}
    return {"User-Agent": "research-paper-manager/0.1"}


def _fetch_crossref_by_doi(doi: str, crossref_mailto: str | None) -> dict[str, Any] | None:
    encoded = doi.strip()
    if not encoded:
        return None

    url = f"{_CROSSREF_API_BASE}/{quote(encoded, safe='')}"
    with httpx.Client(timeout=8.0, headers=_crossref_headers(crossref_mailto), follow_redirects=True) as client:
        response = client.get(url)
        if response.status_code != 200:
            return None
        payload = response.json()

    message = payload.get("message")
    if isinstance(message, dict):
        return message
    return None


def _extract_year(text: str) -> int | None:
    match = re.search(r"\b(19\d{2}|20\d{2}|2100)\b", text)
    if not match:
        return None

    value = int(match.group(1))
    if 1900 <= value <= 2100:
        return value
    return None


def _extract_venue(*texts: str) -> str | None:
    for text in texts:
        for pattern, canonical in _VENUE_PATTERNS:
            if pattern.search(text):
                return canonical
    return None


def infer_upload_metadata(
    *,
    file_name: str,
    title: str | None,
    doi: str | None,
    year: int | None,
    venue: str | None,
    crossref_mailto: str | None = None,
    authors: list[str] | None = None,
    affiliations: list[str] | None = None,
    abstract: str | None = None,
    publisher_url: str | None = None,
    journal: str | None = None,
    volume: str | None = None,
    month: str | None = None,
    number: str | None = None,
    pages: str | None = None,
    project_page: str | None = None,
    keywords: list[str] | None = None,
) -> LocalPaperMetadata:
    stem = Path(file_name).stem
    normalized_stem = stem.replace("_", " ").replace("-", " ")

    inferred_year = year or _extract_year(" ".join([normalized_stem, title or "", doi or ""]))
    inferred_venue = (venue or "").strip() or _extract_venue(normalized_stem, title or "", doi or "")

    crossref_message: dict[str, Any] | None = None
    try:
        if doi and doi.strip():
            crossref_message = _fetch_crossref_by_doi(doi.strip(), crossref_mailto)
    except Exception:
        crossref_message = None

    if crossref_message is not None:
        inferred_year = year or _safe_get_year(crossref_message) or inferred_year
        inferred_venue = (venue or "").strip() or _safe_get_venue(crossref_message) or inferred_venue

    resolved_title = (title or "").strip() or (_safe_get_title(crossref_message) if crossref_message else None)
    resolved_authors = [item.strip() for item in (authors or []) if item.strip()]
    if not resolved_authors and crossref_message is not None:
        resolved_authors = _safe_get_authors(crossref_message)

    resolved_affiliations = [item.strip() for item in (affiliations or []) if item.strip()]
    if not resolved_affiliations and crossref_message is not None:
        resolved_affiliations = _safe_get_affiliations(crossref_message)

    resolved_abstract = (abstract or "").strip() or (_safe_get_abstract(crossref_message) if crossref_message else None)
    resolved_journal = (journal or "").strip() or (_safe_get_venue(crossref_message) if crossref_message else None)
    resolved_doi = normalize_doi(doi) or normalize_doi(_safe_get_doi(crossref_message) if crossref_message else None)
    resolved_publisher_url = (publisher_url or "").strip() or (
        crossref_message.get("URL") if crossref_message and isinstance(crossref_message.get("URL"), str) else None
    )

    return LocalPaperMetadata(
        status="INBOX",
        title=resolved_title or None,
        authors=resolved_authors,
        affiliations=resolved_affiliations,
        year=inferred_year,
        conference=inferred_venue or None,
        journal=resolved_journal or None,
        volume=(volume or "").strip() or None,
        month=(month or "").strip() or None,
        number=(number or "").strip() or None,
        pages=(pages or "").strip() or None,
        doi=resolved_doi,
        abstract=resolved_abstract or None,
        publisher_url=resolved_publisher_url or None,
        project_page=(project_page or "").strip() or None,
        # Keywords are user-managed content tags (for example: LLM,
        # emotion recognition, dataset). Bibliographic fields must not be
        # converted into tags automatically.
        keywords=[item.strip() for item in (keywords or []) if item.strip()],
    )
