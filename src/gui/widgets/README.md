# Widgets Package

Este paquete contiene los widgets personalizados para la interfaz gráfica de Genre Detector.

## Componentes

- `FileListWidget`: Widget para mostrar y gestionar la lista de archivos MP3
- `ControlPanel`: Panel de control con opciones de configuración
- `BackupPanel`: Panel para gestionar el directorio de respaldo
- `ResultsPanel`: Panel para mostrar resultados y progreso

## Diagrama de Componentes

```
+----------------+     +----------------+
|  FileListWidget|     |  ControlPanel  |
+----------------+     +----------------+
        |                     |
        v                     v
+----------------------------------------+
|             MainWindow                  |
+----------------------------------------+
        ^                     ^
        |                     |
+----------------+     +----------------+
|   BackupPanel  |     | ResultsPanel   |
+----------------+     +----------------+
```

## Características

- Todos los widgets están diseñados para ser accesibles
- Soporte para drag & drop en FileListWidget
- Configuraciones persistentes en ControlPanel
- Sistema de respaldo integrado en BackupPanel
- Visualización en tiempo real en ResultsPanel

## Uso

```python
from src.gui.widgets import (
    FileListWidget,
    ControlPanel,
    BackupPanel,
    ResultsPanel
)

# Crear instancias
file_list = FileListWidget()
control = ControlPanel()
backup = BackupPanel()
results = ResultsPanel()

# Conectar señales
file_list.files_added.connect(on_files_added)
control.settings_changed.connect(on_settings_changed)
backup.backup_dir_changed.connect(on_backup_dir_changed)
