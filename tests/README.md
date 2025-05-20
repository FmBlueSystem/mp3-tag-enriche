# Pruebas de Integración End-to-End

Este directorio contiene las pruebas de integración end-to-end del sistema de detección de géneros musicales.

## Requisitos Previos

- Python 3.8 o superior
- pytest instalado (`pip install pytest`)
- Archivos MP3 de prueba disponibles en el directorio especificado en `conftest.py`

## Estructura de Pruebas

```
tests/
├── conftest.py           # Fixtures compartidos
├── test_integration.py   # Pruebas de integración end-to-end
└── utils.py             # Utilidades de prueba
```

## Ejecución de Pruebas

Para ejecutar todas las pruebas de integración:

```bash
pytest tests/test_integration.py -v
```

Para ejecutar una prueba específica:

```bash
pytest tests/test_integration.py::TestIntegrationEndToEnd::test_flujo_normal_completo -v
```

## Casos de Prueba

### 1. Flujo Normal Completo
- Verifica el procesamiento completo de archivos MP3
- Comprueba la detección y normalización de géneros
- Valida la integración con el modelo de datos
- Mide tiempos de procesamiento

### 2. Manejo de Errores y Recuperación
- Prueba la resistencia ante archivos corruptos
- Verifica el logging de errores
- Comprueba la recuperación del sistema

### 3. Límites del Sistema
- Valida el número máximo de géneros
- Verifica umbrales de confianza
- Comprueba restricciones de memoria

### 4. Escenarios Concurrentes
- Prueba el procesamiento paralelo
- Verifica la cola de tareas
- Valida la sincronización

## Interpretación de Resultados

### Métricas Clave
1. **Tiempo de Procesamiento**: Debe ser < 30 segundos por archivo
2. **Tasa de Éxito**: ≥ 95% de archivos procesados correctamente
3. **Precisión de Géneros**: Todos los géneros deben superar el umbral de confianza

### Logs y Reportes
- Los errores se registran en el log de pruebas
- Cada prueba genera métricas detalladas
- Los resultados incluyen estadísticas de rendimiento

## Solución de Problemas

### Errores Comunes
1. **Archivos no encontrados**: Verificar rutas en `conftest.py`
2. **Timeouts**: Ajustar timeouts en la configuración
3. **Errores de API**: Verificar conexión y credenciales

### Depuración
- Usar `pytest -vv` para más detalles
- Revisar logs en `app.log`
- Verificar `cache/` para problemas de caché

## Mantenimiento

### Actualización de Pruebas
1. Mantener fixtures actualizados en `conftest.py`
2. Actualizar umbrales según cambios en el sistema
3. Agregar nuevos casos según se agreguen funcionalidades

### Mejores Prácticas
- Mantener pruebas independientes
- Documentar cambios significativos
- Actualizar valores esperados según evolucione el sistema