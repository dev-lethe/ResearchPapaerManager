#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
API_BASE="${API_BASE:-$BASE_URL/api/v1}"
CURL_RETRY_ARGS=(--retry 8 --retry-connrefused --retry-all-errors)

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[error] required command not found: $1" >&2
    exit 1
  fi
}

require_cmd docker
require_cmd curl
require_cmd python3

RESPONSE_BODY="$(mktemp)"
trap 'rm -f "$RESPONSE_BODY"' EXIT

log() {
  echo "[smoke] $*"
}

fail() {
  echo "[smoke][fail] $*" >&2
  exit 1
}

assert_http_200() {
  local url="$1"
  local label="$2"
  local code
  code="$(curl "${CURL_RETRY_ARGS[@]}" -sS -o "$RESPONSE_BODY" -w "%{http_code}" "$url")"
  if [[ "$code" != "200" ]]; then
    echo "[smoke] response body:" >&2
    cat "$RESPONSE_BODY" >&2 || true
    fail "$label returned HTTP $code"
  fi
  log "$label ok (200)"
}

run_upload_check() {
  local sample_pdf="${SAMPLE_PDF:-}"

  if [[ -z "$sample_pdf" ]]; then
    log "upload check skipped (set SAMPLE_PDF explicitly to test uploads)"
    return 0
  fi

  if [[ ! -f "$sample_pdf" ]]; then
    fail "SAMPLE_PDF does not exist: $sample_pdf"
  fi

  log "uploading sample pdf: $sample_pdf"

  local rsp
  rsp="$(curl -fsS \
    -F "file=@$sample_pdf;type=application/pdf" \
    -F "title=Smoke Test Paper" \
    "$API_BASE/papers/upload")"

  local relative_path
  relative_path="$(python3 -c 'import json, sys; print(json.load(sys.stdin).get("relative_path", ""))' <<< "$rsp")"
  if [[ -z "$relative_path" ]]; then
    echo "$rsp" >&2
    fail "upload response does not include relative_path"
  fi

  log "upload ok (relative_path=$relative_path)"

  local encoded_path paper_id
  encoded_path="$(python3 -c 'import sys; from urllib.parse import quote; print(quote(sys.argv[1], safe="/"))' "$relative_path")"
  paper_id="$(python3 -c 'import json, sys; print(json.load(sys.stdin)["paper_id"])' <<< "$rsp")"
  assert_http_200 "$BASE_URL/papers/$paper_id" "paper detail page"

  local files_rsp
  files_rsp="$(curl "${CURL_RETRY_ARGS[@]}" -fsS "$API_BASE/papers/local-files")"
  if ! python3 -c 'import json, sys; sys.exit(not any(item["relative_path"] == sys.argv[1] for item in json.load(sys.stdin)["files"]))' "$relative_path" <<< "$files_rsp"; then
    echo "$files_rsp" >&2
    fail "uploaded file not found in local-files"
  fi

  log "local-files contains uploaded document"

  local meta_rsp
  meta_rsp="$(curl "${CURL_RETRY_ARGS[@]}" -fsS "$API_BASE/papers/local-metadata/$encoded_path")"
  if ! python3 -c 'import json, sys; sys.exit(json.load(sys.stdin)["metadata"]["status"] != "INBOX")' <<< "$meta_rsp"; then
    echo "$meta_rsp" >&2
    fail "metadata check failed"
  fi

  log "metadata endpoint ok"

  local note_rsp
  note_rsp="$(curl "${CURL_RETRY_ARGS[@]}" -fsS "$API_BASE/papers/local-notes/$encoded_path")"
  if ! python3 -c 'import json, sys; note = json.load(sys.stdin); sys.exit(not (note["exists"] and note["note_relative_path"].endswith(".md")))' <<< "$note_rsp"; then
    echo "$note_rsp" >&2
    fail "Markdown memo was not created"
  fi

  log "Markdown memo endpoint ok"
}

main() {
  log "starting stack"
  (
    cd "$ROOT_DIR"
    docker compose up --build -d
  )

  assert_http_200 "$API_BASE/health" "api health"
  assert_http_200 "$BASE_URL/library" "library page"
  assert_http_200 "$API_BASE/papers/local-search" "paper search"

  run_upload_check

  log "all smoke checks passed"
}

main "$@"
