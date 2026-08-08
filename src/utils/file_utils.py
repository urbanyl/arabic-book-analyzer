import json
import hashlib
from pathlib import Path
from typing import List, Optional
from ..models.book import Book


def generate_id(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]


def save_library(books: List[Book], path: Optional[Path] = None) -> None:
    from config import CONFIG_FILE
    path = path or CONFIG_FILE
    data = []
    for book in books:
        data.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "tome": book.tome,
            "file_path": str(book.file_path),
            "file_type": book.file_type,
            "total_pages": book.total_pages,
            "metadata": book.metadata,
        })
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_library(path: Optional[Path] = None) -> List[Book]:
    from config import CONFIG_FILE
    path = path or CONFIG_FILE
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    books = []
    for item in data:
        books.append(Book(
            id=item["id"],
            title=item["title"],
            author=item["author"],
            tome=item.get("tome", ""),
            file_path=Path(item["file_path"]),
            file_type=item["file_type"],
            total_pages=item.get("total_pages", 0),
            metadata=item.get("metadata", {}),
        ))
    return books
