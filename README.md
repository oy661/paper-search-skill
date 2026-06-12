# Paper Search Skill

A comprehensive academic literature search skill for [Codex](https://codex.ai).

## Features

- **PubMed** - 30M+ biomedical articles, free API
- **Semantic Scholar** - 200M+ papers across all disciplines, AI-enhanced
- **OpenAlex** - 250M+ scholarly works, open source
- **arXiv** - 2M+ preprints (CS/Physics/Math)
- **Crossref** - 150M+ DOI records

## Installation

Copy to ~/.codex/skills/paper-search/ and restart Codex.

## Usage

`ash
python scripts/search_papers.py --backend pubmed --query "anesthesia"
python scripts/search_papers.py --backend semanticscholar --query "deep learning" --max 20
python scripts/fetch_paper.py --pmid 12345678
python scripts/fetch_paper.py --doi 10.1234/example
`

## License

MIT