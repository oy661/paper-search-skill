---
name: paper-search
description: |
  综合学术文献检索工具。支持 PubMed、Semantic Scholar、OpenAlex、arXiv、Crossref 五大数据库，
  支持关键词检索、作者筛选、年份过滤、DOI/PMID/arXiv ID 查询。输出包含标题、作者、摘要、DOI、引用数等信息。
  当用户需要检索学术论文、查找文献、做文献综述、查询论文详情时使用此 skill。
---

# 论文检索 (Paper Search)

使用 Python 脚本调用各大开放学术 API 进行文献检索，无需 API key。

## 工作流程

1. 确定检索需求和数据库
2. 使用 scripts/search_papers.py 进行搜索
3. 找到相关论文后，使用 scripts/fetch_paper.py 获取详细信息

## 脚本使用指南

### search_papers.py - 搜索论文

搜索 PubMed（默认）:
  python search_papers.py --query "anesthesia pharmacology" --max 10

指定数据库:
  python search_papers.py --backend semanticscholar --query "deep learning" --max 20

按年份筛选:
  python search_papers.py --backend pubmed --query "covid-19" --year 2024

按作者筛选（仅 OpenAlex）:
  python search_papers.py --backend openalex --query "machine learning" --author "yoshua bengio"

支持的后端 (--backend):
  pubmed          生物医学 3000万+ | 免费无需 key，医学首选
  semanticscholar 全学科 2亿+     | AI 增强，含引用网络
  openalex        全学科 2.5亿+   | 开源，含机构/基金信息
  arxiv           预印本 200万+   | 计算机/物理/数学
  crossref        全学科 1.5亿+   | DOI 元数据最全

### fetch_paper.py - 获取论文详情

按 PMID 查 PubMed 全文摘要:
  python fetch_paper.py --pmid 12345678

按 DOI 查（使用 Semantic Scholar，含引用和 TL;DR）:
  python fetch_paper.py --doi 10.1234/example

按 arXiv ID 查:
  python fetch_paper.py --arxiv 2301.12345

## 推荐使用场景

- 文献综述: 用 OpenAlex 搜索某领域论文，按引用数排序
- 追踪最新研究: 用 PubMed 按年份筛选
- 找具体论文: 已知 DOI/PMID 用 fetch_paper.py
- 找引用数据: 用 Semantic Scholar 获取引用和参考文献列表
- 找预印本: 用 arXiv 搜索最新研究成果

## 注意事项

- PubMed API 有频率限制（每秒最多 10 请求），脚本已自动加 0.3s 延迟
- 所有 API 均免费，无需注册
- 脚本使用 Python 标准库（urllib + xml.etree），无额外依赖
- 网络访问需申请权限（使用 require_escalated）

## 参考文件

- references/apis.md 各数据库 API 详细说明和高级用法
