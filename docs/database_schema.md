# Esquema de la Base de Datos - Nueva Biblioteca

Este documento define la estructura de la base de datos SQLite para la aplicación "Nueva Biblioteca".

## Tablas

### 1. `tracks`

Almacena información detallada sobre cada pista de música.

-   `track_id` (INTEGER, PK, Autoincrement): Identificador único de la pista.
-   `file_path` (TEXT, UNIQUE, NOT NULL): Ruta absoluta al archivo de música en el sistema.
-   `file_hash` (TEXT, NOT NULL): Hash del contenido del archivo para detectar cambios.
-   `title` (TEXT): Título de la pista.
-   `artist` (TEXT): Artista principal de la pista.
-   `album_artist` (TEXT): Artista del álbum.
-   `album` (TEXT): Álbum al que pertenece la pista.
-   `genre` (TEXT): Género principal de la pista.
-   `year` (INTEGER): Año de lanzamiento.
-   `track_number` (INTEGER): Número de pista en el álbum.
-   `total_tracks_in_album` (INTEGER): Número total de pistas en el álbum.
-   `disc_number` (INTEGER): Número de disco en el álbum.
-   `total_discs_in_album` (INTEGER): Número total de discos en el álbum.
-   `duration_seconds` (REAL): Duración de la pista en segundos.
-   `bpm` (REAL): Beats Por Minuto.
-   `key` (TEXT): Tonalidad musical (ej. "C#m").
-   `camelot_key` (TEXT): Tonalidad en notación Camelot (ej. "1A").
-   `energy` (INTEGER): Nivel de energía percibido (escala 1-10).
-   `rating` (INTEGER): Calificación dada por el usuario (escala 1-5).
-   `play_count` (INTEGER, DEFAULT 0): Número de veces que se ha reproducido.
-   `last_played_at` (TIMESTAMP): Fecha y hora de la última reproducción.
-   `date_added_to_library` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Fecha en que se añadió a la biblioteca.
-   `last_metadata_update_at` (TIMESTAMP): Fecha de la última actualización de metadatos desde APIs externas.
-   `last_modified_file_timestamp` (TIMESTAMP): Fecha de la última modificación del archivo físico.
-   `bitrate_kbps` (INTEGER): Tasa de bits en kbps.
-   `sample_rate_hz` (INTEGER): Frecuencia de muestreo en Hz.
-   `channels` (INTEGER): Número de canales de audio (1 para mono, 2 para estéreo).
-   `comment` (TEXT): Comentarios generales del tag ID3.
-   `lyrics` (TEXT): Letra de la canción.

### 2. `smart_playlists`

Define las playlists inteligentes creadas por el usuario.

-   `playlist_id` (INTEGER, PK, Autoincrement): Identificador único de la playlist inteligente.
-   `name` (TEXT, NOT NULL): Nombre de la playlist.
-   `description` (TEXT): Descripción opcional de la playlist.
-   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Fecha de creación.
-   `updated_at` (TIMESTAMP): Fecha de la última modificación de la definición de la playlist.
-   `last_generated_at` (TIMESTAMP): Fecha en que la lista de pistas se generó/actualizó por última vez.
-   `is_enabled` (BOOLEAN, DEFAULT TRUE): Indica si la playlist debe actualizarse automáticamente por triggers.
-   `target_track_count` (INTEGER, NULLABLE): Número objetivo de pistas (si la playlist tiene un límite).
-   `sort_field` (TEXT, NULLABLE): Campo por el cual ordenar los resultados (ej. "bpm", "date_added_to_library").
-   `sort_order` (TEXT, DEFAULT "ASC"): Orden ("ASC" o "DESC").

### 3. `rules`

Almacena la expresión de la regla para cada playlist inteligente. Se opta por una única expresión de texto por playlist, aprovechando la capacidad del parser existente.

-   `rule_id` (INTEGER, PK, Autoincrement): Identificador único de la regla.
-   `playlist_id` (INTEGER, FK, REFERENCES `smart_playlists`(`playlist_id`) ON DELETE CASCADE, NOT NULL): Playlist a la que pertenece esta regla.
-   `expression_text` (TEXT, NOT NULL): La expresión de la regla completa en formato textual (ej. "(genre = 'House' OR genre = 'Techno') AND bpm > 120").
-   `is_active` (BOOLEAN, DEFAULT TRUE): Permite desactivar una expresión sin borrarla (útil para historial o pruebas).
-   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Fecha de creación de la expresión.

### 4. `playlist_tracks`

Tabla de unión que almacena las pistas que actualmente pertenecen a una playlist inteligente (resultado de la evaluación de sus reglas). Esta tabla se considera un caché y se regenera.

