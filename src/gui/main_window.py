import sys
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QProgressBar, QGroupBox, QCheckBox,
    QTextEdit, QSplitter, QFrame, QStatusBar, QMenuBar, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QAction

from ..models.book import Book, Citation
from ..core.document_parser import DocumentParser
from ..core.indexer import Indexer
from ..core.ai_engine import AIEngine
from ..core.exporter import Exporter
from ..utils.file_utils import load_library, save_library


class ImportThread(QThread):
    finished = pyqtSignal(object, list)
    error = pyqtSignal(str)

    def __init__(self, file_paths: List[Path]):
        super().__init__()
        self.file_paths = file_paths
        self.parser = DocumentParser()

    def run(self):
        try:
            for fp in self.file_paths:
                book, pages = self.parser.parse_file(fp)
                self.finished.emit(book, pages)
        except Exception as e:
            self.error.emit(str(e))


class SearchThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, ai_engine: AIEngine, query: str, search_results: dict):
        super().__init__()
        self.ai_engine = ai_engine
        self.query = query
        self.search_results = search_results

    def run(self):
        try:
            citations = self.ai_engine.extract_citations(self.query, self.search_results)
            self.finished.emit(citations)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.books: List[Book] = []
        self.current_citations: List[Citation] = []
        self.indexer = Indexer()
        self.ai_engine = AIEngine()
        self.exporter = Exporter()

        self.books = load_library()
        self._init_ui()
        self._refresh_book_list()
        self._check_ollama()

    def _init_ui(self):
        self.setWindowTitle("برنامج تحليل الكتب العربية - Arabic Book Analyzer")
        self.setMinimumSize(1200, 800)
        self._center_window()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self._create_menu_bar()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 800])
        layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("جاهز")

    def _create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        import_action = QAction("Import Books...", self)
        import_action.setShortcut("Ctrl+O")
        import_action.triggered.connect(self._import_books)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("Tools")

        models_action = QAction("Check AI Model...", self)
        models_action.triggered.connect(self._check_ollama)
        tools_menu.addAction(models_action)

        stats_action = QAction("Index Statistics", self)
        stats_action.triggered.connect(self._show_stats)
        tools_menu.addAction(stats_action)

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Import section
        import_group = QGroupBox("📚 Import Books")
        import_layout = QVBoxLayout(import_group)

        self.import_btn = QPushButton("Import .docx / .htm files")
        self.import_btn.setMinimumHeight(40)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d8f5e;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1a5c3a; }
        """)
        self.import_btn.clicked.connect(self._import_books)
        import_layout.addWidget(self.import_btn)

        self.import_progress = QProgressBar()
        self.import_progress.setVisible(False)
        import_layout.addWidget(self.import_progress)

        layout.addWidget(import_group)

        # Books list
        books_group = QGroupBox("📖 Library")
        books_layout = QVBoxLayout(books_group)

        self.books_list = QListWidget()
        self.books_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.books_list.setStyleSheet("""
            QListWidget::item { padding: 8px; border-bottom: 1px solid #eee; }
            QListWidget::item:selected { background: #d4edda; color: #155724; }
        """)
        books_layout.addWidget(self.books_list)

        books_buttons = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.books_list.selectAll)
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.books_list.clearSelection)
        self.remove_book_btn = QPushButton("Remove")
        self.remove_book_btn.clicked.connect(self._remove_selected_books)
        books_buttons.addWidget(self.select_all_btn)
        books_buttons.addWidget(self.deselect_all_btn)
        books_buttons.addWidget(self.remove_book_btn)
        books_layout.addLayout(books_buttons)

        layout.addWidget(books_group, stretch=1)

        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # Search section
        search_group = QGroupBox("🔍 Search")
        search_layout = QVBoxLayout(search_group)

        query_row = QHBoxLayout()
        query_label = QLabel("Topic / الموضوع:")
        query_label.setFont(QFont("Segoe UI", 12))
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("مثال: الصبر، العدل، الصلاة...")
        self.query_input.setFont(QFont("Segoe UI", 12))
        self.query_input.setMinimumHeight(38)
        self.query_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #2d8f5e;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        self.query_input.returnPressed.connect(self._start_search)

        self.search_btn = QPushButton("Search / بحث")
        self.search_btn.setMinimumHeight(40)
        self.search_btn.setMinimumWidth(120)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5c3a;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0f3d27; }
            QPushButton:disabled { background-color: #888; }
        """)
        self.search_btn.clicked.connect(self._start_search)

        query_row.addWidget(query_label)
        query_row.addWidget(self.query_input, stretch=1)
        query_row.addWidget(self.search_btn)
        search_layout.addLayout(query_row)

        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        search_layout.addWidget(self.search_progress)

        layout.addWidget(search_group)

        # Results section
        results_group = QGroupBox("📋 Results")
        results_layout = QVBoxLayout(results_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "N°", "Citation (اقتباس)", "Book (الكتاب)", "Author (المؤلف)",
            "Tome (الجزء)", "Page (الصفحة)", "Reference (المرجع)"
        ])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setStyleSheet("""
            QTableWidget { gridline-color: #ddd; font-size: 13px; }
            QHeaderView::section {
                background: #1a5c3a;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item { padding: 6px; }
        """)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self.results_table.setColumnWidth(0, 50)
        self.results_table.setColumnWidth(4, 70)
        self.results_table.setColumnWidth(5, 70)

        results_layout.addWidget(self.results_table)

        # Export buttons
        export_row = QHBoxLayout()
        self.export_txt_btn = QPushButton("Export TXT")
        self.export_txt_btn.setMinimumHeight(38)
        self.export_txt_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #357abd; }
            QPushButton:disabled { background-color: #aaa; }
        """)
        self.export_txt_btn.clicked.connect(lambda: self._export('txt'))
        self.export_txt_btn.setEnabled(False)

        self.export_html_btn = QPushButton("Export HTML Report")
        self.export_html_btn.setMinimumHeight(38)
        self.export_html_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #d35400; }
            QPushButton:disabled { background-color: #aaa; }
        """)
        self.export_html_btn.clicked.connect(lambda: self._export('html'))
        self.export_html_btn.setEnabled(False)

        export_row.addStretch()
        export_row.addWidget(self.export_txt_btn)
        export_row.addWidget(self.export_html_btn)
        results_layout.addLayout(export_row)

        layout.addWidget(results_group, stretch=1)

        return panel

    def _center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def _check_ollama(self):
        if self.ai_engine.check_model_available():
            self.status_bar.showMessage(f"✓ Ollama connected | Model: {self.ai_engine.model}")
        else:
            models = self.ai_engine.list_available_models()
            if models:
                msg = f"Ollama found but model '{self.ai_engine.model}' not installed. Available: {', '.join(models)}"
            else:
                msg = "Ollama not found. Please install Ollama and start it."
            self.status_bar.showMessage(f"⚠ {msg}")
            QMessageBox.warning(self, "Ollama Check", msg)

    def _show_stats(self):
        stats = self.indexer.get_stats()
        QMessageBox.information(
            self, "Index Statistics",
            f"Total indexed chunks: {stats['total_chunks']}\n"
            f"Books in library: {len(self.books)}"
        )

    def _import_books(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Book Files",
            "",
            "Supported Files (*.docx *.htm *.html);;Word Files (*.docx);;HTML Files (*.htm *.html);;All Files (*)"
        )
        if not files:
            return

        self._import_files_batch([Path(f) for f in files])

    def _import_files_batch(self, file_paths: List[Path]):
        self.import_progress.setVisible(True)
        self.import_progress.setRange(0, len(file_paths))
        self.import_progress.setValue(0)
        self.import_btn.setEnabled(False)
        self.status_bar.showMessage(f"Importing {len(file_paths)} files...")

        self._pending_imports = len(file_paths)
        self._import_errors = []

        for i, fp in enumerate(file_paths):
            self.import_progress.setValue(i)
            try:
                parser = DocumentParser()
                book, pages = parser.parse_file(fp)
                self.indexer.index_book(book, pages)
                self.books.append(book)
                self.status_bar.showMessage(f"Indexed: {book.title}")
            except Exception as e:
                self._import_errors.append(f"{fp.name}: {str(e)}")

        save_library(self.books)
        self._refresh_book_list()

        self.import_progress.setVisible(False)
        self.import_btn.setEnabled(True)

        if self._import_errors:
            QMessageBox.warning(
                self, "Import Errors",
                "Some files could not be imported:\n" + "\n".join(self._import_errors)
            )

        self.status_bar.showMessage(f"✓ {len(self.books)} books in library")

    def _refresh_book_list(self):
        self.books_list.clear()
        for book in self.books:
            item_text = f"{book.title}"
            if book.author:
                item_text += f" — {book.author}"
            if book.tome:
                item_text += f" (ت{book.tome})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, book.id)
            self.books_list.addItem(item)

    def _remove_selected_books(self):
        selected = self.books_list.selectedItems()
        if not selected:
            return

        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove {len(selected)} book(s) from library?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ids_to_remove = [item.data(Qt.ItemDataRole.UserRole) for item in selected]
        for book_id in ids_to_remove:
            self.indexer.remove_book(book_id)
            self.books = [b for b in self.books if b.id != book_id]

        save_library(self.books)
        self._refresh_book_list()

    def _start_search(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Input Required", "Please enter a search topic.")
            return

        selected_items = self.books_list.selectedItems()
        if not selected_items:
            book_ids = [b.id for b in self.books]
        else:
            book_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        if not book_ids:
            QMessageBox.warning(self, "No Books", "Please import and select at least one book.")
            return

        self.search_btn.setEnabled(False)
        self.search_progress.setVisible(True)
        self.search_progress.setRange(0, 0)
        self.status_bar.showMessage("Searching...")

        search_results = self.indexer.search(query, book_ids, n_results=25)

        self.search_thread = SearchThread(self.ai_engine, query, search_results)
        self.search_thread.finished.connect(self._on_search_finished)
        self.search_thread.error.connect(self._on_search_error)
        self.search_thread.start()

    def _on_search_finished(self, citations: List[Citation]):
        self.current_citations = citations
        self._populate_results(citations)
        self.search_btn.setEnabled(True)
        self.search_progress.setVisible(False)
        self.export_txt_btn.setEnabled(len(citations) > 0)
        self.export_html_btn.setEnabled(len(citations) > 0)
        self.status_bar.showMessage(f"✓ Found {len(citations)} citation(s)")

    def _on_search_error(self, error_msg: str):
        self.search_btn.setEnabled(True)
        self.search_progress.setVisible(False)
        self.status_bar.showMessage("Error")
        QMessageBox.critical(self, "Search Error", error_msg)

    def _populate_results(self, citations: List[Citation]):
        self.results_table.setRowCount(len(citations))
        for i, cit in enumerate(citations):
            self.results_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.results_table.setItem(i, 1, QTableWidgetItem(cit.text))
            self.results_table.setItem(i, 2, QTableWidgetItem(cit.book_title))
            self.results_table.setItem(i, 3, QTableWidgetItem(cit.author))
            self.results_table.setItem(i, 4, QTableWidgetItem(cit.tome))
            self.results_table.setItem(i, 5, QTableWidgetItem(cit.page))
            self.results_table.setItem(i, 6, QTableWidgetItem(cit.reference))

    def _export(self, format_type: str):
        if not self.current_citations:
            return

        query = self.query_input.text().strip()

        if format_type == 'txt':
            filepath = self.exporter.export_txt(self.current_citations, query)
        else:
            filepath = self.exporter.export_html(self.current_citations, query)

        reply = QMessageBox.question(
            self, "Export Complete",
            f"Saved to:\n{filepath}\n\nOpen file?"
        )
        if reply == QMessageBox.StandardButton.Yes:
            import subprocess
            subprocess.Popen(['start', str(filepath)], shell=True)

    def closeEvent(self, event):
        save_library(self.books)
        event.accept()
