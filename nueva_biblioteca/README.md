# Nueva Biblioteca 🎵

**Sistema Inteligente de Gestión de Bibliotecas Musicales con Material 3 Expressive**

Nueva Biblioteca es una aplicación moderna y expresiva para gestionar bibliotecas musicales con capacidades avanzadas de filtrado inteligente, playlists dinámicas y búsquedas complejas basadas en reglas lógicas.

## ✨ Características Principales

### 🎨 Interfaz Material 3 Expressive
- **Diseño moderno y vibrante** con paleta de colores expresiva
- **Animaciones fluidas** y transiciones suaves
- **Componentes adaptativos** que responden al contexto
- **Tipografía legible** con jerarquía visual clara
- **Tema dark purple** optimizado para uso prolongado

### 🧠 Motor de Reglas Inteligente
- **Parser de expresiones lógicas** completo y robusto
- **Evaluador de reglas** optimizado para grandes datasets
- **Operadores especializados** para música (COMPATIBLE_WITH, CONTAINS, etc.)
- **Validación en tiempo real** con mensajes descriptivos
- **Análisis de rendimiento** y sugerencias de optimización

### 🎵 Gestión Musical Avanzada
- **Metadatos completos**: título, artista, álbum, género, BPM, clave, energía, valencia, etc.
- **Búsqueda inteligente** por texto y reglas complejas
- **Filtros rápidos** predefinidos para casos comunes
- **Compatibilidad Camelot** para mezcla armónica
- **Estadísticas detalladas** de la biblioteca

### 📋 Playlists Inteligentes
- **Creación dinámica** basada en reglas
- **Actualización automática** cuando cambian los datos
- **Plantillas predefinidas** para diferentes estilos
- **Análisis de rendimiento** de las reglas
- **Export/Import** en formato JSON

## 🚀 Instalación y Configuración

### Requisitos
- Python 3.8+
- PySide6
- qt-material

### Instalación
```bash
# Clonar el repositorio
git clone <repository-url>
cd nueva_biblioteca

# Crear entorno virtual
python -m venv nueva_biblioteca_env
source nueva_biblioteca_env/bin/activate  # En Windows: nueva_biblioteca_env\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python main.py
```

### Verificar Instalación
```bash
# Ejecutar pruebas de integración
python test_integration.py
```

## 📖 Guía de Uso

### Búsqueda Básica
1. **Búsqueda por texto**: Escribe en la barra de búsqueda para buscar por título, artista, álbum o género
2. **Filtros rápidos**: Haz clic en el botón ⚡ para acceder a filtros predefinidos
3. **Limpiar búsqueda**: Usa el botón ✕ para mostrar toda la biblioteca

### Búsqueda Avanzada con Reglas
1. **Activar modo reglas**: Haz clic en el botón 🔍 para alternar al modo de reglas
2. **Escribir reglas**: Usa la sintaxis de reglas para crear filtros complejos
3. **Ayuda**: Haz clic en el botón ? para ver ejemplos y operadores disponibles

### Ejemplos de Reglas

#### Reglas Básicas
```
genre = 'House'                    # Género exacto
bpm BETWEEN 120 AND 140           # Rango de BPM
energy > 0.8                      # Alta energía
rating >= 4                       # Bien valorados
```

#### Reglas Complejas
```
(genre = 'House' OR genre = 'Progressive House') AND bpm > 120
energy > 0.7 AND danceability > 0.6 AND valence > 0.5
artist CONTAINS 'deadmau5' OR (rating >= 5 AND play_count > 50)
key COMPATIBLE_WITH '8A' AND energy BETWEEN 0.6 AND 0.9
```

#### Operadores Especiales
```
artist CONTAINS 'martin'          # Contiene texto
title STARTS_WITH 'The'          # Empieza con
genre ENDS_WITH 'House'          # Termina con
key COMPATIBLE_WITH '8A'         # Compatibilidad Camelot
year IN [2010, 2011, 2012]       # Lista de valores
```

### Playlists Inteligentes
1. **Crear playlist**: Usa el panel de playlists para crear nuevas playlists inteligentes
2. **Definir reglas**: Especifica las reglas que determinarán qué tracks incluir
3. **Personalizar**: Asigna nombre, descripción, color e icono
4. **Actualización automática**: La playlist se actualiza cuando cambien los datos

## 🏗️ Arquitectura del Sistema

### Estructura del Proyecto
```
nueva_biblioteca/
├── src/
│   ├── core/                     # Motor de reglas core
│   │   ├── expression_ast.py     # AST y nodos de expresiones
│   │   ├── rule_parser.py        # Parser de reglas lógicas
│   │   ├── rule_evaluator.py     # Evaluador de reglas
│   │   └── rule_engine.py        # Motor principal
│   ├── services/                 # Servicios de aplicación
│   │   ├── music_service.py      # Gestión de datos musicales
│   │   └── rule_service.py       # Integración de reglas con UI
│   └── ui/                       # Interfaz de usuario
│       ├── components/           # Componentes reutilizables
│       ├── views/               # Vistas principales
│       ├── dialogs/             # Diálogos modales
│       └── main_window.py       # Ventana principal
├── config/                      # Configuración
├── tests/                       # Pruebas unitarias
├── main.py                      # Punto de entrada
└── test_integration.py          # Pruebas de integración
```

### Componentes Principales

#### Motor de Reglas Core
- **ExpressionAST**: Representación en árbol de expresiones lógicas
- **RuleParser**: Parser recursivo descendente con precedencia de operadores
- **RuleEvaluator**: Evaluador optimizado con soporte para generadores
- **RuleEngine**: Coordinador principal con gestión de playlists

