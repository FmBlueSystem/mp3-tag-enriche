"""MP3 file handling and tag management module."""
from typing import Dict, List, Optional
from pathlib import Path
import shutil
import os
from datetime import datetime
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TCON
from mutagen.mp3 import MP3
import re

class Mp3FileHandler:
    """Handles MP3 file operations and tag management."""
    
    def __init__(self, backup_dir: Optional[str] = None):
        """Initialize the file handler.
        
        Args:
            backup_dir: Directory for file backups (optional)
        """
        # Si no se proporciona un directorio de respaldo, usar la ubicación predeterminada
        if backup_dir is None:
            # Usar la ruta específica solicitada por el usuario
            backup_dir = "/Volumes/My Passport/Dj compilation 2025/Respados mp3"
            
        self.backup_dir = Path(backup_dir) if backup_dir else None
        if self.backup_dir and not self.backup_dir.exists():
            try:
                self.backup_dir.mkdir(parents=True)
                print(f"Directorio de respaldo creado en: {self.backup_dir}")
            except Exception as e:
                print(f"Error al crear directorio de respaldo: {e}")
                # Intentar crear en una ubicación alternativa en caso de problemas de permisos
                fallback_dir = Path("mp3_backups")
                if not fallback_dir.exists():
                    fallback_dir.mkdir(parents=True)
                self.backup_dir = fallback_dir
                print(f"Usando directorio de respaldo alternativo: {self.backup_dir}")
            
    def _create_backup(self, file_path: str) -> bool:
        """Create a backup of the file before modification.
        
        Args:
            file_path: Path to the MP3 file
            
        Returns:
            True if backup was successful, False otherwise
        """
        if not self.backup_dir:
            return False
            
        try:
            src_path = Path(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{src_path.stem}_{timestamp}{src_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            return True
            
        except Exception as e:
            print(f"Backup error for {file_path}: {e}")
            return False
            
    def read_tags(self, file_path: str) -> Dict[str, List[str]]:
        """Read metadata tags from an MP3 file.
        
        Args:
            file_path: Path to the MP3 file
            
        Returns:
            Dictionary of tag names to values
        """
        print(f"Reading tags from: {file_path}")
        try:
            if not os.path.exists(file_path):
                print(f"File does not exist: {file_path}")
                return {}
                
            audio = EasyID3(file_path)
            tags = {}
            for key in audio.keys():
                tags[key] = audio.get(key, [])
            print(f"Found tags: {tags}")
            return tags
            
        except Exception as e:
            print(f"Error reading tags from {file_path}: {e}")
            return {}
            
    def write_genre(self, file_path: str, genres: List[str], backup: bool = True) -> bool:
        """Write genre tags to an MP3 file.
        
        Args:
            file_path: Path to the MP3 file
            genres: List of genres to write
            backup: Whether to create a backup before writing
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Writing genres to {file_path}: {genres}")
        
        # Verificar permisos de escritura
        if not os.access(os.path.dirname(file_path), os.W_OK):
            print(f"No hay permisos de escritura en el directorio: {os.path.dirname(file_path)}")
            return False
            
        # Crear backup si se solicita
        if backup:
            self._create_backup(file_path)
        
        # Verificar que el archivo sea accesible antes de intentar modificarlo
        try:
            with open(file_path, 'rb+') as f:
                # Verificar que el archivo se pueda abrir en modo lectura/escritura
                pass
        except Exception as access_error:
            print(f"No se puede acceder al archivo para escritura: {access_error}")
            return False
            
        # Ahora intentamos realizar la escritura
        try:
            # Intentar con EasyID3 primero
            try:
                audio = EasyID3(file_path)
            except Exception as id3_error:
                print(f"Error al abrir EasyID3, intentando crear etiquetas: {id3_error}")
                # Si el archivo no tiene etiqueta ID3, agregar una
                try:
                    audio = MP3(file_path)
                    audio.add_tags()
                    audio.save()
                    audio = EasyID3(file_path)
                except Exception as create_tag_error:
                    print(f"Error al crear etiquetas ID3: {create_tag_error}")
                    return False
                
            # Actualizar géneros
            audio['genre'] = genres
            
            # Intentar guardar con manejo de excepciones mejorado
            try:
                audio.save()
                print(f"Géneros escritos exitosamente: {genres}")
                return True
            except IOError as io_error:
                print(f"Error de E/S al guardar etiquetas: {io_error}")
                return False
            except Exception as save_error:
                print(f"Error al guardar etiquetas: {save_error}")
                return False
            
        except Exception as e:
            print(f"Error escribiendo géneros en {file_path}: {e}")
            # Intentar con escritura directa ID3 como alternativa
            try:
                audio = ID3(file_path)
                audio.add(TCON(encoding=3, text=genres))
                audio.save()
                print("Géneros escritos exitosamente usando método alternativo")
                return True
            except Exception as e2:
                print(f"El método alternativo de escritura también falló: {e2}")
                
                # Último intento: crear una etiqueta nueva desde cero
                try:
                    audio = MP3(file_path)
                    if audio.tags is None:
                        audio.tags = ID3()
                    audio.tags.add(TCON(encoding=3, text=genres))
                    audio.save()
                    print("Géneros escritos exitosamente usando método de último recurso")
                    return True
                except Exception as e3:
                    print(f"Todos los métodos de escritura fallaron: {e3}")
                    return False
                
    def get_file_info(self, file_path: str) -> Dict[str, str]:
        """Get basic information about an MP3 file.
        
        Args:
            file_path: Path to the MP3 file
            
        Returns:
            Dictionary with file information
        """
        print(f"Getting file info for: {file_path}")
        try:
            if not os.path.exists(file_path):
                print(f"File does not exist: {file_path}")
                return {}
                
            audio = MP3(file_path)
            info = {
                'length': str(int(audio.info.length)),
                'bitrate': str(audio.info.bitrate // 1000) + ' kbps',
                'sample_rate': str(audio.info.sample_rate) + ' Hz',
                'mode': audio.info.mode
            }
            
            # Try to get basic tags
            try:
                id3 = EasyID3(file_path)
                info.update({
                    'title': id3.get('title', [''])[0],
                    'artist': id3.get('artist', [''])[0],
                    'album': id3.get('album', [''])[0],
                    'current_genre': ', '.join(id3.get('genre', []))
                })
                print(f"Found file info: {info}")
            except Exception as e:
                print(f"Error reading ID3 tags: {e}")
                
            return info
            
        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return {}
            
    def rename_file_by_genre(self, file_path: str, include_genre: bool = True) -> Dict[str, str]:
        """Renombra el archivo basado en sus etiquetas y géneros.
        
        Args:
            file_path: Ruta al archivo MP3
            include_genre: Indica si se debe incluir el género en el nombre del archivo
            
        Returns:
            Diccionario con información del renombramiento o error
        """
        print(f"Intentando renombrar archivo: {file_path}")
        result = {"success": False, "original_path": file_path}
        
        try:
            # Verificar que el archivo exista y sea accesible
            if not os.path.exists(file_path):
                result["error"] = "El archivo no existe"
                return result
                
            # Obtener información actual del archivo
            info = self.get_file_info(file_path)
            if not info:
                result["error"] = "No se pudo obtener información del archivo"
                return result
                
            # Construir nuevo nombre basado en artista, título y género
            artist = info.get('artist', '').strip()
            title = info.get('title', '').strip()
            genre = info.get('current_genre', '').strip()
            
            if not artist or not title:
                result["error"] = "Faltan metadatos esenciales (artista o título)"
                return result
                
            # Crear el nuevo nombre base del archivo
            if include_genre and genre:
                new_basename = f"{artist} - {title} [{genre}]"
            else:
                new_basename = f"{artist} - {title}"
                
            # Limpiar caracteres no válidos para nombres de archivo
            new_basename = re.sub(r'[\\/*?:"<>|]', '_', new_basename)
            
            # Obtener la extensión original
            file_obj = Path(file_path)
            extension = file_obj.suffix.lower()
            
            # Construir la nueva ruta completa
            new_path = os.path.join(os.path.dirname(file_path), new_basename + extension)
            result["new_path"] = new_path
            
            # Si el archivo ya tiene ese nombre, no hacer nada
            if file_path == new_path:
                result["success"] = True
                result["message"] = "El archivo ya tiene el nombre correcto"
                return result
                
            # Verificar si ya existe un archivo con el nuevo nombre
            if os.path.exists(new_path):
                # Crear un nombre único añadiendo un timestamp
                timestamp = datetime.now().strftime("%H%M%S")
                new_basename = f"{new_basename}_{timestamp}"
                new_path = os.path.join(os.path.dirname(file_path), new_basename + extension)
                result["new_path"] = new_path
            
            # Crear backup opcional antes de renombrar
            if self.backup_dir:
                self._create_backup(file_path)
                
            # Renombrar el archivo
            os.rename(file_path, new_path)
            
            result["success"] = True
            result["message"] = f"Archivo renombrado a: {os.path.basename(new_path)}"
            return result
            
        except Exception as e:
            result["error"] = f"Error al renombrar archivo: {str(e)}"
            return result
            
    def is_valid_mp3(self, file_path: str) -> bool:
        """Check if the file is a valid MP3.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid MP3, False otherwise
        """
        print(f"Checking if valid MP3: {file_path}")
        
        # Primero verificamos si podemos acceder al archivo
        exists = False
        try:
            # Intentar tres métodos de verificación diferentes
            try:
                # 1. Método Path
                path_obj = Path(file_path)
                if path_obj.exists():
                    exists = True
            except:
                pass
                
            if not exists:
                # 2. Método os.path
                try:
                    if os.path.exists(file_path):
                        exists = True
                except:
                    pass
                    
            if not exists:
                # 3. Intento directo de apertura
                try:
                    with open(file_path, 'rb') as f:
                        f.read(10)  # Intentar leer algunos bytes
                        exists = True
                except:
                    pass
                    
            if not exists:
                print(f"No se puede acceder al archivo: {file_path}")
                return False
                
            # Si llegamos hasta aquí, el archivo existe y es accesible
            # Ahora verificamos si es un MP3 válido
            try:
                audio = MP3(file_path)
                print(f"El archivo {file_path} es un MP3 válido")
                return True
            except Exception as e:
                print(f"El archivo existe pero no es un MP3 válido: {e}")
                return False
                
        except Exception as e:
            print(f"Error al verificar archivo MP3: {e}")
            return False
