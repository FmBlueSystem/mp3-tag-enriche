# Threads Package

Este paquete contiene los hilos de procesamiento para operaciones asíncronas en Genre Detector.

## Componentes

- `ProcessingThread`: Hilo para procesar archivos MP3 en segundo plano

## Diagrama de Componentes

```
+----------------+     +----------------+
| ProcessingThread| --> |  GenreModel   |
+----------------+     +----------------+
        |                    |
        v                    v
+----------------+     +----------------+
|  GUI Updates   |     |   MPCServer   |
+----------------+     +----------------+
```

## Señales

### ProcessingThread
- `progress`: Emite mensajes de progreso durante el procesamiento
- `finished`: Emite resultados finales al completar el procesamiento
- `file_processed`: Emite resultados individuales por archivo

## Características

- Procesamiento asíncrono de archivos
- Actualización en tiempo real de la interfaz
- Manejo de errores robusto
- Integración con sistema de respaldo
- Soporte para cancelación de operaciones
- Logging detallado

## Uso

```python
from src.gui.threads import ProcessingThread

# Crear instancia del hilo
thread = ProcessingThread(
    file_paths=["/ruta/archivo1.mp3", "/ruta/archivo2.mp3"],
    model=genre_model,
    analyze_only=True,
    confidence=0.3,
    max_genres=3,
    rename_files=False,
    backup_dir="/ruta/respaldos"
)

# Conectar señales
thread.progress.connect(on_progress_update)
thread.finished.connect(on_processing_complete)
thread.file_processed.connect(on_file_processed)

# Iniciar procesamiento
thread.start()
```

## Estructura de Resultados

```python
{
    "total": int,          # Total de archivos procesados
    "success": int,        # Operaciones exitosas
    "errors": int,         # Errores encontrados
    "renamed": int,        # Archivos renombrados
    "details": [           # Detalles por archivo
        {
            "filepath": str,
            "written_metadata_success": bool,
            "current_genre": str,
            "selected_genres_written": List[str],
            "threshold_used": float,
            "renamed_to": str,
            "error": str,
            "rename_error": str,
            "rename_message": str,
            "detected_genres_initial_clean": Dict[str, float],
            "detected_genres_written": List[str],
            "tag_update_error": str
        }
    ]
}
