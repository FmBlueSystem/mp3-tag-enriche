from typing import Optional, Set, Dict, Any
import math

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (QPainter, QPainterPath, QPen, QColor, QBrush,
                        QFont, QFontMetrics)

from ....core.camelot import CamelotWheel, CompatibilityMode

class CamelotWheelWidget(QWidget):
    """
    Widget que muestra una rueda Camelot interactiva para selección
    de claves musicales y visualización de compatibilidad.
    """
    
    # Señales
    keySelected = pyqtSignal(str)  # Emitida al seleccionar una clave
    compatibilityChanged = pyqtSignal(list)  # Emitida al cambiar compatibilidad
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Componentes
        self.wheel = CamelotWheel()
        
        # Estado
        self.selected_key: Optional[str] = None
        self.compatible_keys: Set[str] = set()
        self.compatibility_mode = CompatibilityMode.PERFECT
        self.hover_key: Optional[str] = None
        self.wheel_rotation = 0  # Rotación en grados
        
        # Configuración visual
        self.setMinimumSize(400, 400)
        self.setSizePolicy(
            QWidget.SizePolicy.MinimumExpanding,
            QWidget.SizePolicy.MinimumExpanding
        )
        
        # Estilos
        self.colors = {
            'background': QColor('#f5f5f5'),
            'border': QColor('#e0e0e0'),
            'text': QColor('#424242'),
            'major': QColor('#2196F3'),
            'minor': QColor('#F44336'),
            'selected': QColor('#4CAF50'),
            'compatible': QColor('#8BC34A'),
            'hover': QColor('#FFC107')
        }
        
        # Estado de la UI
        self._cell_rects: Dict[str, QRectF] = {}  # Cache de áreas de celdas
        self._center = QPointF()  # Centro de la rueda
        self._radius = 0.0  # Radio de la rueda
        
        # Configuración
        self.setMouseTracking(True)
        self._update_layout()
        
    def sizeHint(self):
        """Tamaño sugerido del widget."""
        return self.minimumSize()
        
    def resizeEvent(self, event):
        """Maneja el redimensionamiento del widget."""
        super().resizeEvent(event)
        self._update_layout()
        
    def _update_layout(self):
        """Actualiza el layout de la rueda."""
        # Calcular dimensiones
        size = min(self.width(), self.height())
        margin = size * 0.1
        self._radius = (size - 2 * margin) / 2
        self._center = QPointF(self.width() / 2, self.height() / 2)
        
        # Calcular áreas de celdas
        self._cell_rects.clear()
        for i in range(1, 13):
            angle = (i - 1) * 30 - self.wheel_rotation
            
            # Clave mayor (externa)
            rect_major = self._get_cell_rect(angle, True)
            self._cell_rects[f"{i}A"] = rect_major
            
            # Clave menor (interna)
            rect_minor = self._get_cell_rect(angle, False)
            self._cell_rects[f"{i}B"] = rect_minor
            
    def _get_cell_rect(self, angle: float, is_outer: bool) -> QRectF:
        """
        Calcula el rectángulo de una celda de la rueda.
        
        Args:
            angle: Ángulo en grados
            is_outer: True para el anillo exterior (mayor)
            
        Returns:
            QRectF con el área de la celda
        """
        # Convertir a radianes
        rad = math.radians(angle)
        
        # Radio interno/externo según posición
        if is_outer:
            r1 = self._radius * 0.7
            r2 = self._radius
        else:
            r1 = self._radius * 0.4
            r2 = self._radius * 0.7
            
        # Calcular puntos del sector
        span = math.radians(30)  # 30 grados
        points = []
        
        for r in (r1, r2):
            # Punto inicial del arco
            x = self._center.x() + r * math.cos(rad - span/2)
            y = self._center.y() + r * math.sin(rad - span/2)
            points.append(QPointF(x, y))
            
            # Punto final del arco
            x = self._center.x() + r * math.cos(rad + span/2)
            y = self._center.y() + r * math.sin(rad + span/2)
            points.append(QPointF(x, y))
            
        # Crear rectángulo que contiene el sector
        rect = QRectF()
        for point in points:
            if rect.isNull():
                rect = QRectF(point, point)
            else:
                rect = rect.united(QRectF(point, point))
                
        return rect
        
    def paintEvent(self, event):
        """Dibuja el widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo
        painter.fillRect(self.rect(), self.colors['background'])
        
        # Dibujar sectores
        for i in range(1, 13):
            self._draw_sector(painter, i)
            
        # Dibujar conexiones de compatibilidad
        if self.selected_key and self.compatible_keys:
            self._draw_compatibility_lines(painter)
            
        painter.end()
        
    def _draw_sector(self, painter: QPainter, number: int):
        """
        Dibuja un sector de la rueda.
        
        Args:
            painter: QPainter a usar
            number: Número de sector (1-12)
        """
        # Dibujar sector mayor
        major_key = f"{number}A"
        self._draw_cell(
            painter, major_key,
            self.wheel.get_musical_key(major_key),
            True
        )
        
        # Dibujar sector menor
        minor_key = f"{number}B"
        self._draw_cell(
            painter, minor_key,
            self.wheel.get_musical_key(minor_key),
            False
        )
        
    def _draw_cell(
        self,
        painter: QPainter,
        camelot_key: str,
        musical_key: str,
        is_outer: bool
    ):
        """
        Dibuja una celda de la rueda.
        
        Args:
            painter: QPainter a usar
            camelot_key: Clave en notación Camelot
            musical_key: Clave en notación musical
            is_outer: True si es celda exterior (mayor)
        """
        rect = self._cell_rects.get(camelot_key)
        if not rect:
            return
            
        # Determinar color de fondo
        if camelot_key == self.selected_key:
            bg_color = self.colors['selected']
        elif camelot_key == self.hover_key:
            bg_color = self.colors['hover']
        elif camelot_key in self.compatible_keys:
            bg_color = self.colors['compatible']
        else:
            bg_color = self.colors['major'] if is_outer else self.colors['minor']
            
        # Dibujar fondo
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color.lighter(120)))
        painter.drawPath(self._get_cell_path(camelot_key))
        
        # Dibujar borde
        painter.setPen(QPen(bg_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self._get_cell_path(camelot_key))
        
        # Dibujar texto
        self._draw_cell_text(
            painter, rect,
            f"{camelot_key}\n{musical_key}",
            self.colors['text']
        )
        
    def _get_cell_path(self, camelot_key: str) -> QPainterPath:
        """
        Crea el path para una celda.
        
        Args:
            camelot_key: Clave en notación Camelot
            
        Returns:
            QPainterPath para la celda
        """
        path = QPainterPath()
        rect = self._cell_rects.get(camelot_key)
        if rect:
            path.addRect(rect)
        return path
        
    def _draw_cell_text(
        self,
        painter: QPainter,
        rect: QRectF,
        text: str,
        color: QColor
    ):
        """
        Dibuja el texto en una celda.
        
        Args:
            painter: QPainter a usar
            rect: Área donde dibujar
            text: Texto a dibujar
            color: Color del texto
        """
        painter.setPen(color)
        painter.setFont(QFont('Arial', 8))
        
        # Alinear texto en el centro
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignCenter,
            text
        )
        
    def _draw_compatibility_lines(self, painter: QPainter):
        """Dibuja líneas de conexión entre claves compatibles."""
        if not self.selected_key or not self.compatible_keys:
            return
            
        # Configurar pincel
        pen = QPen(self.colors['compatible'], 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Obtener centro de celda seleccionada
        selected_rect = self._cell_rects.get(self.selected_key)
        if not selected_rect:
            return
            
        selected_center = selected_rect.center()
        
        # Dibujar líneas a claves compatibles
        for key in self.compatible_keys:
            rect = self._cell_rects.get(key)
            if rect:
                painter.drawLine(
                    selected_center,
                    rect.center()
                )
                
    def mousePressEvent(self, event):
        """Maneja clicks del mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Encontrar celda clickeada
            for key, rect in self._cell_rects.items():
                if rect.contains(event.position()):
                    self.select_key(key)
                    break
                    
    def mouseMoveEvent(self, event):
        """Maneja movimiento del mouse."""
        # Actualizar hover
        old_hover = self.hover_key
        self.hover_key = None
        
        for key, rect in self._cell_rects.items():
            if rect.contains(event.position()):
                self.hover_key = key
                break
                
        if old_hover != self.hover_key:
            self.update()
            
    def leaveEvent(self, event):
        """Maneja cuando el mouse sale del widget."""
        self.hover_key = None
        self.update()
        
    def select_key(self, key: str):
        """
        Selecciona una clave y actualiza compatibilidad.
        
        Args:
            key: Clave en notación Camelot
        """
        if key != self.selected_key:
            self.selected_key = key
            self.compatible_keys = self.wheel.get_compatible_keys(
                key,
                self.compatibility_mode
            )
            self.keySelected.emit(key)
            self.compatibilityChanged.emit(list(self.compatible_keys))
            self.update()
            
    def set_compatibility_mode(self, mode: CompatibilityMode):
        """
        Cambia el modo de compatibilidad.
        
        Args:
            mode: Nuevo modo de compatibilidad
        """
        if mode != self.compatibility_mode:
            self.compatibility_mode = mode
            if self.selected_key:
                self.compatible_keys = self.wheel.get_compatible_keys(
                    self.selected_key,
                    mode
                )
                self.compatibilityChanged.emit(list(self.compatible_keys))
                self.update()
                
    def rotate(self, degrees: float):
        """
        Rota la rueda.
        
        Args:
            degrees: Grados a rotar
        """
        self.wheel_rotation = (self.wheel_rotation + degrees) % 360
        self._update_layout()
        self.update()
