import os
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from .database.music_database import MusicDatabase, Track

logger = logging.getLogger(__name__)

class FolderOrganizer:
    """
    Organiza archivos musicales en una estructura de carpetas basada en metadatos.
    """

    def __init__(self, db_manager: MusicDatabase, base_output_dir: str = "OrganizedMusic"):
        """
        Inicializa el organizador de carpetas.

        Args:
            db_manager (MusicDatabase): Instancia del gestor de la base de datos.
            base_output_dir (str): Directorio base donde se creará la estructura organizada.
        """
        self.db_manager = db_manager
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio base de organización: '{self.base_output_dir}'")

        # Definiciones de rangos (ejemplos, pueden ser configurables)
        self.bpm_ranges = {
            "Slow": (0, 90),
            "MidTempo": (91, 120),
            "Fast": (121, 140),
            "VeryFast": (141, 200)
        }
        self.energy_levels = {
            "LowEnergy": (0.0, 0.33),
            "MediumEnergy": (0.34, 0.66),
            "HighEnergy": (0.67, 1.0)
        }

    def _get_decade(self, year: Optional[int]) -> str:
        """Determina la década a partir de un año."""
        if year is None or not (1900 <= year <= 2100): # Rango razonable
            return "UnknownDecade"
        decade_start = (year // 10) * 10
        return f"{decade_start}s"

    def _get_bpm_range_label(self, bpm: Optional[float]) -> str:
        """Determina la etiqueta del rango de BPM."""
        if bpm is None:
            return "UnknownBPM"
        for label, (min_bpm, max_bpm) in self.bpm_ranges.items():
            if min_bpm <= bpm <= max_bpm:
                return label
        return "UnknownBPM"

    def _get_energy_level_label(self, energy: Optional[float]) -> str:
        """Determina la etiqueta del nivel de energía."""
        if energy is None:
            return "UnknownEnergy"
        for label, (min_energy, max_energy) in self.energy_levels.items():
            if min_energy <= energy <= max_energy:
                return label
        return "UnknownEnergy"

    def _sanitize_name(self, name: str) -> str:
        """Sanea un nombre para usarlo en rutas de archivo."""
        import re
        # Reemplazar caracteres no permitidos con guiones bajos
        sane_name = re.sub(r'[^\w\s.-]', '', name).strip()
        # Reemplazar espacios con guiones bajos
        sane_name = re.sub(r'\s+', '_', sane_name)
        return sane_name

    def get_target_folder_path(self, track: Track) -> Path:
        """
        Genera la ruta completa de la carpeta destino para un track.
        Formato: BaseDir/Genre/Artist/Year o BaseDir/Genre/Artist
        """
        genre = self._sanitize_name(track.genre.split(';')[0] if track.genre else "UnknownGenre")
        artist = self._sanitize_name(track.artist if track.artist else "UnknownArtist")
        
        # Construir la ruta base
        target_folder = self.base_output_dir / genre / artist
        
        # Añadir el año si está disponible
        if track.year:
            target_folder = target_folder / str(track.year)
            
        return target_folder

    def organize_track_file(self, track: Track, dry_run: bool = False) -> Dict[str, Any]:
        """
        Mueve y renombra un archivo de track a su ubicación organizada.

        Args:
            track (Track): Objeto Track con metadatos completos.
            dry_run (bool): Si es True, solo simula la operación sin mover archivos.

        Returns:
            Dict[str, Any]: Resultado de la operación (éxito, ruta antigua, ruta nueva, error).
        """
        if not track.filepath or not os.path.exists(track.filepath):
            return {"success": False, "error": f"Archivo no encontrado o ruta inválida: {track.filepath}"}

        original_filepath = Path(track.filepath)
        target_folder = self.get_target_folder_path(track)

        # Generar el nuevo nombre de archivo
        title_sane = self._sanitize_name(track.title if track.title else "UnknownTitle")
        
        new_filename = f"{title_sane}{original_filepath.suffix}"
        new_filepath = target_folder / new_filename

        logger.info(f"Original: {original_filepath}")
        logger.info(f"Destino: {new_filepath}")

        if dry_run:
            logger.info(f"DRY RUN: Se crearía la carpeta '{target_folder}' y se movería '{original_filepath.name}' a '{new_filepath.name}'")
            return {
                "success": True,
                "dry_run": True,
                "original_path": str(original_filepath),
                "new_path": str(new_filepath),
                "action": "simulated_move"
            }

        try:
            # Crear la carpeta destino si no existe
            target_folder.mkdir(parents=True, exist_ok=True)

            # Si el archivo destino ya existe, añadir un sufijo numérico
            count = 1
            while new_filepath.exists():
                name_parts = new_filename.rsplit('.', 1)
                if len(name_parts) > 1:
                    new_filename = f"{name_parts[0]}_{count}.{name_parts[1]}"
                else:
                    new_filename = f"{new_filename}_{count}"
                new_filepath = target_folder / new_filename
                count += 1

            # Mover y renombrar el archivo
            shutil.move(str(original_filepath), str(new_filepath))
            logger.info(f"Archivo movido y renombrado: '{original_filepath}' -> '{new_filepath}'")

            # Actualizar la ruta del archivo en la base de datos
            self.db_manager.execute_query(
                "UPDATE tracks SET filepath = ? WHERE id = ?",
                (str(new_filepath), track.id)
            )
            logger.info(f"Ruta del track ID {track.id} actualizada en la DB.")

            return {
                "success": True,
                "original_path": str(original_filepath),
                "new_path": str(new_filepath),
                "action": "moved_and_renamed"
            }
        except OSError as e:
            logger.error(f"Error al mover/renombrar '{original_filepath}': {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error inesperado al organizar '{original_filepath}': {e}")
            return {"success": False, "error": str(e)}

    def organize_all_tracks(self, genre_filter: str = None, limit: int = 100, 
                           dry_run: bool = True) -> Dict[str, Any]:
        """
        Organiza todos los tracks en la base de datos.
        
        Args:
            genre_filter: Filtro opcional de género
            limit: Límite de tracks a procesar
            dry_run: Si es True, no mueve físicamente los archivos
            
        Returns:
            Resultados de la organización
        """
        try:
            # Consultar tracks
            query = "SELECT * FROM tracks WHERE 1=1"
            params = []
            
            if genre_filter:
                query += " AND genre LIKE ?"
                params.append(f"%{genre_filter}%")
                
            query += " LIMIT ?"
            params.append(limit)
            
            rows = self.db_manager.fetch_query(query, tuple(params))
            
            results = {
                "total": len(rows),
                "organized": 0,
                "errors": 0,
                "skipped": 0,
                "details": []
            }
            
            # Procesar cada track
            for row in rows:
                track = Track.from_row(row)
                org_result = self.organize_track_file(track, dry_run)
                
                if org_result["success"]:
                    if org_result.get("already_organized"):
                        results["skipped"] += 1
                    else:
                        results["organized"] += 1
                else:
                    results["errors"] += 1
                    
                results["details"].append({
                    "track_id": track.id,
                    "filepath": track.filepath,
                    **org_result
                })
            
            logger.info(f"Organización completa: {results['organized']} archivos organizados, "
                      f"{results['skipped']} omitidos, {results['errors']} errores")
            
            return {
                "success": True,
                **results
            }
            
        except Exception as e:
            logger.error(f"Error en organize_all_tracks: {e}")
            return {
                "success": False,
                "error": str(e)
            }