#### Servicios de Aplicación
- **MusicService**: Gestión de datos musicales y metadatos
- **RuleService**: Integración del motor de reglas con la UI

#### Interfaz de Usuario
- **SearchBar**: Barra de búsqueda con modo de reglas
- **LibraryView**: Vista de biblioteca con tabla de tracks
- **FilterPanel**: Panel de filtros avanzados
- **PlaylistPanel**: Gestión de playlists inteligentes

## 🔧 Campos y Operadores Disponibles

### Campos Musicales
| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `title` | String | Título del track | "Strobe" |
| `artist` | String | Artista | "deadmau5" |
| `album` | String | Álbum | "For Lack of a Better Name" |
| `genre` | String | Género musical | "Progressive House" |
| `bpm` | Number | Beats por minuto | 128 |
| `key` | String | Clave musical (Camelot) | "8A" |
| `energy` | Number | Nivel de energía (0-1) | 0.7 |
| `valence` | Number | Valencia/positividad (0-1) | 0.6 |
| `danceability` | Number | Bailabilidad (0-1) | 0.8 |
| `year` | Number | Año de lanzamiento | 2009 |
| `duration` | Number | Duración en segundos | 636 |
| `rating` | Number | Calificación (1-5) | 5 |
| `play_count` | Number | Número de reproducciones | 42 |
| `last_played` | String | Última reproducción (ISO) | "2024-01-15T..." |

### Operadores Disponibles
| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `=` | Igual | `genre = 'House'` |
| `!=` | Diferente | `genre != 'Dubstep'` |
| `>` | Mayor que | `bpm > 120` |
| `<` | Menor que | `energy < 0.5` |
| `>=` | Mayor o igual | `rating >= 4` |
| `<=` | Menor o igual | `year <= 2010` |
| `BETWEEN` | Entre valores | `bpm BETWEEN 120 AND 140` |
| `IN` | En lista | `year IN [2010, 2011, 2012]` |
| `CONTAINS` | Contiene texto | `artist CONTAINS 'martin'` |
| `STARTS_WITH` | Empieza con | `title STARTS_WITH 'The'` |
| `ENDS_WITH` | Termina con | `genre ENDS_WITH 'House'` |
| `COMPATIBLE_WITH` | Compatible Camelot | `key COMPATIBLE_WITH '8A'` |

### Conectores Lógicos
| Conector | Descripción | Ejemplo |
|----------|-------------|---------|
| `AND` | Y lógico | `energy > 0.8 AND bpm > 120` |
| `OR` | O lógico | `genre = 'House' OR genre = 'Techno'` |
| `NOT` | Negación | `NOT (genre = 'Dubstep')` |
| `()` | Agrupación | `(A OR B) AND C` |

## 🎯 Filtros Rápidos Predefinidos

- **⚡ Alta Energía**: `energy > 0.8`
- **🏠 House Music**: `genre CONTAINS 'House'`
- **🆕 Tracks Recientes**: `year > 2015`
- **🎵 BPM Medio**: `bpm BETWEEN 120 AND 140`
- **⭐ Favoritos**: `rating >= 4`
- **🔥 Muy Reproducidos**: `play_count > 30`
- **😌 Chill Vibes**: `energy < 0.5 AND valence > 0.4`
- **💪 Workout**: `energy > 0.8 AND bpm BETWEEN 120 AND 140`
- **🎖️ Clásicos**: `year < 2010 AND rating >= 4`
- **🎹 Compatibles 8A**: `key COMPATIBLE_WITH '8A'`

## 🧪 Testing y Desarrollo

### Ejecutar Pruebas
```bash
# Pruebas de integración completa
python test_integration.py

# Pruebas del parser de reglas
python test_parser.py

# Pruebas unitarias
python -m pytest tests/
```

### Desarrollo
```bash
# Activar entorno de desarrollo
source nueva_biblioteca_env/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar con recarga automática
python main.py --dev
```

## 📊 Rendimiento y Optimización

### Características de Rendimiento
- **Evaluación lazy**: Los filtros se evalúan solo cuando es necesario
- **Short-circuit evaluation**: Optimización automática de expresiones lógicas
- **Generadores**: Soporte para datasets grandes sin cargar todo en memoria
- **Caché inteligente**: Resultados de reglas complejas se cachean automáticamente
- **Análisis de rendimiento**: Métricas detalladas de tiempo de ejecución

### Recomendaciones
- Usa campos indexados (`genre`, `artist`, `year`) para mejor rendimiento
- Coloca condiciones más selectivas al inicio de expresiones AND
- Usa `CONTAINS` con moderación en datasets grandes
- Aprovecha los filtros rápidos para casos comunes

## 🤝 Contribución

### Cómo Contribuir
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

### Estándares de Código
- Sigue PEP 8 para estilo de Python
- Documenta todas las funciones públicas
- Incluye pruebas para nuevas funcionalidades
- Usa type hints donde sea apropiado

## 📝 Changelog

### v1.0.0 (2024-01-15)
- ✨ Implementación completa del motor de reglas
- 🎨 Interfaz Material 3 Expressive
- 🔍 Búsqueda inteligente con reglas complejas
- 📋 Playlists inteligentes dinámicas
- ⚡ Filtros rápidos predefinidos
- 🎵 Compatibilidad Camelot para DJs
- 📊 Análisis de rendimiento y estadísticas
- 🧪 Suite completa de pruebas

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- **Material Design 3** por las guías de diseño expresivo
- **PySide6** por el framework de UI robusto
- **qt-material** por los temas Material Design
- **Camelot Wheel** por el sistema de compatibilidad armónica

---

**Nueva Biblioteca** - Donde la música inteligente encuentra el diseño expresivo 🎵✨
