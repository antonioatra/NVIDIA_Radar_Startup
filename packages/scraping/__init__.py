"""Coleta de dados públicos com proveniência (F1).

Adapters: Tavily (busca), Firecrawl, Playwright (dinâmico), trafilatura, BeautifulSoup, Scrapy.
Respeita robots.txt + rate limiting. Registra url/fetched_at/hash em evidence.

Seeds de fontes do §9 (F0.9): `from packages.scraping import load_sources, allowlist`.
Busca de URLs candidatas (F1.1): `from packages.scraping import search, SearchResult`.
Extração limpa de página (F1.2): `from packages.scraping import scrape, ExtractedPage`.
Renderização de página dinâmica (F1.3): `from packages.scraping import render, RenderedPage`.
Texto principal de blog/notícia (F1.4): `extract_article`, `fetch_article`, `Article`.
"""

from .article import Article
from .article import extract as extract_article
from .article import fetch as fetch_article
from .dynamic import RenderedPage, render
from .firecrawl import ExtractedPage, scrape
from .search import SearchResult, search
from .seeds import Source, allowlist, by_type, denylist, load_sources

__all__ = [
    "Source",
    "load_sources",
    "allowlist",
    "denylist",
    "by_type",
    "search",
    "SearchResult",
    "scrape",
    "ExtractedPage",
    "render",
    "RenderedPage",
    "Article",
    "extract_article",
    "fetch_article",
]
