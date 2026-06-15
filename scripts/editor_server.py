#!/usr/bin/env python3
"""
Local visual editor server for Alexander Salganik's website.
Run this to start the editor on http://localhost:8001
"""

import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).parent.parent
EDITOR_DIR = Path(__file__).parent / "editor"
DEFAULT_PAGE = "home"
DEFAULT_PORT = 8001

PAGE_FILES = {
    "home": ROOT_DIR / "index.html",
    "cv": ROOT_DIR / "cv" / "index.html",
    "publications": ROOT_DIR / "publications" / "index.html",
    "research": ROOT_DIR / "research" / "index.html",
    "contact": ROOT_DIR / "contact" / "index.html",
}

FIELD_PATTERNS = {
    "home": {
        "overview": (
            r'(<h2 id="overview-title">Research Overview</h2>\s*<p>)(.*?)(</p>)',
            re.DOTALL,
        ),
        "pub_title": (
            r'(<h3 id="latest-publication-title">)(.*?)(</h3>)',
            re.DOTALL,
        ),
        "pub_meta": (
            r'(<p class="muted" id="latest-publication-meta">)(.*?)(</p>)',
            re.DOTALL,
        ),
        "pub_doi": (
            r'(<a class="btn" id="latest-publication-doi" href=")([^"]*)(")',
            0,
        ),
    },
    "cv": {
        "education": (
            r'(<section class="section" id="education">\s*<h2[^>]*>.*?</h2>)(.*?)(</section>)',
            re.DOTALL,
        ),
        "experience": (
            r'(<section class="section" id="experience">\s*<h2[^>]*>.*?</h2>)(.*?)(</section>)',
            re.DOTALL,
        ),
    },
    "publications": {
        "publications": (
            r'(<section class="section" id="publications">\s*<h2[^>]*>.*?</h2>)(.*?)(</section>)',
            re.DOTALL,
        ),
    },
    "research": {
        "intro": (
            r'(<section class="section">\s*)(<p>.*?</p>\s*)(<div class="grid three">)',
            re.DOTALL,
        ),
    },
    "contact": {
        "contact": (
            r'(<main id="content" class="container">.*?<section class="section">)(.*?)(</section>\s*</main>)',
            re.DOTALL,
        ),
    },
}


def normalize_page(page):
    """Return a known page key or the default page."""
    return page if page in PAGE_FILES else DEFAULT_PAGE


def extract_field(html, pattern, flags):
    """Extract a single editable field from HTML."""
    match = re.search(pattern, html, flags)
    return match.group(2).strip() if match else ""


def replace_field(html, pattern, value, flags):
    """Replace a single editable field while preserving surrounding markup."""
    compiled = re.compile(pattern, flags)
    if not compiled.search(html):
        raise ValueError(f"Could not find editable field for pattern: {pattern}")

    replacement = "" if value is None else str(value)
    return compiled.sub(
        lambda match: f"{match.group(1)}{replacement}{match.group(3)}",
        html,
        count=1,
    )


def get_page_content(page):
    """Extract editable content for a page."""
    page = normalize_page(page)
    html = PAGE_FILES[page].read_text(encoding="utf-8")

    content = {"page": page}
    for field_name, (pattern, flags) in FIELD_PATTERNS[page].items():
        content[field_name] = extract_field(html, pattern, flags)

    return content


def save_page_content(data):
    """Save editable content back to a page."""
    page = data.get("page")
    if page not in PAGE_FILES:
        raise ValueError(f"Unknown page: {page!r}")

    html = PAGE_FILES[page].read_text(encoding="utf-8")
    changed = False

    for field_name, (pattern, flags) in FIELD_PATTERNS[page].items():
        if field_name not in data:
            continue
        html = replace_field(html, pattern, data[field_name], flags)
        changed = True

    if changed:
        PAGE_FILES[page].write_text(html, encoding="utf-8")

    return changed


class EditorHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the editor server."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path or "/"

        if path == "/":
            self.directory = str(EDITOR_DIR)
            self.path = "/editor.html"
            super().do_GET()
            return

        if path == "/api/content":
            page = parse_qs(parsed_url.query).get("page", [DEFAULT_PAGE])[0]
            self.send_json(get_page_content(page))
            return

        if path == "/api/pages":
            self.send_json({"pages": list(PAGE_FILES.keys())})
            return

        self.directory = str(EDITOR_DIR)
        self.path = path
        super().do_GET()

    def do_POST(self):
        """Handle POST requests."""
        parsed_url = urlparse(self.path)
        if parsed_url.path != "/api/save":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            changed = save_page_content(data)
            self.send_json({"success": True, "changed": changed})
        except json.JSONDecodeError as exc:
            self.send_json(
                {"success": False, "error": f"Invalid JSON payload: {exc}"},
                status=HTTPStatus.BAD_REQUEST,
            )
        except ValueError as exc:
            self.send_json(
                {"success": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        except Exception as exc:
            print(f"Error saving content: {exc}")
            self.send_json(
                {"success": False, "error": "Failed to save content"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def send_json(self, payload, status=HTTPStatus.OK):
        """Send a JSON response."""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Suppress default request logging."""
        pass


class LocalEditorServer(ThreadingHTTPServer):
    """HTTP server with reusable local socket."""

    allow_reuse_address = True


def main():
    """Start the editor server."""
    try:
        server = LocalEditorServer(("127.0.0.1", DEFAULT_PORT), EditorHandler)
    except OSError as exc:
        print(f"\nCould not start site editor on http://localhost:{DEFAULT_PORT}")
        print(f"Reason: {exc}\n")
        raise SystemExit(1) from exc

    print("\n" + "=" * 50)
    print("Local Site Editor")
    print("=" * 50)
    print("\nOpen your browser at:")
    print(f"  http://localhost:{DEFAULT_PORT}")
    print("\nPress Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nEditor stopped\n")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
