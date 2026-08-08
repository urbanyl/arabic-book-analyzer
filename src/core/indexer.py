import json
from pathlib import Path
from typing import List, Tuple, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import DB_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from ..models.book import Book


class Indexer:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(
            path=str(DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="arabic_books",
            metadata={"hnsw:space": "cosine"}
        )

    def index_book(self, book: Book, pages: List[Tuple[str, str]]) -> None:
        existing = self.collection.get(where={"book_id": book.id})
        if existing and existing.get("ids"):
            self.collection.delete(ids=existing["ids"])

        all_ids = []
        all_docs = []
        all_metadatas = []

        for page_num, page_content in pages:
            chunks = self._chunk_text(page_content)
            for i, chunk in enumerate(chunks):
                doc_id = f"{book.id}_p{page_num}_c{i}"
                all_ids.append(doc_id)
                all_docs.append(chunk)
                all_metadatas.append({
                    "book_id": book.id,
                    "book_title": book.title,
                    "author": book.author,
                    "tome": book.tome,
                    "page": page_num,
                    "chunk_index": i,
                    "reference": book.reference,
                })

        if all_docs:
            embeddings = self.model.encode(all_docs, show_progress_bar=False).tolist()
            batch_size = 500
            for i in range(0, len(all_ids), batch_size):
                self.collection.add(
                    ids=all_ids[i:i + batch_size],
                    documents=all_docs[i:i + batch_size],
                    embeddings=embeddings[i:i + batch_size],
                    metadatas=all_metadatas[i:i + batch_size],
                )

    def search(self, query: str, book_ids: Optional[List[str]] = None, n_results: int = 20) -> dict:
        where_filter = None
        if book_ids:
            where_filter = {"book_id": {"$in": book_ids}}

        query_embedding = self.model.encode([query]).tolist()[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )
        return results

    def remove_book(self, book_id: str) -> None:
        existing = self.collection.get(where={"book_id": book_id})
        if existing and existing.get("ids"):
            self.collection.delete(ids=existing["ids"])

    def get_stats(self) -> dict:
        count = self.collection.count()
        return {"total_chunks": count}

    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= CHUNK_SIZE:
            return [text] if text.strip() else []

        chunks = []
        sentences = text.split('.')
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current_chunk) + len(sentence) + 1 <= CHUNK_SIZE:
                current_chunk += sentence + "."
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "."

        if current_chunk:
            chunks.append(current_chunk.strip())

        if not chunks:
            for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
                chunk = text[i:i + CHUNK_SIZE].strip()
                if chunk:
                    chunks.append(chunk)

        return chunks
