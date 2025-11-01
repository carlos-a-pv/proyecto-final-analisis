import os
import sys
import importlib.util
import bibtexparser


def load_module_from_path(path, name=None):
    """Load a module from a file path while temporarily ensuring its directory is on sys.path.

    This helps modules in `src/r2 - bibliometria` that do local imports between files.
    """
    module_dir = os.path.dirname(os.path.abspath(path))
    old_sys_path = list(sys.path)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    try:
        spec = importlib.util.spec_from_file_location(
            name or os.path.splitext(os.path.basename(path))[0], path
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        # restore original sys.path
        sys.path[:] = old_sys_path


def extract_abstracts(bib_path, limit=None):
    """Extract abstracts (fallback to title/note) from a .bib file using bibtexparser.

    Returns a list of text strings (abstract/title) up to `limit` if provided.
    """
    if not os.path.exists(bib_path):
        return []
    with open(bib_path, encoding="utf-8", errors="ignore") as fh:
        bib = bibtexparser.load(fh)
    docs = []
    for entry in bib.entries:
        text = ""
        for key in ("abstract", "note", "annote", "summary", "title"):
            if key in entry and str(entry[key]).strip():
                text = str(entry[key]).strip()
                break
        if text:
            docs.append(text)
        if limit and len(docs) >= limit:
            break
    return docs


def list_bib_articles(bib_path, limit=None):
    """Return a list of article metadata from a .bib file.

    Each item is a dict with at least: index (int), key (bibtex key if present), title (if available),
    authors (if available), year (if available), and a short snippet (first 200 chars of abstract/title).
    """
    items = []
    if not os.path.exists(bib_path):
        return items
    with open(bib_path, encoding="utf-8", errors="ignore") as fh:
        bib = bibtexparser.load(fh)
    for i, entry in enumerate(bib.entries):
        if limit and i >= limit:
            break
        title = entry.get('title') or ''
        key = entry.get('ID') or entry.get('key') or ''
        authors = entry.get('author') or entry.get('authors') or ''
        year = entry.get('year') or ''
        # choose a primary text field for snippet
        snippet = ''
        for k in ('abstract', 'note', 'annote', 'summary', 'title'):
            if k in entry and str(entry[k]).strip():
                snippet = str(entry[k]).strip()
                break
        snippet = (snippet[:197] + '...') if snippet and len(snippet) > 200 else snippet
        items.append({
            'index': i,
            'key': key,
            'title': title,
            'authors': authors,
            'year': year,
            'snippet': snippet,
        })
    return items
