"""Main window implementation for the MP3 Tag Enricher application."""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QProgressBar, QStatusBar, QScrollArea,
    QFrame, QLineEdit, QCheckBox, QTextEdit, QListWidget
)
from PySide6.QtCore import Qt, QMimeData, Signal, Slot, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from . import apply_material_style, COLORS
from ..core import MP3TagProcessor, ProcessingResult

class DragDropArea(QFrame):
    """A widget that accepts drag and drop of MP3 files."""
    
    fileDropped = Signal(str)  # Signal emitted when a file is dropped
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setMinimumHeight(100)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Label
        self.label = QLabel("Drag and drop MP3 files or directories here\nor use the buttons below to browse")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Styling
        self.setStyleSheet(f"""
            DragDropArea {{
                background-color: {COLORS['surface']};
                border: 2px dashed {COLORS['primary']};
                border-radius: 8px;
                padding: 16px;
            }}
            QLabel {{
                color: {COLORS['on_surface']};
                font-size: 16px;
            }}
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for MP3 files and directories."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.mp3') or Path(file_path).is_dir():
                    event.acceptProposedAction()
                    return
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for MP3 files and directories."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            path = Path(file_path)
            if path.is_dir():
                self.fileDropped.emit(str(path))
            elif file_path.lower().endswith('.mp3'):
                self.fileDropped.emit(str(path))

class ProcessingThread(QThread):
    """Background thread for MP3 processing."""
    
    finished = Signal(ProcessingResult)
    file_processed = Signal(str, ProcessingResult)  # Emitted for each processed file
    progress = Signal(int, int)  # current, total
    
    def __init__(self, processor: MP3TagProcessor, files: list[Path], analysis_mode: bool):
        super().__init__()
        self.processor = processor
        self.files = files
        self.analysis_mode = analysis_mode
    
    def run(self):
        """Execute the processing operation for multiple files."""
        total_files = len(self.files)
        for i, filepath in enumerate(self.files, 1):
            result = self.processor.process_file(filepath, self.analysis_mode)
            self.file_processed.emit(str(filepath), result)
            self.progress.emit(i, total_files)
        self.finished.emit(result)  # Emit last result

class ResultsWidget(QFrame):
    """Widget for displaying processing results."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Results text area
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setMinimumHeight(200)
        layout.addWidget(self.results)
        
        # Styling
        self.setStyleSheet(f"""
            ResultsWidget {{
                background-color: {COLORS['surface']};
                border-radius: 4px;
                padding: 16px;
            }}
            QTextEdit {{
                font: 14px;
                border: 1px solid {COLORS['primary']};
                border-radius: 4px;
            }}
        """)
    
    def set_results(self, result: ProcessingResult):
        """Display processing results."""
        text = []
        
        # Status and message
        text.append(f"Status: {'Success' if result.success else 'Error'}")
        text.append(f"Message: {result.message}\n")
        
        # Original tags
        if result.original_tags:
            text.append("Original Tags:")
            for key, value in result.original_tags.items():
                text.append(f"  {key.title()}: {value}")
            text.append("")
        
        # Language info
        if result.detected_language:
            text.append(f"Detected Language: {result.detected_language}\n")
        
        # MusicBrainz data
        if result.musicbrainz_info:
            text.append("MusicBrainz Data:")
            for key, value in result.musicbrainz_info.items():
                text.append(f"  {key.title()}: {value}")
            text.append("")
        
        # Proposed changes
        if result.proposed_tags:
            text.append("Proposed Tags:")
            for key, value in result.proposed_tags.items():
                text.append(f"  {key.title()}: {value}")
        
        self.results.setPlainText("\n".join(text))

class TagEditorWidget(QFrame):
    """Widget for displaying and editing MP3 tags."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create fields
        self.fields = {}
        field_names = ['Artist', 'Title', 'Album', 'Year', 'Genre', 'Track']
        
        for name in field_names:
            field_layout = QHBoxLayout()
            label = QLabel(name + ':')
            label.setMinimumWidth(80)
            edit = QLineEdit()
            apply_material_style(edit)  # Apply Material Design style
            field_layout.addWidget(label)
            field_layout.addWidget(edit)
            layout.addLayout(field_layout)
            self.fields[name.lower()] = edit
        
        # Styling
        self.setStyleSheet(f"""
            TagEditorWidget {{
                background-color: {COLORS['surface']};
                border-radius: 4px;
                padding: 16px;
            }}
            QLabel {{
                color: {COLORS['on_surface']};
                font: 14px;
            }}
            QLineEdit {{
                border: 1px solid {COLORS['primary']};
                border-radius: 4px;
                padding: 8px;
                font: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
    
    def set_tags(self, tags: dict):
        """Update the displayed tags."""
        for field, value in tags.items():
            if field in self.fields:
                self.fields[field].setText(str(value))
    
    def get_tags(self) -> dict:
        """Get the current tag values."""
        return {
            field: edit.text()
            for field, edit in self.fields.items()
        }

class MainWindow(QMainWindow):
    """Main window of the MP3 Tag Enricher application."""
    
    def __init__(self):
        super().__init__()
        self.processor = MP3TagProcessor()
        self.mp3_files = []
        self.processing_thread = None
        self.setup_ui()
        apply_material_style(self)
    
    def setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("MP3 Tag Enricher")
        self.setMinimumSize(800, 600)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Drag & Drop area
        self.drag_drop = DragDropArea()
        self.drag_drop.fileDropped.connect(self.handle_file_dropped)
        layout.addWidget(self.drag_drop)
        
        # Browse buttons
        browse_layout = QHBoxLayout()
        browse_button = QPushButton("Browse for MP3 Files")
        browse_button.clicked.connect(self.browse_file)
        apply_material_style(browse_button)
        
        browse_dir_button = QPushButton("Browse for Directory")
        browse_dir_button.clicked.connect(self.browse_directory)
        apply_material_style(browse_dir_button)
        
        browse_layout.addWidget(browse_button)
        browse_layout.addWidget(browse_dir_button)
        layout.addLayout(browse_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(100)
        self.file_list.itemSelectionChanged.connect(self.handle_file_selection)
        layout.addWidget(self.file_list)
        
        # Tag editor
        self.tag_editor = TagEditorWidget()
        layout.addWidget(self.tag_editor)
        
        # Results display
        self.results_widget = ResultsWidget()
        layout.addWidget(self.results_widget)
        
        # Process controls
        controls_layout = QHBoxLayout()
        
        self.analysis_mode = QCheckBox("Analysis Mode")
        self.analysis_mode.setStyleSheet(f"""
            QCheckBox {{
                font: 14px;
                color: {COLORS['on_surface']};
            }}
        """)
        controls_layout.addWidget(self.analysis_mode)
        
        controls_layout.addStretch()
        
        self.process_button = QPushButton("Process All Files")
        self.process_button.clicked.connect(self.process_file)
        self.process_button.setEnabled(False)
        apply_material_style(self.process_button)
        controls_layout.addWidget(self.process_button)
        
        layout.addLayout(controls_layout)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def scan_directory(self, directory: Path) -> list[Path]:
        """Recursively scan a directory for MP3 files."""
        mp3_files = []
        try:
            for item in directory.rglob("*.mp3"):
                if item.is_file():
                    mp3_files.append(item)
        except Exception as e:
            self.status_bar.showMessage(f"Error scanning directory: {e}")
        return mp3_files
    
    @Slot(str)
    def handle_file_dropped(self, file_path: str):
        """Handle a dropped MP3 file or directory."""
        path = Path(file_path)
        
        if path.is_dir():
            # Scan directory for MP3 files
            new_files = self.scan_directory(path)
            self.mp3_files.extend(new_files)
            self.update_file_list()
            self.status_bar.showMessage(f"Found {len(new_files)} MP3 files in directory")
        else:
            # Single MP3 file
            self.mp3_files.append(path)
            self.update_file_list()
            self.load_file_tags(path)
            self.status_bar.showMessage(f"Loaded: {file_path}")
    
    def update_file_list(self):
        """Update the list widget with found MP3 files."""
        self.file_list.clear()
        for file_path in self.mp3_files:
            self.file_list.addItem(file_path.name)
        self.process_button.setEnabled(len(self.mp3_files) > 0)
    
    def handle_file_selection(self):
        """Handle selection change in the file list."""
        if self.file_list.currentItem():
            selected_name = self.file_list.currentItem().text()
            selected_file = next(f for f in self.mp3_files if f.name == selected_name)
            self.load_file_tags(selected_file)
    
    def load_file_tags(self, file_path: Path):
        """Load and display tags for the selected file."""
        try:
            current_tags = self.processor.load_current_tags(file_path)
            self.tag_editor.set_tags(current_tags)
        except Exception as e:
            self.status_bar.showMessage(f"Error loading tags: {e}")
    
    def browse_file(self):
        """Open file browser dialog for MP3 selection."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select MP3 Files",
            "",
            "MP3 Files (*.mp3);;All Files (*.*)"
        )
        for file_path in file_paths:
            self.handle_file_dropped(file_path)
    
    def browse_directory(self):
        """Open directory browser dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            ""
        )
        if directory:
            self.handle_file_dropped(directory)
    
    @Slot()
    def process_file(self):
        """Process the selected MP3 files."""
        if not self.mp3_files:
            return
        
        # Disable UI during processing
        self.process_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.mp3_files))
        self.progress.setValue(0)
        
        # Start processing in background thread
        self.processing_thread = ProcessingThread(
            self.processor,
            self.mp3_files.copy(),
            self.analysis_mode.isChecked()
        )
        self.processing_thread.finished.connect(self.handle_processing_complete)
        self.processing_thread.file_processed.connect(self.handle_file_processed)
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.start()
    
    @Slot(str, ProcessingResult)
    def handle_file_processed(self, file_path: str, result: ProcessingResult):
        """Handle completion of single file processing."""
        # Update results for the current file
        self.results_widget.set_results(result)
        
        if result.success:
            self.status_bar.showMessage(f"Processed: {file_path}")
            # Update displayed tags if changes were made and this is the selected file
            if not self.analysis_mode.isChecked():
                current_item = self.file_list.currentItem()
                if current_item and current_item.text() == Path(file_path).name:
                    self.tag_editor.set_tags(result.proposed_tags)
        else:
            self.status_bar.showMessage(f"Error processing {file_path}: {result.message}")
    
    @Slot(int, int)
    def update_progress(self, current: int, total: int):
        """Update the progress bar."""
        self.progress.setValue(current)
    
    @Slot(ProcessingResult)
    def handle_processing_complete(self, result: ProcessingResult):
        """Handle completion of file processing."""
        # Update UI
        self.progress.setVisible(False)
        self.process_button.setEnabled(True)
        
        # Display results
        self.results_widget.set_results(result)
        
        # Update status
        if result.success:
            self.status_bar.showMessage(result.message)
            # Update displayed tags if changes were made
            if not self.analysis_mode.isChecked():
                self.tag_editor.set_tags(result.proposed_tags)
        else:
            self.status_bar.showMessage(f"Error: {result.message}")
