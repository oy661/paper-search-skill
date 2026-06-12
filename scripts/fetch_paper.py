#!/usr/bin/env python3
"""Fetch detailed paper info by ID (PMID, DOI, arXiv ID).

Usage:
  python fetch_paper.py --pmid 12345678
  python fetch_paper.py --doi 10.1234/example
  python fetch_paper.py --arxiv 2301.12345
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import time
import xml.etree.ElementTree as ET

USER_AGENT = "Codex-PaperSearch/1.0"


def request_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def request_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_pubmed(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "xml", "rettype": "abstract"})
    text = request_text(url)
    root = ET.fromstring(text)
    ns = {"pubmed": "http://www.ncbi.nlm.nih.gov/pubmed"}
    art = root.find(".//pubmed:Article", ns) or root.find(".//Article")
    if art is None:
        print(f"Paper not found: PMID {pmid}", file=sys.stderr)
        sys.exit(1)
    title = (art.find("ArticleTitle") or art.find("./pubmed:ArticleTitle", ns))
    abstract = art.find("Abstract/AbstractText") or art.find("./pubmed:Abstract/pubmed:AbstractText", ns)
    authors = art.find("AuthorList") or art.find("./pubmed:AuthorList", ns)
    journal = art.find("Journal/Title") or art.find("./pubmed:Journal/pubmed:Title", ns)
    year = art.find("Journal/JournalIssue/PubDate/Year") or art.find(
        "./pubmed:Journal/pubmed:JournalIssue/pubmed:PubDate/pubmed:Year", ns)

    author_names = []
    if authors is not None:
        for a in authors.findall("Author") or authors.findall("./pubmed:Author", ns):
            last = a.find("LastName") or a.find("./pubmed:LastName", ns)
            fore = a.find("ForeName") or a.find("./pubmed:ForeName", ns)
            if last is not None:
                author_names.append(f"{fore.text if fore is not None else ''} {last.text}".strip())

    print(f"\n{'='*70}")
    print(f"  {title.text.strip() if title is not None else 'N/A'}")
    print(f"  {'='*70}")
    if author_names:
        print(f"  作者: {', '.join(author_names)}")
    if journal is not None:
        print(f"  期刊: {journal.text.strip()}")
    if year is not None:
        print(f"  年份: {year.text}")
    print(f"  PMID: {pmid}")
    print(f"  链接: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
    if abstract is not None:
        print(f"\n  摘要:")
        print(f"  {'─'*70}")
        print(f"  {abstract.text.strip() if abstract.text else ''}")


def fetch_s2(doi):
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,authors,year,journal,abstract,externalIds,citations,references,tldr"
    data = request_json(url)
    authors = [a.get("name", "") for a in data.get("authors", []) if a.get("name")]
    eids = data.get("externalIds", {}) or {}
    ab = data.get("abstract", "") or ""
    print(f"\n{'='*70}")
    print(f"  {data.get('title', 'N/A')}")
    print(f"  {'='*70}")
    if authors: print(f"  作者: {', '.join(authors)}")
    if data.get("year"): print(f"  年份: {data['year']}")
    if data.get("journal"): print(f"  期刊: {data['journal'].get('name', '')}")
    print(f"  DOI : {doi}")
    if eids.get("ArXiv"): print(f"  arXiv: {eids['ArXiv']}")
    if data.get("url"): print(f"  链接: {data['url']}")
    tldr = data.get("tldr") or {}
    citations = data.get("citations", [])
    refs = data.get("references", [])
    print(f"  引用数: {len(citations)}")
    print(f"  参考文献数: {len(refs)}")
    if tldr.get("text"): print(f"  TL;DR: {tldr['text']}")
    if ab:
        print(f"\n  摘要:")
        print(f"  {'─'*70}")
        print(f"  {ab}")


def fetch_arxiv(arxiv_id):
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    text = request_text(url)
    root = ET.fromstring(text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    if entry is None:
        print(f"Paper not found: arXiv {arxiv_id}", file=sys.stderr)
        sys.exit(1)
    title = entry.find("a:title", ns)
    summary = entry.find("a:summary", ns)
    published = entry.find("a:published", ns)
    authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns) if a.find("a:name", ns) is not None]
    categories = [c.get("term", "") for c in entry.findall("a:category", ns)]
    print(f"\n{'='*70}")
    print(f"  {(title.text or '').strip().replace(chr(10), ' ')}")
    print(f"  {'='*70}")
    if authors: print(f"  作者: {', '.join(authors)}")
    if published is not None: print(f"  日期: {published.text[:10]}")
    if categories: print(f"  分类: {', '.join(categories)}")
    print(f"  arXiv: {arxiv_id}")
    print(f"  链接: https://arxiv.org/abs/{arxiv_id}")
    if summary is not None:
        ab = (summary.text or "").strip().replace(chr(10), " ")
        print(f"\n  摘要:")
        print(f"  {'─'*70}")
        print(f"  {ab}")


def main():
    parser = argparse.ArgumentParser(description="Fetch paper details by ID")
    parser.add_argument("--pmid", help="PubMed ID")
    parser.add_argument("--doi", help="DOI")
    parser.add_argument("--arxiv", help="arXiv ID")
    args = parser.parse_args()

    if args.pmid:
        fetch_pubmed(args.pmid)
    elif args.doi:
        fetch_s2(args.doi)
    elif args.arxiv:
        fetch_arxiv(args.arxiv)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
