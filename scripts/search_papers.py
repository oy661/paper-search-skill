#!/usr/bin/env python3
"""Search academic papers across multiple databases.

Usage:
  python search_papers.py --backend pubmed --query "anesthesia" --max 10
  python search_papers.py --backend semanticscholar --query "machine learning" --year 2023
  python search_papers.py --backend openalex --query "covid vaccine" --author "john"
  python search_papers.py --backend arxiv --query "large language model" --max 5
  python search_papers.py --backend crossref --query "data science" --year 2022

Backends: pubmed, semanticscholar, openalex, arxiv, crossref
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
        body = e.read().decode("utf-8", errors="replace")[:500]
        if body:
            print(body, file=sys.stderr)
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


# ── PubMed ──
def search_pubmed(query, max_results=10, mindate=None, maxdate=None):
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    if mindate:
        params["mindate"] = mindate; params["datetype"] = "pdat"
    if maxdate:
        params["maxdate"] = maxdate
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(params)
    data = request_json(url)
    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return []
    time.sleep(0.3)
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(id_list), "retmode": "json"})
    summary_data = request_json(summary_url)
    results = summary_data.get("result", {})
    papers = []
    for uid in results.get("uids", []):
        item = results.get(uid, {})
        authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
        doi = next((a.get("value", "") for a in item.get("articleids", []) if a.get("idtype") == "doi"), "")
        papers.append({
            "title": item.get("title", ""), "authors": authors,
            "journal": item.get("source", ""), "year": item.get("pubdate", ""),
            "pmid": uid, "doi": doi, "source": "PubMed",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
        })
    return papers


# ── Semantic Scholar ──
def search_semanticscholar(query, max_results=10, year=None):
    fields = "title,authors,year,journal,externalIds,abstract,url"
    params = {"query": query, "limit": max_results, "fields": fields}
    if year:
        params["year"] = str(year)
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params)
    data = request_json(url)
    papers = []
    for item in data.get("data", []):
        authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
        eids = item.get("externalIds", {}) or {}
        papers.append({
            "title": item.get("title", ""), "authors": authors,
            "year": str(item.get("year", "") or ""),
            "abstract": item.get("abstract", "") or "",
            "doi": eids.get("DOI", ""), "arxiv_id": eids.get("ArXiv", ""),
            "source": "Semantic Scholar", "url": item.get("url", ""),
        })
    return papers


# ── OpenAlex ──
def search_openalex(query, max_results=10, author=None, year=None):
    params = {"search": query, "per_page": max_results, "sort": "relevance_score:desc"}
    filters = []
    if year:
        filters.append(f"from_publication_date:{year}-01-01,to_publication_date:{year}-12-31")
    if author:
        filters.append(f'authorships.author.display_name.search:"{author}"')
    if filters:
        params["filter"] = ",".join(filters)
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = request_json(url)
    papers = []
    for item in data.get("results", []):
        authors = [a.get("author", {}).get("display_name", "")
                   for a in item.get("authorships", []) if a.get("author")]
        doi = (item.get("doi") or "").replace("https://doi.org/", "")
        papers.append({
            "title": item.get("title", ""), "authors": authors,
            "year": str(item.get("publication_year", "") or ""),
            "journal": (item.get("primary_location") or {}).get("source", {}).get("display_name", ""),
            "doi": doi, "cited_by": item.get("cited_by_count", 0),
            "source": "OpenAlex", "url": item.get("id", ""),
        })
    return papers


# ── arXiv ──
def search_arxiv(query, max_results=10):
    params = {"search_query": f"all:{query}", "start": 0,
              "max_results": max_results, "sortBy": "relevance", "sortOrder": "descending"}
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    text = request_text(url)
    root = ET.fromstring(text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    papers = []
    for entry in root.findall("a:entry", ns):
        title = entry.find("a:title", ns)
        summary = entry.find("a:summary", ns)
        published = entry.find("a:published", ns)
        arxiv_id = entry.find("a:id", ns)
        authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)
                   if a.find("a:name", ns) is not None]
        doi_el = entry.find('a:link[@title="doi"]', ns)
        doi = doi_el.get("href", "").replace("https://doi.org/", "") if doi_el is not None else ""
        papers.append({
            "title": (title.text or "").strip().replace("\n", " ") if title is not None else "",
            "authors": authors,
            "year": (published.text or "")[:4] if published is not None else "",
            "abstract": (summary.text or "").strip().replace("\n", " ") if summary is not None else "",
            "doi": doi,
            "arxiv_id": (arxiv_id.text or "").split("/")[-1] if arxiv_id is not None else "",
            "source": "arXiv", "url": arxiv_id.text if arxiv_id is not None else "",
        })
    return papers


# ── Crossref ──
def search_crossref(query, max_results=10, year=None):
    params = {"query": query, "rows": max_results}
    if year:
        params["filter"] = f"from-pub-date:{year}-01-01,until-pub-date:{year}-12-31"
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = request_json(url)
    items = data.get("message", {}).get("items", [])
    papers = []
    for item in items:
        authors = [a.get("given", "") + " " + a.get("family", "")
                   for a in item.get("author", []) if a.get("family")]
        papers.append({
            "title": (item.get("title") or [""])[0], "authors": authors,
            "year": str(item.get("published-print", {}).get("date-parts", [[None]])[0][0]
                        or item.get("published-online", {}).get("date-parts", [[None]])[0][0] or ""),
            "journal": (item.get("container-title") or [""])[0],
            "doi": item.get("DOI", ""), "source": "Crossref",
            "url": f"https://doi.org/{item.get('DOI', '')}",
        })
    return papers


# ── Display ──
def display_papers(papers):
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", [])[:5])
        if len(p.get("authors", [])) > 5:
            authors += "..."
        ab = p.get("abstract", "")
        ab_short = (ab[:200] + "...") if len(ab) > 200 else ab
        print(f"\n{'='*60}")
        print(f"  [{i}] {p.get('title', 'N/A')[:100]}")
        print(f"  {'─'*60}")
        if authors:        print(f"  作者: {authors}")
        if p.get("year"):  print(f"  年份: {p['year']}")
        if p.get("source"): print(f"  来源: {p['source']}")
        if p.get("journal"): print(f"  期刊: {p['journal']}")
        if p.get("doi"):   print(f"  DOI : {p['doi']}")
        if p.get("pmid"):  print(f"  PMID: {p['pmid']}")
        if p.get("arxiv_id"): print(f"  arXiv: {p['arxiv_id']}")
        if p.get("url"):   print(f"  链接: {p['url']}")
        if p.get("cited_by"): print(f"  引用: {p['cited_by']} 次")
        if ab_short:       print(f"  摘要: {ab_short}")


BACKENDS = {
    "pubmed": search_pubmed, "semanticscholar": search_semanticscholar,
    "openalex": search_openalex, "arxiv": search_arxiv, "crossref": search_crossref,
}


def main():
    parser = argparse.ArgumentParser(description="Search academic papers")
    parser.add_argument("--backend", choices=list(BACKENDS.keys()), default="pubmed",
                        help="Search backend (default: pubmed)")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--max", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--year", help="Filter by year (e.g. 2023 or 2023-2024)")
    parser.add_argument("--author", help="Filter by author (OpenAlex)")
    args = parser.parse_args()

    search_fn = BACKENDS[args.backend]
    kwargs = {"query": args.query, "max_results": args.max}

    if args.backend == "pubmed":
        if args.year and "-" in args.year:
            kwargs["mindate"], kwargs["maxdate"] = args.year.split("-", 1)
        elif args.year:
            kwargs["mindate"] = kwargs["maxdate"] = args.year
    if args.backend == "semanticscholar" and args.year:
        kwargs["year"] = args.year
    if args.backend == "openalex":
        if args.author: kwargs["author"] = args.author
        if args.year:   kwargs["year"] = args.year
    if args.backend == "crossref" and args.year:
        kwargs["year"] = args.year

    print(f"Searching {args.backend} for: {args.query}")
    papers = search_fn(**kwargs)

    if not papers:
        print("No results found.")
        return
    print(f"\nFound {len(papers)} papers:")
    display_papers(papers)


if __name__ == "__main__":
    main()
