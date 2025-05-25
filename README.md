# 🎵 Nueva Biblioteca Musical v2.3

## Sistema Profesional de Gestión Musical con Herramientas de DJ

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://pypi.org/project/PyQt6/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-orange.svg)](https://sqlite.org)
[![Estado](https://img.shields.io/badge/Estado-v2.3%20COMPLETADO-brightgreen.svg)](docs/ESTADO_ACTUAL_V2.md)

Un sistema avanzado de gestión de biblioteca musical que combina playlists inteligentes, análisis armónico profesional y herramientas de DJ en una aplicación integrada.

---

## 🚀 Características Principales

### 🎛️ **NUEVO v2.3: Herramientas de DJ Profesionales**
- **Crossfader Virtual**: Control de mezcla con barras de volumen en tiempo real
- **Sincronización de BPM**: Cálculo automático de pitch para sincronización perfecta
- **Sugerencias Inteligentes**: Algoritmo que analiza compatibilidad de transiciones
- **Análisis de Transiciones**: Evaluación multi-factor (BPM + Armonía + Energía)
- **Motor de DJ**: Algoritmos profesionales para análisis de compatibilidad

### 🎵 Sistema de Playlists Inteligentes
- **Motor de reglas avanzado** con sintaxis natural expandida
- **Operadores de texto**: `STARTS WITH`, `ENDS WITH`
- **Operadores de rango**: `BETWEEN valor1 AND valor2`
- **Listas y conjuntos**: `IN ['Rock', 'Pop', 'Electronic']`
- **Evaluación automática** contra la base de datos
- **Exportación M3U** para software de DJ

### 🎛️ Rueda Camelot Interactiva
- **15 técnicas de mezcla armónica** implementadas
- **Filtrado por tonalidades** en tiempo real
- **Visualización circular** de relaciones armónicas
- **Integración completa** con la base de datos
- **Creación automática** de playlists desde filtros

### 📊 Análisis Completo de Biblioteca
- **Estadísticas generales** (tracks, artistas, álbumes, géneros)
- **Análisis de tonalidades** con distribución modal
- **Análisis de BPM** con rangos y promedios por género
- **Herramientas de limpieza** (duplicados, metadatos incompletos)
- **Gráficos integrados** con matplotlib
- **Exportación CSV** de estadísticas completas

### ✨ Enriquecimiento Automático de Metadatos
- **Múltiples APIs musicales**: MusicBrainz, Last.fm, Discogs, Wikipedia, iTunes
- **Normalización inteligente de géneros**: Unifica variaciones de nombres de géneros
- **Consultas paralelas**: Optimizado para velocidad y eficiencia
- **Sistema de confianza**: Combina resultados de múltiples fuentes con puntuaciones
- **Cache persistente**: Evita consultas repetidas y mejora rendimiento

### 🎭 Gestión Avanzada de Géneros
- **Normalización automática**: "rock music" → "Rock", "hip-hop" → "Hip Hop"
- **Categorización**: Agrupa géneros en categorías principales
- **Mapeos extensos**: Cubre cientos de variaciones de géneros
- **Puntuación de confianza**: Evalúa la precisión de cada género detectado

### 📊 Sistema de Métricas y Monitoreo
- **Tracking de APIs**: Latencia, tasa de éxito, llamadas por minuto
- **Rate limiting inteligente**: Respeta límites de cada API automáticamente
- **Manejo de errores robusto**: Fallbacks y reintentos automáticos
- **Estadísticas detalladas**: Monitoreo completo del rendimiento

### 🏷️ Extracción de Metadatos Mejorada
- **Soporte multi-formato**: MP3, FLAC, MP4, OGG Vorbis
- **Metadatos técnicos**: Bitrate, sample rate, duración, canales
- **Validación automática**: Detecta metadatos faltantes o inválidos
- **Enriquecimiento integrado**: Combina datos del archivo con APIs externas

---

## 🖥️ Capturas de Pantalla

### Tab de Herramientas DJ (v2.3)
```
🎧 Herramientas DJ
├── Crossfader Virtual
│   ├── Control deslizante (-1.0 a 1.0)
│   ├── Barras de volumen Track A/B
│   └── Indicadores de posición
├── Sincronización BPM
│   ├── Comparación automática
│   ├── Cálculo de pitch
│   └── Botones de sync bidireccional
└── Sugerencias de Transición
    ├── Lista ordenada por compatibilidad
    ├── Análisis de calidad
    └── Selección interactiva
```

### Rueda Camelot Interactiva
```
🎛️ Rueda Camelot
├── Visualización circular de tonalidades
├── 15 técnicas de mezcla profesionales
├── Filtrado interactivo por compatibilidad
└── Estadísticas de resultados
```

### Análisis de Biblioteca
```
📊 Análisis de Tracks
├── Estadísticas Generales
├── Análisis de Tonalidades
├── Análisis de BPM
├── Herramientas de Limpieza
└── Gráficos Visuales
```

---

## 🛠️ Instalación y Uso

### Requisitos
```bash
Python 3.8+
PyQt6
matplotlib
numpy
sqlite3 (incluido en Python)
```

### Instalación
```bash
# Clonar el repositorio
git clone <repository-url>
cd basico

# Instalar dependencias
pip install PyQt6 matplotlib numpy

# Ejecutar la aplicación completa
python3 -m src.ui.main_window

# O usar los demos específicos:
python3 demo_dj_tools.py          # Demo de herramientas DJ
python3 demo_analysis_tab.py      # Demo de análisis
python3 -m src.ui.camelot_wheel   # Demo de Rueda Camelot
```

### Uso Rápido
1. **Herramientas DJ**: Tab "🎧 Herramientas DJ"
   - Mueve el crossfader para mezclar
   - Usa botones de sync para BPM
   - Haz clic en sugerencias para transiciones

2. **Playlists Inteligentes**: Tab "🎵 Playlists Inteligentes"
   - Crea reglas como: `genre = 'Electronic' AND bpm BETWEEN 120 AND 140`
   - Evalúa automáticamente contra la biblioteca
   - Exporta a M3U para uso externo

3. **Rueda Camelot**: Tab "🎛️ Rueda Camelot"
   - Haz clic en tonalidades para filtrar
   - Activa técnicas de mezcla
   - Crea playlists desde filtros

4. **Análisis**: Tab "📊 Análisis de Tracks"
   - Revisa estadísticas de tu biblioteca
   - Busca duplicados y metadatos incompletos
   - Exporta datos para análisis externo

---

## 🏗️ Arquitectura

### Estructura del Proyecto
```
src/
├── core/                    # Lógica de negocio
│   ├── dj_engine.py        # 🆕 Motor de DJ profesional
│   ├── parser/             # Parser de reglas
│   ├── rule_engine.py      # Motor de evaluación
│   └── exporter.py         # Exportación M3U
├── data/                   # Capa de datos
│   ├── database_setup.py   # Configuración SQLite
│   └── crud.py            # Operaciones CRUD
├── ui/                     # Interfaz de usuario
│   ├── main_window.py      # Ventana principal (4 tabs)
│   ├── dj_tools_tab.py     # 🆕 Tab de herramientas DJ
│   ├── camelot_wheel.py    # Rueda Camelot interactiva
│   └── playlist_edit_dialog.py # Editor de playlists
└── tests/                  # Pruebas y validación
```

### Tecnologías
- **Backend**: Python 3.8+ con SQLite
- **Frontend**: PyQt6 con widgets personalizados
- **Gráficos**: matplotlib para visualizaciones
- **Arquitectura**: MVC con separación clara de responsabilidades

---

## 🎯 Casos de Uso

### 🎧 DJ Profesional
```python
# Ejemplo de uso del motor de DJ
from src.core.dj_engine import DJEngine, TrackInfo

dj = DJEngine()
track_a = TrackInfo(1, "Song A", "Artist", 128.0, "Am", "8A", 7, 4.5, 240)
track_b = TrackInfo(2, "Song B", "Artist", 132.0, "Em", "9A", 8, 4.0, 210)

# Analizar transición
analysis = dj.analyze_transition(track_a, track_b)
print(f"Compatibilidad: {analysis.compatibility_score}/100")
print(f"Pitch necesario: {analysis.pitch_adjustment}%")
```

### 🎵 Curador Musical
```python
# Crear playlist inteligente con reglas avanzadas
regla = "genre = 'Electronic' AND bpm BETWEEN 120 AND 140 AND rating >= 4"
# La aplicación evalúa automáticamente y genera la playlist
```

### 🎛️ Explorador Armónico
```python
# Usar la Rueda Camelot para encontrar compatibilidades
# Seleccionar 8A → obtener compatibles: 7A, 9A, 8B, 5B
# Crear playlist automática con progresión armónica
```

### 🎭 Normalización de Géneros
```python
from src.core.genre_normalizer import GenreNormalizer

# Ejemplos de normalización
GenreNormalizer.normalize("rock music")        # → ("Rock", 1.0)
GenreNormalizer.normalize("alternative rock")  # → ("Alternative Rock", 1.0)
GenreNormalizer.normalize("hip-hop")           # → ("Hip Hop", 1.0)
GenreNormalizer.normalize("electronic dance music") # → ("EDM", 0.8)

# Obtener categoría
GenreNormalizer.get_genre_category("Rock")     # → "Rock"
GenreNormalizer.get_genre_category("Techno")   # → "Electronic"
```

### 📊 Monitoreo y Métricas
```python
from src.core.api_metrics import get_all_metrics, log_metrics_summary

# Obtener métricas detalladas
metrics = get_all_metrics()
for api_name, stats in metrics.items():
    print(f"{api_name}: {stats['success_rate']:.2%} éxito")

# Log resumen completo
log_metrics_summary()
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🙏 Agradecimientos

- **MusicBrainz**: Base de datos musical abierta
- **Last.fm**: API de metadatos musicales
- **Discogs**: Base de datos de música y marketplace
- **Mutagen**: Biblioteca de metadatos de audio para Python

---

**Nueva Biblioteca v2.0** - Sistema de playlists inteligentes con enriquecimiento automático de metadatos 🎵
