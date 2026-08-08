import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = DATA_DIR / "index"
DB_DIR = DATA_DIR / "chroma_db"
EXPORT_DIR = DATA_DIR / "exports"
CONFIG_FILE = DATA_DIR / "library.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

EMBEDDING_MODEL = "CAMeL-Lab/bert-base-arabic-camelbert-mix"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CONTEXT_CHUNKS = 15

PAGE_PATTERN = r'(?:صفحة|الصفحة|page|p\.?)\s*(\d+)'
TOME_PATTERN = r'(?:الجزء|جزء|المجلد|volume|tome|part)\s*(\d+)'
TITLE_PATTERN = r'(?:كتاب|الكتاب|title)\s*[:：]\s*(.+)'
AUTHOR_PATTERN = r'(?:تأليف|المؤلف|author|الإمام|الشيخ)\s*[:：]?\s*(.+)'

SUPPORTED_EXTENSIONS = {'.docx', '.htm', '.html'}
