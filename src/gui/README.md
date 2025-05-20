# GUI Package

Este paquete contiene la implementación completa de la interfaz gráfica de Genre Detector.

## Estructura

```
src/gui/
├── models/              # Modelos y lógica de negocio
│   ├── genre_model.py  # Procesamiento de géneros
│   └── mpc_server.py   # Interfaz con servidor MPC
│
├── widgets/            # Widgets personalizados
│   ├── file_list_widget.py
│   ├── control_panel.py
│   ├── backup_panel.py
│   └── results_panel.py
│
├── threads/           # Procesamiento asíncrono
│   └── processing_thread.py
│
├── main_window.py    # Ventana principal
└── style.py         # Estilos y temas
```

## Características Principales

- Interfaz moderna y accesible
- Soporte para drag & drop
- Procesamiento asíncrono
- Integración con MPC server
- Sistema de respaldo automático
- Temas claros y oscuros
- Logging detallado

## Componentes Principales

### MainWindow
Ventana principal que integra todos los componentes:
- Lista de archivos
- Panel de control
- Gestión de respaldos
- Visualización de resultados

### Modelos
- `GenreModel`: Procesamiento de géneros
- `MPCServer`: Comunicación con servidor MPC

### Widgets
- `FileListWidget`: Gestión de archivos
- `ControlPanel`: Configuración
- `BackupPanel`: Sistema de respaldo
- `ResultsPanel`: Visualización de resultados

### Threads
- `ProcessingThread`: Procesamiento asíncrono

## Uso

```python
from PySide6.QtWidgets import QApplication
from src.gui import MainWindow

# Crear aplicación
app = QApplication([])

# Crear y mostrar ventana principal
window = MainWindow()
window.show()

# Ejecutar aplicación
app.exec()
```

## Personalización

### Tema Oscuro
```python
from src.gui.style import apply_dark_theme

# Aplicar tema oscuro
apply_dark_theme(window)
```

### Configuración
```python
# Directorio de respaldo personalizado
window.backup_dir = "/ruta/personalizada"

# Configurar modelo
window.model.min_confidence = 0.2
window.model.max_api_tags = 100
window.model.rename_after_update = True
```

## Señales

El sistema utiliza señales Qt para la comunicación entre componentes:
- `files_added`: Nuevos archivos añadidos
- `settings_changed`: Cambios en configuración
- `backup_dir_changed`: Cambio en directorio de respaldo
- `process_files_triggered`: Inicio de procesamiento
