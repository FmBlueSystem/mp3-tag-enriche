# GUÍA DE MANTENIMIENTO DEL SISTEMA
**Sistema de Detección de Géneros Musicales v2.0**

## 🚀 COMANDOS DE VERIFICACIÓN RÁPIDA

### Verificación de Estado General
```bash
# Verificación básica (30s)
python monitor_system_health.py

# Verificación completa con tests (2-3 min)
python monitor_system_health.py --full

# Verificación silenciosa para scripts
python monitor_system_health.py --quiet
```

### Validación de Mejoras Implementadas
```bash
# Ejecutar tests de mejoras específicas
python test_improvements.py

# Ver resumen de mejoras implementadas
cat comprehensive_improvement_summary.json | python -m json.tool
```

## 🔧 COMANDOS DE MONITOREO

### Performance Monitor
```bash
# Obtener métricas actuales de performance
python -c "
from src.core.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
metrics = monitor.get_current_metrics()
import json
print(json.dumps(metrics, indent=2))
"

# Iniciar monitoreo de performance en background
python -c "from src.core.performance_monitor import setup_performance_monitoring; setup_performance_monitoring()"
```

### Error Handler
```bash
# Ver estadísticas de errores
python -c "
from src.core.error_handler import ErrorHandler
handler = ErrorHandler()
stats = handler.get_error_statistics()
print('Errores totales:', stats['total_errors'])
print('Errores por componente:', stats['errors_by_component'])
"

# Exportar historial de errores
python -c "
from src.core.error_handler import ErrorHandler
handler = ErrorHandler()
handler.export_error_history('error_history.json')
print('Historial exportado a error_history.json')
"
```

### API Metrics
```bash
# Ver métricas de APIs
python -c "
from src.core.api_metrics import MetricsTracker
tracker = MetricsTracker('api_metrics.json')
print('Métricas de Spotify:', tracker.get_metrics('Spotify'))
print('Métricas de LastFM:', tracker.get_metrics('LastFM'))
"

# Resetear métricas de una API específica
python -c "
from src.core.api_metrics import MetricsTracker
tracker = MetricsTracker('api_metrics.json')
tracker.reset_metrics('Spotify')
print('Métricas de Spotify reseteadas')
"
```

## 🧹 COMANDOS DE LIMPIEZA

### Cache Management
```bash
# Limpiar cache antiguo (más de 30 días)
python -c "
from src.core.persistent_cache import PersistentCache
cache = PersistentCache('cache')
cleaned = cache.cleanup_old_entries(max_age_days=30)
print(f'Entradas limpiadas: {cleaned}')
"

# Ver estadísticas de cache
python -c "
from src.core.persistent_cache import PersistentCache
cache = PersistentCache('cache')
stats = cache.get_cache_stats()
print('Entradas totales:', stats['total_entries'])
print('Tamaño total (MB):', stats['total_size_mb'])
"

# Sanitizar nombres de archivos problemáticos
python -c "
from src.core.persistent_cache import sanitize_cache_filename
test_name = 'Artist: Name <Bad> Characters?.mp3'
clean_name = sanitize_cache_filename(test_name)
print(f'Original: {test_name}')
print(f'Sanitizado: {clean_name}')
"
```

### Log Management
```bash
# Ver últimos errores críticos
tail -100 app.log | grep "CRITICAL\|ERROR" | tail -20

# Comprimir logs antiguos (manual)
gzip app.log.old

# Rotar logs (manual)
mv app.log app.log.old && touch app.log
```

## 🎯 COMANDOS DE TESTING

### Ejecutar Tests Específicos
```bash
# Tests de normalización de géneros
python -m pytest tests/test_file_handler.py::TestGenreNormalization -v

# Tests de métricas de API
python -m pytest tests/test_api_metrics.py -v

# Tests de detección de géneros
python -m pytest tests/test_genre_detection.py -v

# Tests con cobertura
python -m pytest tests/ --cov=src --cov-report=html
```

### Validación de Configuración
```bash
# Verificar configuración dinámica
python -c "
from src.core.config_loader import ConfigLoader
config = ConfigLoader('config/dynamic_settings.json')
print('Configuración válida:', config.validate_config())
"

# Obtener umbral dinámico
python -c "
from src.core.config_loader import DynamicConfig
dynamic = DynamicConfig()
threshold = dynamic.get_dynamic_threshold(
    num_apis=3,
    confidence_spread=0.4,
    base_context={'genre_detection': {'base_threshold': 0.3}}
)
print(f'Umbral dinámico: {threshold}')
"
```

## 🔍 COMANDOS DE DIAGNÓSTICO

