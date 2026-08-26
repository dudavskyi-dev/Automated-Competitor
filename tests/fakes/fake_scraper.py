from app.ports.scraper import ScrapedPage


class FakeScraper:
    def __init__(
        self,
        pages: dict[str, ScrapedPage] | None = None,
        default: ScrapedPage | None = None,
    ) -> None:
        self._pages = pages or {}
        self._default = default
        self.calls: list[str] = []

    async def fetch_markdown(self, url: str) -> ScrapedPage:
        self.calls.append(url)
        if url in self._pages:
            return self._pages[url]
        if self._default is not None:
            return self._default
        raise KeyError(url)
