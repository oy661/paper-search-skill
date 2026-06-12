# API 参考文档

本文档记录各数据库 API 的详细信息和高级用法。

## PubMed (NCBI E-utilities)

### 基础信息
- 官网: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- 无需 API key（但注册后可以获得更高频率限制）
- 频率限制: 每秒最多 10 请求，不加 key 时
- 数据格式: JSON / XML

### 关键端点
- ESearch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
- ESummary: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi
- EFetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi

### 高级参数
- field: 搜索字段限制，如 [Title/Abstract]、[Author]、[Journal]
- datetype: 日期类型，pdat(出版日期)、mdat(修改日期)、edat(录入日期)
- sort: 排序方式，relevance(相关度)、pub_date(出版日期)

## Semantic Scholar API

### 基础信息
- 官网: https://api.semanticscholar.org/
- 无需 API key（有 key 频率限制: 100/秒 vs 1/秒）
- 数据格式: JSON

### 关键端点
- 搜索: GET /graph/v1/paper/search?query=
- 详情: GET /graph/v1/paper/{id}
- ID 格式: DOI:10.1234/abc、ArXiv:1234.5678、CorpusId:12345

### 可用字段 (fields)
title, authors, year, journal, abstract, externalIds, url, tldr,
citations, references, citationCount, publicationDate

## OpenAlex API

### 基础信息
- 官网: https://docs.openalex.org/
- 完全免费开源，无需 key
- 数据格式: JSON

### 关键端点
- 搜索作品: GET /works?search=
- 搜索作者: GET /authors?search=
- 搜索机构: GET /institutions?search=

### 过滤参数 (filter)
- from_publication_date, to_publication_date
- authorships.author.display_name.search
- open_access.is_oa （是否开放获取）

### 分页
默认每页 25 条，最大 200 条（per_page）。
通过 cursor 参数翻页: ?cursor=*

## arXiv API

### 基础信息
- 官网: https://info.arxiv.org/help/api/index.html
- 仅支持 HTTP（不是 HTTPS）
- 数据格式: Atom XML

### 搜索查询格式
search_query 参数支持:
- all: 所有字段
- ti: 标题
- au: 作者
- abs: 摘要
- cat: 分类（如 cs.AI、math.ST）

组合: ti:transformer AND abs:attention

## Crossref API

### 基础信息
- 官网: https://api.crossref.org/
- 免费，无需 key
- 数据格式: JSON

### 过滤器 (filter)
- from-pub-date, until-pub-date
- type: journal-article, book-chapter
- has-abstract: true/false
- has-references: true/false
- has-full-text: true/false

### 邮件联系
建议设置 mailto 参数: ?query=...&mailto=your@email.com
可以提高频率限制。

