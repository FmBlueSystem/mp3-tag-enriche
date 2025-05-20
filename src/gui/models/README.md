# Models Package

Este paquete contiene los modelos de datos y lógica de negocio para Genre Detector.

## Componentes

- `GenreModel`: Modelo principal para procesamiento de géneros musicales
- `MPCServer`: Interfaz para comunicación con el servidor MPC

## Diagrama de Componentes

```
+----------------+     +----------------+
|   GenreModel   | --> |   MPCServer   |
+----------------+     +----------------+
        |
        v
+------------------+
| GenreDetector    |
+------------------+
        |
        v
+------------------+
|  Mp3FileHandler  |
+------------------+
```

## Características

### GenreModel
- Procesamiento de géneros musicales
- Limpieza y normalización de nombres de géneros
- Gestión de confianza adaptativa
- Integración con sistema de respaldo
- Actualización automática de biblioteca MPC

### MPCServer
- Conexión al servidor MPC
- Actualización de biblioteca después de cambios
- Manejo de errores de conexión
- Logging de operaciones

## Uso

```python
from src.gui.models import GenreModel, MPCServer

# Crear instancia del modelo
model = GenreModel(backup_dir="/ruta/respaldos")

# Analizar archivo
result = model.analyze("/ruta/archivo.mp3")

# Procesar archivo
result = model.process(
    filepath="/ruta/archivo.mp3",
    confidence=0.3,
    max_genres=3,
    rename_flag=True
)

# Actualizar biblioteca MPC
model.mpc_server.update_library("/ruta/biblioteca")
```

## Configuración

### Términos en Lista Negra
```python
BLACKLIST_GENRE_TERMS_MODEL = {
    'victim', 'fire', 'universal', 'compilation',
    'soundtrack', 'http', 'fix', 'tag', ...
}
```

### Servidor MPC
```python
MPCServer(
    host='localhost',  # Host por defecto
    port=6600         # Puerto por defecto
)
