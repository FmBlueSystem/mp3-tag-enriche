from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QFrame
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath

class RuleCanvas(QWidget):
    """
    Widget principal donde se construyen visualmente las reglas mediante drag & drop.
    Permite la construcción visual de expresiones lógicas complejas.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.rules = []  # Lista de chips de reglas en el canvas
        self.connections = []  # Lista de conexiones lógicas entre reglas
        self.dropIndicatorPosition = None
        self.selectedChips = set()
        
    def initUI(self):
        """Inicializa la interfaz del canvas"""
        self.setAcceptDrops(True)
        self.setMinimumSize(600, 400)
        
        # Layout principal
        self.layout = QGridLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Estilo del canvas
        self.setStyleSheet("""
            RuleCanvas {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)

    def dragEnterEvent(self, event):
        """Maneja el inicio de un drag sobre el canvas"""
        if event.mimeData().hasFormat("application/x-rule-field"):
            event.acceptProposedAction()
            self.dropIndicatorPosition = event.position()
            self.update()

    def dragMoveEvent(self, event):
        """Actualiza la posición del indicador de drop mientras se arrastra"""
        self.dropIndicatorPosition = event.position()
        self.update()

    def dragLeaveEvent(self, event):
        """Limpia el indicador de drop cuando el drag sale del canvas"""
        self.dropIndicatorPosition = None
        self.update()

    def dropEvent(self, event):
        """
        Maneja el drop de un campo en el canvas.
        Crea un nuevo chip de regla en la posición del drop.
        """
        if event.mimeData().hasFormat("application/x-rule-field"):
            field_data = event.mimeData().data("application/x-rule-field").data().decode()
            
            # Aquí crearemos el chip de regla cuando implementemos RuleChip
            # position = self.mapToGrid(event.position())
            # self.addRuleChip(field_data, position)
            
            event.acceptProposedAction()
            self.dropIndicatorPosition = None
            self.update()

    def paintEvent(self, event):
        """
        Dibuja el canvas, incluyendo:
        - Grid de fondo
        - Conectores lógicos entre reglas
        - Indicador de drop
        - Selección actual
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar grid de fondo
        self._drawGrid(painter)
        
        # Dibujar conectores entre reglas
        self._drawConnections(painter)
        
        # Dibujar indicador de drop si hay un drag activo
        if self.dropIndicatorPosition:
            self._drawDropIndicator(painter)
            
        painter.end()

    def _drawGrid(self, painter):
        """Dibuja el grid de fondo del canvas"""
        pen = QPen(QColor("#e0e0e0"))
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        
        # Dibujar líneas horizontales
        for y in range(0, self.height(), 20):
            painter.drawLine(0, y, self.width(), y)
            
        # Dibujar líneas verticales
        for x in range(0, self.width(), 20):
            painter.drawLine(x, 0, x, self.height())

    def _drawConnections(self, painter):
        """Dibuja los conectores lógicos entre reglas"""
        if not self.connections:
            return
            
        pen = QPen(QColor("#2196F3"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        for connection in self.connections:
            # Por ahora solo dibujamos líneas rectas
            # Más adelante implementaremos curvas Bézier
            start, end = connection
            painter.drawLine(start, end)

    def _drawDropIndicator(self, painter):
        """Dibuja el indicador de la zona de drop durante un drag"""
        if not self.dropIndicatorPosition:
            return
            
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2196F3"))
        
        x = self.dropIndicatorPosition.x() - 10
        y = self.dropIndicatorPosition.y() - 10
        painter.drawRoundedRect(int(x), int(y), 20, 20, 5, 5)

    def mapToGrid(self, point: QPoint) -> QPoint:
        """Ajusta una posición al grid más cercano"""
        grid_size = 20
        x = round(point.x() / grid_size) * grid_size
        y = round(point.y() / grid_size) * grid_size
        return QPoint(x, y)

    def addRuleChip(self, field_data: str, position: QPoint):
        """
        Añade un nuevo chip de regla al canvas.
        Esta función se completará cuando implementemos RuleChip.
        """
        pass  # Por implementar cuando creemos RuleChip

    def removeRuleChip(self, chip):
        """Elimina un chip de regla del canvas"""
        if chip in self.rules:
            self.rules.remove(chip)
            # Eliminar conexiones asociadas
            self.connections = [c for c in self.connections 
                              if chip not in (c[0], c[1])]
            self.update()

    def clearSelection(self):
        """Limpia la selección actual de chips"""
        self.selectedChips.clear()
        self.update()

    def selectChip(self, chip, multi_select=False):
        """Selecciona un chip, opcionalmente manteniendo la selección anterior"""
        if not multi_select:
            self.clearSelection()
        self.selectedChips.add(chip)
        self.update()
