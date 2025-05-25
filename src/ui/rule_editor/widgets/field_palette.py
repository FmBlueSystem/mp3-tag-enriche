from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, 
                                    QScrollArea, QWidget, QLineEdit)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag

class FieldItem(QFrame):
    """
    Widget que representa un campo individual en la paleta.
    Se puede arrastrar al canvas para crear una regla.
    """
    def __init__(self, field_name: str, field_type: str, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.field_type = field_type
        
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz del campo"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Ícono según tipo
        icon = self._getIconForType()
        
        # Label con ícono y nombre
        label = QLabel(f"{icon} {self.field_name}")
        label.setStyleSheet("""
            QLabel {
                color: #424242;
                font-size: 13px;
            }
        """)
        
        layout.addWidget(label)
        
        # Estilo del item
        self.setStyleSheet("""
            FieldItem {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
            
            FieldItem:hover {
                background-color: #E3F2FD;
                border-color: #2196F3;
                cursor: grab;
            }
        """)
        
        # Configuración del item
        self.setFixedHeight(32)
        
    def _getIconForType(self) -> str:
        """Retorna el ícono apropiado según el tipo de campo"""
        icons = {
            'text': '📝',
            'number': '🔢',
            'key': '🎵',
            'boolean': '✓',
            'date': '📅',
            'enum': '📋'
        }
        return icons.get(self.field_type.lower(), '❔')
        
    def mousePressEvent(self, event):
        """Inicia el drag & drop del campo"""
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Datos del campo para el drop
            mime_data.setData(
                "application/x-rule-field",
                f"{self.field_name}|{self.field_type}".encode()
            )
            
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction)

class FieldPalette(QFrame):
    """
    Panel lateral que contiene los campos disponibles para
    crear reglas mediante drag & drop.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        """Inicializa la interfaz de la paleta"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Título
        title = QLabel("Campos Disponibles")
        title.setStyleSheet("""
            QLabel {
                background-color: #1976D2;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        # Búsqueda
        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText("🔍 Buscar campos...")
        self.searchBox.textChanged.connect(self.filterFields)
        self.searchBox.setStyleSheet("""
            QLineEdit {
                border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 8px;
            }
            QLineEdit:focus {
                border-bottom-color: #2196F3;
            }
        """)
        
        # Área scrolleable para campos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fafafa;
            }
        """)
        
        # Contenedor de campos
        self.fieldsContainer = QWidget()
        self.fieldsLayout = QVBoxLayout(self.fieldsContainer)
        self.fieldsLayout.setContentsMargins(8, 8, 8, 8)
        self.fieldsLayout.setSpacing(4)
        self.fieldsLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.fieldsContainer)
        
        # Agregar widgets al layout
        layout.addWidget(title)
        layout.addWidget(self.searchBox)
        layout.addWidget(scroll)
        
        # Estilo de la paleta
        self.setStyleSheet("""
            FieldPalette {
                background-color: white;
                border: none;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        self.setFixedWidth(250)
        
        # Cargar campos por defecto
        self.loadDefaultFields()
        
    def loadDefaultFields(self):
        """Carga los campos disponibles por defecto"""
        default_fields = [
            ("BPM", "number"),
            ("Key", "key"),
            ("Genre", "text"),
            ("Artist", "text"),
            ("Title", "text"),
            ("Year", "number"),
            ("Energy", "number"),
            ("Danceability", "number"),
            ("Label", "text"),
            ("Duration", "number"),
            ("Rating", "number"),
            ("Added Date", "date"),
            ("Is Favorite", "boolean")
        ]
        
        for name, type in default_fields:
            self.addField(name, type)
            
    def addField(self, name: str, type: str):
        """Agrega un nuevo campo a la paleta"""
        field = FieldItem(name, type)
        self.fieldsLayout.addWidget(field)
        
    def filterFields(self, text: str):
        """Filtra los campos según el texto de búsqueda"""
        text = text.lower()
        
        # Mostrar/ocultar campos según coincidencia
        for i in range(self.fieldsLayout.count()):
            widget = self.fieldsLayout.itemAt(i).widget()
            if isinstance(widget, FieldItem):
                matches = text in widget.field_name.lower()
                widget.setVisible(matches)