### Validación de Datos
```bash
# Validar nombres de archivo
python -c "
from src.core.data_validator import DataValidator
validator = DataValidator()
print('Válido:', validator.validate_filename('Artist - Song.mp3'))
print('Sanitizado:', validator.safe_filename('Artist/Bad<Name>.mp3'))
"

# Validar género musical
python -c "
from src.core.data_validator import DataValidator
validator = DataValidator()
print('Es género válido:', validator.validate_genre('Electronic'))
print('URL válida:', validator.validate_url('https://api.spotify.com/track/123'))
"
```

### Fallback de Géneros
```bash
# Probar fallback de géneros
python -c "
from src.core.genre_detector import get_fallback_genres
fallbacks = get_fallback_genres('Calvin Harris', 'Summer Remix')
print('Géneros de fallback:', fallbacks)
"

# Normalizar géneros con confianza
python -c "
from src.core.genre_normalizer import GenreNormalizer
normalized, confidence = GenreNormalizer.normalize('Electronic Dance Music')
print(f'Normalizado: {normalized} (confianza: {confidence})')
"
```

## 📊 COMANDOS DE REPORTES

### Generar Reporte de Estado
```bash
# Reporte básico en consola
python monitor_system_health.py

# Reporte completo guardado en archivo
python monitor_system_health.py --full --output=daily_report.json

# Reporte programático (para scripts)
python monitor_system_health.py --quiet --output=status.json
echo $? # 0=HEALTHY, 1=WARNING, 2=UNHEALTHY, 3=CRITICAL
```

### Métricas de Performance
```bash
# Exportar todas las métricas
python -c "
from src.core.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
monitor.export_metrics('performance_metrics.json')
print('Métricas exportadas a performance_metrics.json')
"

# Ver alertas activas
python -c "
from src.core.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
alerts = monitor.get_active_alerts()
for alert in alerts:
    print(f'⚠️ {alert}')
"
```

## 🔄 COMANDOS DE MANTENIMIENTO AUTOMÁTICO

### Script de Mantenimiento Diario
```bash
#!/bin/bash
# daily_maintenance.sh

echo "🔧 Iniciando mantenimiento diario..."

# 1. Verificar estado del sistema
python monitor_system_health.py --output=daily_health.json

# 2. Limpiar cache antiguo
python -c "from src.core.persistent_cache import PersistentCache; PersistentCache('cache').cleanup_old_entries(30)"

# 3. Exportar métricas
python -c "from src.core.api_metrics import MetricsTracker; MetricsTracker('api_metrics.json').export_metrics('daily_api_metrics.json')"

# 4. Verificar logs de errores
ERROR_COUNT=$(tail -1000 app.log | grep -c "ERROR\|CRITICAL")
echo "Errores en últimas 1000 líneas: $ERROR_COUNT"

echo "✅ Mantenimiento diario completado"
```

### Script de Mantenimiento Semanal
```bash
#!/bin/bash
# weekly_maintenance.sh

echo "🛠️ Iniciando mantenimiento semanal..."

# 1. Verificación completa del sistema
python monitor_system_health.py --full --output=weekly_health.json

# 2. Ejecutar tests completos
python test_improvements.py > weekly_tests.log

# 3. Comprimir logs antiguos
[ -f app.log.old ] && gzip app.log.old

# 4. Generar reporte de performance
python -c "
from src.core.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
monitor.export_metrics('weekly_performance.json')
"

# 5. Backup de configuraciones
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

echo "✅ Mantenimiento semanal completado"
```

## 🚨 COMANDOS DE EMERGENCIA

### En caso de fallos críticos
```bash
# 1. Verificar estado general
python monitor_system_health.py --full

# 2. Ver errores recientes
tail -50 app.log | grep "CRITICAL\|ERROR"

# 3. Resetear cache si hay problemas
rm -rf cache/*.json

# 4. Regenerar configuraciones
python apply_improvements.py

# 5. Ejecutar tests básicos
python test_improvements.py
```

### Restaurar desde backup
```bash
# Restaurar configuraciones
tar -xzf config_backup_YYYYMMDD.tar.gz

# Verificar integridad
python monitor_system_health.py --full

# Re-ejecutar mejoras si es necesario
python apply_improvements.py
```

## 📅 CRONOGRAMA DE MANTENIMIENTO RECOMENDADO

### Diario (Automatizado)
- ✅ Verificación básica de salud del sistema
- ✅ Limpieza de cache antiguo
- ✅ Exportación de métricas diarias

### Semanal (Semi-automatizado)  
- ✅ Verificación completa con tests
- ✅ Backup de configuraciones
- ✅ Compresión de logs antiguos
- ✅ Reporte de performance semanal

### Mensual (Manual)
- 🔍 Revisión manual de logs de errores
- 📊 Análisis de tendencias de performance
- 🎯 Optimización de umbrales dinámicos
- 📝 Actualización de documentación

---

**💡 Tip:** Ejecuta `python monitor_system_health.py` antes de cualquier operación de mantenimiento para conocer el estado actual del sistema. 