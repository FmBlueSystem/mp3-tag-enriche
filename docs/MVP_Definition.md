# 🚀 Definición del MVP (Minimum Viable Product) - Nueva Biblioteca

Este documento detalla el conjunto mínimo de funcionalidades para la primera versión viable y útil de la aplicación "Nueva Biblioteca". Está basado en la tarea A3AbgCMSzts3.

## 🎯 Objetivo del MVP

Definir el conjunto mínimo de funcionalidades para un producto viable y útil que permita a los usuarios crear y gestionar playlists inteligentes básicas.

## 🔥 Core Features del MVP

### 1. Motor Básico de Reglas (ESENCIAL)

-   **Parser de expresiones simples:** `campo operador valor` (ej. `genre = 'House'`).
-   **Operadores básicos de comparación:** `=`, `!=`, `>`, `<`, `IN`.
-   **Operadores lógicos:** `AND`, `OR`.
-   **Validación de sintaxis básica:** El sistema debe ser capaz de identificar y reportar errores en la sintaxis de las reglas.
-   **Ejemplo de regla MVP:** `genre = 'House' AND bpm > 120`

### 2. Persistencia Mínima (ESENCIAL)

-   **Base de datos SQLite:** Utilizará el esquema definido en `docs/database_schema.md`.
-   **Tablas esenciales para el MVP:** `tracks`, `smart_playlists`, `rules`, `playlist_tracks`.
-   **Operaciones CRUD básicas:** Para las entidades de playlist y reglas.
-   **Backup/Restore simple:** Funcionalidad básica para exportar/importar la base de datos o configuraciones (detalle a definir, podría ser manual inicialmente).
-   **No incluye en MVP:** Historial detallado de cambios, versionado avanzado de reglas, auditoría completa.

### 3. UI Básica Funcional (ESENCIAL)

-   **Lista de playlists inteligentes:** Mostrar las playlists existentes.
-   **Editor de reglas con texto:** Un campo de texto simple para escribir la expresión de la regla (sin drag-and-drop en el MVP).
-   **Preview de resultados:** Mostrar una lista de las primeras N pistas (ej. 20 pistas) que coinciden con la regla de la playlist seleccionada.
-   **Botones de acción básicos:** Crear nueva playlist, Editar playlist (nombre y regla), Eliminar playlist, Exportar playlist.
-   **No incluye en MVP:** Wireframes complejos, rueda Camelot interactiva, sliders avanzados para rangos, UI drag-and-drop para reglas.

### 4. Exportación M3U (ESENCIAL)

-   **Generación de archivo M3U básico:** Exportar la lista de pistas de una playlist inteligente a un archivo `.m3u`.
-   **Rutas de archivo:** Opción de rutas absolutas o relativas (configurable o predefinido para MVP).
-   **Compatibilidad:** El archivo M3U generado debe ser compatible con reproductores estándar.
-   **No incluye en MVP:** Formatos de exportación avanzados, inclusión de metadatos extendidos en el M3U.

## 🚫 Lo que NO está en el MVP (Planificado para v2.0 o posterior)

-   ❌ Rueda Camelot interactiva.
-   ❌ Recomendador de progresión energética.
-   ❌ Triggers automáticos para actualización de playlists.
-   ❌ UI con Drag & Drop para la construcción de reglas.
-   ❌ Plantillas de reglas predefinidas (más allá de ejemplos muy básicos si se decide).
-   ❌ Integración profunda con APIs externas para enriquecimiento de metadatos en tiempo real (se asume que los datos básicos en la tabla `tracks` ya existen o se cargan por un proceso separado para el MVP).
-   ❌ Visualizaciones avanzadas de la biblioteca o playlists.
-   ❌ Sistema de triggers programados o basados en eventos complejos.

## 📊 Criterios de Éxito del MVP

### Funcionales:

-   [ ] El usuario puede crear una nueva playlist inteligente especificando un nombre y una regla simple basada en texto.
-   [ ] Las reglas de las playlists se evalúan correctamente contra la tabla `tracks`.
-   [ ] Los resultados (lista de pistas) de una playlist seleccionada se muestran al usuario (preview).
-   [ ] El usuario puede exportar una playlist inteligente a un archivo M3U funcional.
-   [ ] El sistema persiste correctamente los datos de playlists y sus reglas.

### No Funcionales:

-   [ ] El sistema puede procesar una biblioteca de al menos 1000 pistas y evaluar reglas simples en menos de 5 segundos (objetivo inicial).
-   [ ] La interfaz de usuario básica responde a las acciones del usuario en menos de 200ms (para las operaciones del MVP).
-   [ ] El motor de reglas puede manejar expresiones con hasta 10 condiciones combinadas con AND/OR (para el MVP).
-   [ ] La aplicación (en su forma MVP) puede ejecutarse en Windows, macOS y Linux (asumiendo Python y SQLite como base).

## 🕐 Timeline Estimado del MVP

-   **Duración estimada total:** 15-20 días de desarrollo (aproximación inicial).
-   **Hitos principales:**
    1.  **Días 1-5:** Implementación de la persistencia SQLite (CRUDs básicos para MVP) y carga inicial de datos de prueba.
    2.  **Días 6-10:** Desarrollo y pruebas del motor de reglas básico (parser ya existe, foco en evaluación y aplicación a DB).
    3.  **Días 11-15:** Creación de la UI básica funcional (lista de playlists, editor textual, preview).
    4.  **Días 16-20:** Implementación de la exportación M3U y testing integral del MVP.

## 🎯 Definición de "Done" para el MVP

Se considerará que el MVP está "Done" cuando un usuario pueda realizar las siguientes acciones de forma consecutiva y exitosa:

1.  Instalar y ejecutar la aplicación (MVP).
2.  Crear una playlist inteligente nueva (ej. "House Mayor a 120 BPM") mediante una regla simple basada en texto (ej. `genre = 'House' AND bpm > 120`).
3.  Ver la lista de pistas que cumplen con la regla de la playlist creada.
4.  Exportar dicha playlist a un archivo M3U.
5.  Cargar y reproducir el archivo M3U resultante en un reproductor de música estándar (ej. VLC, Foobar2000).

**En resumen: MVP = FUNCIONAL + ÚTIL + SIMPLE** 