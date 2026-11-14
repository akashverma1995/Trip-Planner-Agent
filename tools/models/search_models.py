from typing import Optional, List
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Represents a single search result item."""
    title: str = Field(default="Unknown")
    url: str = Field(default="")
    content: str = Field(default="")
    score: Optional[float] = Field(default=None)

    def formatted_snippet(self, max_length: int = 300) -> str:
        snippet = self.content.strip()
        if len(snippet) > max_length:
            snippet = snippet[:max_length].rsplit(" ", 1)[0] + "..."
        return snippet


class SearchResponse(BaseModel):
    """Unified container for web search results."""
    query: str
    results: List[SearchResultItem] = Field(default_factory=list)
    success: bool = True
    cached: bool = False
    error_message: Optional[str] = None

    def to_markdown(self, max_snippet_length: int = 300) -> str:
        if not self.success and self.error_message:
            return self.error_message

        if not self.results:
            return f"No search results found for: '{self.query}'."

        formatted_items = []
        for i, item in enumerate(self.results, 1):
            snippet = item.formatted_snippet(max_length=max_snippet_length)
            formatted_items.append(f"{i}. **{item.title}**\n   {item.url}\n   {snippet}")

        cache_badge = " *(cached)*" if self.cached else ""
        return f"### Search Results{cache_badge}\n\n" + "\n\n".join(formatted_items)

