import re
from pathlib import Path
from typing import List, Tuple, Optional
from docx import Document
from bs4 import BeautifulSoup
from ..models.book import Book


class DocumentParser:
    PAGE_PATTERNS = [
        r'(?:صفحة|الصفحة)\s*[:：]?\s*(\d+)',
        r'(?:page|p\.?)\s*[:：]?\s*(\d+)',
        r'\[?\s*(\d+)\s*\]?\s*$',
        r'ـ\s*(\d+)\s*ـ',
    ]

    TOME_PATTERNS = [
        r'(?:الجزء|جزء|المجلد)\s*[:：]?\s*(\d+)',
        r'(?:volume|tome|part)\s*[:：]?\s*(\d+)',
    ]

    TITLE_PATTERNS = [
        r'(?:كتاب|الكتاب|title)\s*[:：]\s*(.+)',
        r'^\s*(.+?)\s*$',
    ]

    AUTHOR_PATTERNS = [
        r'(?:تأليف|المؤلف|مؤلف|الإمام|الشيخ)\s*[:：]?\s*(.+)',
        r'(?:author)\s*[:：]\s*(.+)',
    ]

    def parse_file(self, file_path: Path) -> Tuple[Book, List[Tuple[str, str]]]:
        file_type = file_path.suffix.lower()
        if file_type == '.docx':
            text, pages = self._parse_docx(file_path)
        elif file_type in ('.htm', '.html'):
            text, pages = self._parse_htm(file_path)
        else:
            raise ValueError(f"Format non supporté: {file_type}")

        title = self._extract_title(text) or file_path.stem
        author = self._extract_author(text)
        tome = self._extract_tome(text)
        book_id = f"{title}_{tome}" if tome else title

        book = Book(
            id=book_id,
            title=title,
            author=author,
            tome=tome,
            file_path=file_path,
            file_type=file_type,
            total_pages=len(pages),
        )
        return book, pages

    def _parse_docx(self, path: Path) -> Tuple[str, List[Tuple[str, str]]]:
        doc = Document(path)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        pages = self._split_into_pages(full_text)
        return full_text, pages

    def _parse_htm(self, path: Path) -> Tuple[str, List[Tuple[str, str]]]:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        full_text = soup.get_text(separator='\n', strip=True)
        pages = self._split_into_pages(full_text)
        return full_text, pages

    def _split_into_pages(self, text: str) -> List[Tuple[str, str]]:
        pages = []
        current_page = "1"
        current_content = []

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue

            page_num = self._detect_page_number(line)
            if page_num:
                if current_content:
                    pages.append((current_page, '\n'.join(current_content)))
                current_page = page_num
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            pages.append((current_page, '\n'.join(current_content)))

        if not pages:
            pages = [("1", text)]

        return pages

    def _detect_page_number(self, line: str) -> Optional[str]:
        for pattern in self.PAGE_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_title(self, text: str) -> Optional[str]:
        lines = text.split('\n')[:30]
        for line in lines:
            line = line.strip()
            for pattern in self.TITLE_PATTERNS:
                match = re.search(pattern, line)
                if match and len(match.group(1).strip()) > 2:
                    return match.group(1).strip()
        return None

    def _extract_author(self, text: str) -> str:
        lines = text.split('\n')[:50]
        for line in lines:
            line = line.strip()
            for pattern in self.AUTHOR_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    return match.group(1).strip()
        return ""

    def _extract_tome(self, text: str) -> str:
        lines = text.split('\n')[:20]
        for line in lines:
            line = line.strip()
            for pattern in self.TOME_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
        return ""
