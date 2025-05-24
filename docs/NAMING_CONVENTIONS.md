# Convenciones de Nombres para OrganizacionMusical (v1.0)

Este documento establece los estándares consistentes para la nomenclatura de carpetas, archivos y tags de metadatos dentro del proyecto OrganizacionMusical. El objetivo es asegurar la uniformidad, facilitar la búsqueda y mejorar la navegabilidad de la biblioteca musical.

## 1. Convenciones para Carpetas

La estructura de carpetas debe ser jerárquica y reflejar los metadatos clave de la música.

**Estructura Jerárquica Sugerida:**
`Género/Subgénero/Década/BPM`

**Reglas de Nomenclatura:**
-   **Caracteres:** Utilizar solo caracteres alfanuméricos, guiones (`-`) y guiones bajos (`_`). Evitar espacios, caracteres especiales (`/`, `\`, `*`, `?`, `"`, `<`, `>`, `|`, `:`, `;`, `,`, `!`, `@`, `#`, `$`, `%`, `^`, `&`, `(`, `)`, `[`, `]`, `{`, `}`), y acentos.
-   **Mayúsculas/Minúsculas:** Usar `CamelCase` o `PascalCase` para los nombres de géneros y subgéneros (ej. `Electronic`, `House`, `DeepHouse`). Para décadas y rangos de BPM, usar el formato numérico (ej. `2020s`, `120-130bpm`).
-   **Separadores:** Utilizar el carácter `/` para separar los niveles de la jerarquía de carpetas.

**Ejemplos:**
-   `Electronic/House/2020s/120-130bpm`
-   `Rock/Alternative/1990s/90-100bpm`
-   `Latin/Salsa/1970s/140-150bpm`

## 2. Convenciones para Archivos de Música

Los archivos de música (principalmente `.mp3`) deben seguir un formato estandarizado para facilitar su identificación y organización.

**Formato de Nombre de Archivo:**
`Artista - Título (Año).mp3`

**Reglas de Nomenclatura:**
-   **Separador Principal:** Utilizar ` - ` (espacio, guion, espacio) para separar el Artista del Título.
-   **Año:** El año debe ir entre paréntesis al final del título, antes de la extensión.
-   **Caracteres:** Similar a las carpetas, evitar caracteres especiales. Reemplazar espacios por guiones bajos (`_`) si es necesario para compatibilidad en sistemas de archivos, aunque el formato `Artista - Título (Año).mp3` con espacios es preferible para legibilidad.
-   **Colaboraciones:** Para colaboraciones, usar `Artista1 & Artista2 - Título (Año).mp3`.
-   **Remixes/Versiones:** Incluir la información del remix o versión entre paréntesis después del título, antes del año, si aplica: `Artista - Título (Remixer Remix) (Año).mp3`.

**Ejemplos:**
-   `Daft Punk - One More Time (2000).mp3`
-   `Calvin Harris & Dua Lipa - One Kiss (2018).mp3`
-   `The Weeknd - Blinding Lights (Remix by Major Lazer) (2019).mp3`

## 3. Convenciones para Tags de Metadatos (ID3 Tags)

Los tags ID3 de los archivos MP3 son cruciales para la organización y las Playlists Inteligentes. Deben ser consistentes y completos.

**Campos Obligatorios (Mínimos):**
-   `Título`
-   `Artista`
-   `Género`
-   `Año`
-   `BPM` (Beats Per Minute)
-   `Key` (Tonalidad musical, preferiblemente en formato Camelot)
-   `Nivel de Energía` (Escala definida por el proyecto, ej. 1-10)

**Reglas de Formato para Tags:**
-   **Género:** Utilizar una taxonomía unificada de géneros y subgéneros. Evitar variaciones (ej. "House" vs "house"). Si un género no está en la lista, mapearlo al más cercano o categorizarlo como "Unsorted".
-   **BPM:** Valor numérico entero (ej. `125`).
-   **Key (Camelot):** Formato estándar Camelot (ej. `8A`, `5B`).
-   **Nivel de Energía:** Valor numérico entero en la escala definida (ej. `7`).
-   **Año:** Formato de 4 dígitos (ej. `2023`).
-   **Artistas Múltiples:** Separar con `; ` (punto y coma y espacio) en el tag de Artista (ej. `Artista1; Artista2`).

**Mapeo de Géneros:**
Se mantendrá una lista interna de géneros y subgéneros aceptados para asegurar la consistencia. Cualquier género detectado que no esté en esta lista será normalizado o marcado para revisión manual.

**Prioridad:** Alta
**Dependencias:** Definición de la taxonomía de géneros y la escala de energía.
