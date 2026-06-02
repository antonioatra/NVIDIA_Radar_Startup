"""Coleta de dados públicos com proveniência (F1).

Adapters: Tavily (busca), Firecrawl, Playwright (dinâmico), trafilatura, BeautifulSoup, Scrapy.
Respeita robots.txt + rate limiting. Registra url/fetched_at/hash em evidence.

Seeds de fontes do §9 (F0.9): `from packages.scraping import load_sources, allowlist`.
"""

from .seeds import Source, allowlist, by_type, denylist, load_sources

__all__ = ["Source", "load_sources", "allowlist", "denylist", "by_type"]