-   `playlist_track_id` (INTEGER, PK, Autoincrement): Identificador único de la entrada.
-   `playlist_id` (INTEGER, FK, REFERENCES `smart_playlists`(`playlist_id`) ON DELETE CASCADE, NOT NULL): Playlist a la que pertenece la pista.
-   `track_id` (INTEGER, FK, REFERENCES `tracks`(`track_id`) ON DELETE CASCADE, NOT NULL): Pista incluida en la playlist.
-   `added_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Fecha en que la pista fue añadida a esta generación de la playlist.
-   `rank_in_playlist` (INTEGER, NULLABLE): Posición de la pista si se aplica un orden específico post-evaluación.
-   UNIQUE (`playlist_id`, `track_id`)

### 5. `templates`

Almacena plantillas de reglas predefinidas que los usuarios pueden utilizar.

-   `template_id` (INTEGER, PK, Autoincrement): Identificador único de la plantilla.
-   `name` (TEXT, NOT NULL, UNIQUE): Nombre de la plantilla.
-   `description` (TEXT): Descripción de lo que hace la plantilla.
-   `rule_expression_text` (TEXT, NOT NULL): La expresión de la regla de la plantilla.
-   `category` (TEXT): Categoría de la plantilla (ej. "Género", "BPM", "Energía", "DJ Sets").
-   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Fecha de creación.
-   `is_system_template` (BOOLEAN, DEFAULT FALSE): Indica si es una plantilla del sistema (no editable/borrable por el usuario).

### 6. `triggers`

Define los disparadores para la actualización automática de playlists inteligentes.

-   `trigger_id` (INTEGER, PK, Autoincrement): Identificador único del trigger.
-   `playlist_id` (INTEGER, FK, REFERENCES `smart_playlists`(`playlist_id`) ON DELETE CASCADE, NULLABLE): Playlist específica a actualizar. Si es NULL, podría ser un trigger global (ej. "actualizar todas las playlists habilitadas").
-   `name` (TEXT, NOT NULL): Nombre descriptivo del trigger.
-   `trigger_type` (TEXT, NOT NULL): Tipo de trigger (ej. "SCHEDULED", "FILE_SYSTEM_EVENT", "METADATA_CHANGE").
-   `config_json` (TEXT, NOT NULL): Configuración específica del trigger en formato JSON.
    -   Para "SCHEDULED": `{"cron_expression": "0 0 * * *"}`
    -   Para "FILE_SYSTEM_EVENT": `{"event_type": "FILE_ADDED", "path_to_watch": "/music/new"}`
    -   Para "METADATA_CHANGE": `{"target_fields": ["genre", "bpm"]}` (aplicaría a cualquier track modificado en esos campos).
-   `is_enabled` (BOOLEAN, DEFAULT TRUE): Si el trigger está activo.
-   `last_fired_at` (TIMESTAMP, NULLABLE): Última vez que el trigger se disparó.
-   `last_successful_run_at` (TIMESTAMP, NULLABLE): Última vez que el trigger se ejecutó y completó la acción asociada con éxito.
-   `last_error_at` (TIMESTAMP, NULLABLE): Última vez que el trigger falló.
-   `last_error_message` (TEXT, NULLABLE): Mensaje del último error.
-   `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Fecha de creación.

### 7. `app_config`

Almacena configuraciones generales de la aplicación.

-   `config_key` (TEXT, PK, NOT NULL): Clave única de configuración (ej. "library_scan_path", "lastfm_api_key").
-   `config_value` (TEXT): Valor de la configuración.
-   `description` (TEXT): Descripción de la clave de configuración.
-   `data_type` (TEXT, DEFAULT "TEXT"): Tipo de dato del valor (ej. "TEXT", "INTEGER", "BOOLEAN", "JSON") para ayudar en la deserialización/validación.
-   `is_user_configurable` (BOOLEAN, DEFAULT TRUE): Si el usuario puede modificar este valor a través de la UI.
-   `updated_at` (TIMESTAMP): Fecha de la última actualización.

## Relaciones Principales (Resumen)

-   **`smart_playlists` 1--N `rules`**: Una playlist tiene una regla activa (expresión).
-   **`smart_playlists` M--N `tracks` (via `playlist_tracks`)**: Las pistas resultantes de una playlist.
-   **`triggers` N--1 `smart_playlists` (opcional)**: Un trigger puede estar asociado a una playlist o ser global.

Este esquema busca ser completo y cubrir los requisitos de la tarea de consolidación de persistencia y los aspectos del MVP. 