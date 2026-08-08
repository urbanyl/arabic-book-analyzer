from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class Citation:
    text: str
    book_title: str
    author: str
    tome: str
    page: str
    reference: str


@dataclass
class Book:
    id: str
    title: str
    author: str
    tome: str
    file_path: Path
    file_type: str
    total_pages: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def reference(self) -> str:
        parts = [self.title]
        if self.author:
            parts.append(f"تأليف: {self.author}")
        if self.tome:
            parts.append(f"الجزء: {self.tome}")
        return " | ".join(parts)


@dataclass
class SearchResult:
    query: str
    selected_books: List[str]
    citations: List[Citation]
    timestamp: str = ""
