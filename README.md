# برنامج تحليل الكتب العربية بالذكاء الاصطناعي المحلي
# Arabic Book Analyzer — Local AI-Powered Analysis

A Windows desktop application for analyzing Arabic books using a local LLM (via Ollama). Extracts exact citations on any topic from `.docx` and `.htm` files with zero hallucination.

---

## ✨ Features

- **100% Local** — No internet connection required. All AI runs on your PC.
- **Multi-format** — Import `.docx` and `.htm` files containing Arabic text.
- **Semantic Search** — Uses SentenceTransformers + ChromaDB for fast vector search.
- **Exact Extraction** — AI extracts verbatim citations only. No hallucinations.
- **Multi-book Search** — Query one book or all books at once.
- **Export** — Generate `.txt` and styled `.html` reports.
- **Arabic UI** — Right-to-left interface designed for Arabic texts.

---

## 🖥️ Architecture

```
arabic-book-analyzer/
├── main.py                  # Application entry point
├── config.py                # Configuration & paths
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── data/                   # Created at runtime
│   ├── library.json        # Book metadata database
│   ├── chroma_db/          # Vector database
│   └── exports/            # Generated reports
├── src/
│   ├── gui/
│   │   ├── main_window.py  # Main PyQt6 window
│   │   └── __init__.py
│   ├── core/
│   │   ├── document_parser.py  # DOCX/HTML text extraction
│   │   ├── indexer.py          # Vector indexing (ChromaDB)
│   │   ├── ai_engine.py        # LLM extraction (Ollama)
│   │   ├── exporter.py         # TXT/HTML report generation
│   │   └── __init__.py
│   ├── models/
│   │   ├── book.py         # Data models (Book, Citation)
│   │   └── __init__.py
│   └── utils/
│       ├── arabic_utils.py # Arabic text normalization
│       ├── file_utils.py   # Library save/load
│       └── __init__.py
└── tests/
    ├── sample.docx         # Sample test file
    └── sample.htm          # Sample test file
```

---

## 🛠️ Installation

### Prerequisites

- **Python 3.10+** (64-bit)
- **Ollama** installed and running ([ollama.com](https://ollama.com))
- **8 GB RAM minimum** (16 GB recommended)

### Step 1: Install Ollama

1. Download Ollama from [https://ollama.com](https://ollama.com)
2. Install and start it
3. Pull a model:

```bash
# Recommended: Llama 3 8B (multilingual, good Arabic support)
ollama pull llama3

# Alternative: Mistral 7B
ollama pull mistral
```

### Step 2: Install Python Dependencies

```bash
cd arabic-book-analyzer
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
python main.py
```

---

## 📖 Usage Guide

### 1. Import Books

- Click **"Import .docx / .htm files"** or use `File > Import Books`
- Select one or more files
- The app automatically extracts:
  - Title (from file content)
  - Author
  - Tome/Volume number
  - Page numbers (if present in text)
- Books are indexed and stored in the local vector database

### 2. Search

- Enter a topic in Arabic (e.g., `الصبر`, `العدل`, `الصلاة`)
- Select specific books or leave all selected
- Click **"Search / بحث"**
- The AI finds all exact citations related to your topic

### 3. Export Results

- **Export TXT** — Raw text file with all citations
- **Export HTML Report** — Styled report with table (printable)

---

## ⚙️ Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_MODEL` | `llama3` | LLM model name |
| `EMBEDDING_MODEL` | `CAMeL-BERT` | Arabic sentence embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size for indexing |
| `MAX_CONTEXT_CHUNKS` | `15` | Max chunks sent to LLM |

Or use environment variables:
```bash
set OLLAMA_MODEL=mistral
set OLLAMA_HOST=http://localhost:11434
```

---

## 🧠 How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Import     │────▶│  Parse Text  │────▶│  Index      │
│  .docx/.htm │     │  + Metadata  │     │  (ChromaDB) │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
┌─────────────┐     ┌──────────────┐     ┌──────▼──────┐
│  Export     │◀────│  AI Extract  │◀────│  Semantic   │
│  TXT/HTML   │     │  (Ollama)    │     │  Search     │
└─────────────┘     └──────────────┘     └─────────────┘
```

1. **Parse** — Extract text, pages, metadata from files
2. **Index** — Split into chunks, embed with Arabic BERT, store in ChromaDB
3. **Search** — User query → vector search → top relevant chunks
4. **Extract** → LLM receives chunks + query → returns exact citations as JSON
5. **Export** — Generate reports

---

## 📋 Requirements

```
PyQt6>=6.6.0
python-docx>=1.1.0
beautifulsoup4>=4.12.0
chromadb>=0.4.22
sentence-transformers>=2.3.0
ollama>=0.1.6
lxml>=5.1.0
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama not found | Ensure Ollama is running: `ollama serve` |
| Model not found | Pull the model: `ollama pull llama3` |
| Slow first run | Embedding model downloads on first use (~200MB) |
| Arabic text garbled | Ensure files are UTF-8 encoded |
| No results found | Try broader topic terms or check if books are indexed |

---

## 📄 License

MIT License — Free for personal and academic use.

---

## 🤝 Contributing

This project is designed for researchers, students, and anyone working with Arabic texts. Contributions welcome!
