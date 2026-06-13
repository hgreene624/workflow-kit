"""Corpus walking + markdown parsing for the AI-Memory retrieval engine.

Shared helpers: enumerate markdown files under a corpus root, extract a
display title, the plain body text, and the Obsidian wikilink targets.

No external dependencies (stdlib only). See README.md.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

# Default corpus: the Work Vault markdown tree. Overridable via --corpus or
# the AIMEM_CORPUS env var. The corpus is the source of truth; the index
# built from it is a disposable cache (NFR-2/NFR-3).
DEFAULT_CORPUS = os.environ.get(
    "AIMEM_CORPUS",
    "/Users/holdengreene/Documents/Vaults/Work Vault",
)

# Directories we never index (build artifacts, vcs, obsidian internals).
SKIP_DIRS = {".git", ".obsidian", "node_modules", "__pycache__", ".venv", "data.nosync"}

# Obsidian wikilink: [[Target]], [[Target|Display]], [[Target#Heading]],
# [[Target#Heading|Display]]. We capture the Target (the resolvable name),
# stripping any #heading and |display.
_WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Doc:
    path: str           # absolute path
    name: str           # basename without .md (the wikilink-resolvable name)
    title: str          # display title (H1 or frontmatter title, else name)
    body: str           # full markdown text
    links: list = field(default_factory=list)  # list of wikilink target names
    mtime: float = 0.0


def link_target_name(raw: str) -> str:
    """Normalize a raw wikilink inner string to its resolvable note name.

    [[Foo#Bar|Baz]] -> 'Foo'. Strips alias and heading, keeps shortest path
    basename so links resolve by filename like Obsidian does.
    """
    target = raw.split("|", 1)[0]          # drop display alias
    target = target.split("#", 1)[0]       # drop heading anchor
    target = target.strip()
    # If someone wrote a path, keep only the basename without extension.
    target = os.path.basename(target)
    if target.lower().endswith(".md"):
        target = target[:-3]
    return target.strip()


def extract_links(text: str) -> list:
    """Return the de-duplicated, order-preserving list of wikilink targets."""
    seen = {}
    for m in _WIKILINK_RE.finditer(text):
        name = link_target_name(m.group(1))
        if name and name not in seen:
            seen[name] = True
    return list(seen.keys())


def extract_title(text: str, fallback: str) -> str:
    """Title = frontmatter `title:` if present, else first H1, else fallback."""
    fm = _FRONTMATTER_RE.match(text)
    if fm:
        for line in fm.group(1).splitlines():
            if line.lower().startswith("title:"):
                t = line.split(":", 1)[1].strip().strip("\"'")
                if t:
                    return t
    h1 = _H1_RE.search(text)
    if h1:
        return h1.group(1).strip()
    return fallback


def iter_markdown(corpus_root: str):
    """Yield Doc objects for every .md file under corpus_root."""
    corpus_root = os.path.abspath(os.path.expanduser(corpus_root))
    for dirpath, dirnames, filenames in os.walk(corpus_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    body = fh.read()
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            name = fn[:-3] if fn.lower().endswith(".md") else fn
            yield Doc(
                path=path,
                name=name,
                title=extract_title(body, name),
                body=body,
                links=extract_links(body),
                mtime=mtime,
            )
