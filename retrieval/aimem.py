#!/usr/bin/env python3
"""aimem -- AI-Memory retrieval CLI (Phase 1: keyword + wikilink arms).

The agent-facing entrypoint (Task 14). One command issues a query and gets
ranked keyword results plus 1-hop link context back, as text or JSON.

Subcommands:
  build      (re)build the disposable index from the markdown corpus
  search     keyword/BM25 search (FR-5)
  links      1-hop wikilink/backlink neighbors of an artifact (FR-6)
  query      unified: keyword hits + link expansion of the top hit (Task 14)
  stats      show index status

Examples:
  python3 aimem.py build
  python3 aimem.py search "flora-postgres" --limit 5
  python3 aimem.py links "PL - AI-Memory Vault Phase 1"
  python3 aimem.py query "OCG" --json

Index defaults to ~/.cache/ai-memory/index.db (disposable cache; override
with AIMEM_INDEX). Corpus defaults to the Work Vault (override with
AIMEM_CORPUS or --corpus). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corpus import DEFAULT_CORPUS  # noqa: E402
import engine  # noqa: E402


def _print_hits(hits):
    if not hits:
        print("(no keyword matches)")
        return
    for h in hits:
        print(f"  {h['rank']:>2}. [{h['score']}] {h['name']}")
        if h["title"] and h["title"] != h["name"]:
            print(f"       title: {h['title']}")


def _print_links(nb):
    if not nb.get("found"):
        print(f"(artifact not found: {nb.get('artifact')})")
        return
    print(f"  artifact: {nb['artifact']}")
    print(f"  forward links ({len(nb['forward'])}): "
          + (", ".join(nb["forward"]) or "(none)"))
    print(f"  backlinks ({len(nb['backlinks'])}): "
          + (", ".join(nb["backlinks"]) or "(none)"))


def main(argv=None):
    # Common flags usable before OR after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--index", default=engine.DEFAULT_INDEX,
                        help="index db path")
    common.add_argument("--json", action="store_true", help="emit JSON")

    p = argparse.ArgumentParser(prog="aimem", description=__doc__, parents=[common],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", parents=[common],
                       help="(re)build the index from the corpus")
    b.add_argument("--corpus", default=DEFAULT_CORPUS, help="corpus root")

    s = sub.add_parser("search", parents=[common],
                       help="keyword/BM25 search (FR-5)")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=10)

    l = sub.add_parser("links", parents=[common],
                       help="1-hop wikilink/backlink neighbors (FR-6)")
    l.add_argument("artifact")

    q = sub.add_parser("query", parents=[common],
                       help="keyword + link expansion (agent entry)")
    q.add_argument("query")
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--no-expand", action="store_true")

    sub.add_parser("stats", parents=[common], help="show index status")

    args = p.parse_args(argv)

    if args.cmd == "build":
        res = engine.build(args.corpus, args.index)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Built index: {res['docs']} docs, {res['links']} links "
                  f"in {res['seconds']}s")
            print(f"  index:  {res['index_path']}")
            print(f"  corpus: {res['corpus_root']}")
        return 0

    if args.cmd == "search":
        hits = engine.search(args.query, args.limit, args.index)
        if args.json:
            print(json.dumps(hits, indent=2))
        else:
            print(f"keyword search: {args.query!r}")
            _print_hits(hits)
        return 0

    if args.cmd == "links":
        nb = engine.neighbors(args.artifact, args.index)
        if args.json:
            print(json.dumps(nb, indent=2))
        else:
            _print_links(nb)
        return 0

    if args.cmd == "query":
        res = engine.query(args.query, args.limit,
                           expand=not args.no_expand, index_path=args.index)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"query: {res['query']!r}")
            print("keyword:")
            _print_hits(res["keyword"])
            if res["links"]:
                print("link expansion (top hit):")
                _print_links(res["links"])
        return 0

    if args.cmd == "stats":
        st = engine.stats(args.index)
        print(json.dumps(st, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
