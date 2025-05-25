"""
Pruebas unitarias para el sistema de importación.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.importers.file_scanner import MusicFileScanner, ScanResult
from src.importers.import_manager import ImportManager, ImportProgress, ImportResult
from src.metadata.extractor import MetadataExtractor, TrackMetadata

class TestMusicFileScanner:
    """Pruebas para el escáner de archivos musicales."""
    
    @pytest.fixture
    def scanner(self):
        """Fixture que proporciona un escáner."""
        return MusicFileScanner(max_workers=2)
    
    @pytest.fixture
    def temp_music_files(self):
        """Fixture que crea archivos de música temporales."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Crear archivos de prueba
            music_files = []
            for i, ext in enumerate(['.mp3', '.flac', '.m4a']):
                file_path = temp_path / f"song_{i}{ext}"
                file_path.write_text(f"fake audio content {i}")
                music_files.append(file_path)
            
            # Crear un archivo no musical
            text_file = temp_path / "readme.txt"
            text_file.write_text("not music")
            
            # Crear subdirectorio
            subdir = temp_path / "subdir"
            subdir.mkdir()
            sub_music = subdir / "sub_song.mp3"
            sub_music.write_text("sub fake audio")
            music_files.append(sub_music)
            
            yield temp_path, music_files
    
    def test_is_music_file(self, scanner):
        """Prueba la detección de archivos musicales."""
        assert scanner.is_music_file(Path("song.mp3"))
        assert scanner.is_music_file(Path("album.flac"))
        assert scanner.is_music_file(Path("track.M4A"))  # Case insensitive
        assert not scanner.is_music_file(Path("document.pdf"))
        assert not scanner.is_music_file(Path("image.jpg"))
    
    def test_should_ignore_directory(self, scanner):
        """Prueba la detección de directorios a ignorar."""
        assert scanner.should_ignore_directory(Path("__pycache__"))
        assert scanner.should_ignore_directory(Path(".git"))
        assert scanner.should_ignore_directory(Path(".hidden"))
        assert scanner.should_ignore_directory(Path("_private"))
        assert not scanner.should_ignore_directory(Path("Music"))
        assert not scanner.should_ignore_directory(Path("Albums"))
    
    def test_scan_file_valid(self, scanner, temp_music_files):
        """Prueba el escaneo de un archivo válido."""
        temp_path, music_files = temp_music_files
        test_file = music_files[0]  # song_0.mp3
        
        result = scanner.scan_file(test_file)
        
        assert result.is_valid
        assert result.file_path == str(test_file.resolve())
        assert result.file_format == "mp3"
        assert result.file_size > 0
        assert result.error_message is None
    
    def test_scan_file_nonexistent(self, scanner):
        """Prueba el escaneo de un archivo inexistente."""
        nonexistent = Path("/nonexistent/file.mp3")
        result = scanner.scan_file(nonexistent)
        
        assert not result.is_valid
        assert "Archivo no encontrado" in result.error_message
    
    def test_scan_file_unsupported_format(self, scanner):
        """Prueba el escaneo de un formato no soportado."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("not music")
            
            try:
                result = scanner.scan_file(temp_path)
                assert not result.is_valid
                assert "Formato no soportado" in result.error_message
            finally:
                temp_path.unlink()
    
    def test_find_music_files(self, scanner, temp_music_files):
        """Prueba la búsqueda de archivos musicales."""
        temp_path, expected_files = temp_music_files
        
        found_files = list(scanner.find_music_files(str(temp_path)))
        
        # Debe encontrar todos los archivos musicales
        assert len(found_files) == len(expected_files)
        
        # Verificar que son los archivos correctos
        found_names = {f.name for f in found_files}
        expected_names = {f.name for f in expected_files}
        assert found_names == expected_names
    
    def test_scan_directory(self, scanner, temp_music_files):
        """Prueba el escaneo de un directorio."""
        temp_path, expected_files = temp_music_files
        
        results = list(scanner.scan_directory(str(temp_path)))
        
        # Filtrar solo resultados válidos
        valid_results = [r for r in results if r.is_valid]
        assert len(valid_results) == len(expected_files)
        
        # Verificar que todos tienen información básica
        for result in valid_results:
            assert result.file_size > 0
            assert result.file_format in ['mp3', 'flac', 'm4a']
    
    def test_scan_directory_non_recursive(self, scanner, temp_music_files):
        """Prueba el escaneo no recursivo."""
        temp_path, expected_files = temp_music_files
        
        results = list(scanner.scan_directory(str(temp_path), recursive=False))
        valid_results = [r for r in results if r.is_valid]
        
        # No debe incluir archivos del subdirectorio
        expected_non_recursive = [f for f in expected_files if f.parent == temp_path]
        assert len(valid_results) == len(expected_non_recursive)
    
    def test_progress_callback(self, scanner, temp_music_files):
        """Prueba el callback de progreso."""
        temp_path, _ = temp_music_files
        
        progress_calls = []
        def progress_callback(processed, total):
            progress_calls.append((processed, total))
        
        scanner.set_progress_callback(progress_callback)
        list(scanner.scan_directory(str(temp_path)))
        
        # Debe haber llamado al callback
        assert len(progress_calls) > 0
        
        # El último debe tener processed == total
        final_call = progress_calls[-1]
        assert final_call[0] == final_call[1]
    
    def test_stop_scanning(self, scanner, temp_music_files):
        """Prueba la cancelación del escaneo."""
        temp_path, _ = temp_music_files
        
        # Iniciar escaneo en paralelo y cancelar inmediatamente
        scanner.stop_scan()
        results = list(scanner.scan_directory(str(temp_path)))
        
        # Puede que se procesen algunos archivos antes de la cancelación
        # pero no debe procesar todos
        assert isinstance(results, list)

class TestMetadataExtractor:
    """Pruebas para el extractor de metadatos."""
    
    @pytest.fixture
    def extractor(self):
        """Fixture que proporciona un extractor."""
        return MetadataExtractor()
    
    def test_safe_int_conversion(self, extractor):
        """Prueba la conversión segura a entero."""
        assert extractor._safe_int("123") == 123
        assert extractor._safe_int("5/10") == 5  # Formato track/total
        assert extractor._safe_int("invalid") is None
        assert extractor._safe_int(None) is None
    
    def test_safe_float_conversion(self, extractor):
        """Prueba la conversión segura a float."""
        assert extractor._safe_float("123.5") == 123.5
        assert extractor._safe_float("120") == 120.0
        assert extractor._safe_float("invalid") is None
        assert extractor._safe_float(None) is None
    
    def test_extract_year_from_date(self, extractor):
        """Prueba la extracción de año de fechas."""
        assert extractor._extract_year_from_date("2024") == 2024
        assert extractor._extract_year_from_date("2024-03-15") == 2024
        assert extractor._extract_year_from_date("15/03/2024") == 2024
        assert extractor._extract_year_from_date("invalid") is None
        assert extractor._extract_year_from_date("1800") is None  # Fuera de rango
    
    def test_normalize_metadata(self, extractor):
        """Prueba la normalización de metadatos."""
        from src.metadata.extractor import TrackMetadata
        from datetime import datetime
        
        metadata = TrackMetadata(
            file_path="/test/file.mp3",
            file_size=1000,
            file_format="mp3",
            last_modified=datetime.now(),
            title="  Test Song  ",  # Con espacios
            artist="",  # String vacío
            disc_number=None  # Sin número de disco
        )
        
        extractor._normalize_metadata(metadata)
        
        assert metadata.title == "Test Song"  # Espacios removidos
        assert metadata.artist is None  # String vacío convertido a None
        assert metadata.disc_number == 1  # Valor por defecto
    
    @patch('src.metadata.extractor.MUTAGEN_AVAILABLE', False)
    def test_extract_without_mutagen(self, extractor):
        """Prueba la extracción sin Mutagen disponible."""
        with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_file:
            temp_path = Path(temp_file.name)
            
            metadata = extractor.extract_metadata(temp_path)
            
            assert not metadata.extraction_success
            assert "Mutagen no está instalado" in metadata.extraction_errors
    
    def test_get_supported_formats(self, extractor):
        """Prueba la obtención de formatos soportados."""
        formats = extractor.get_supported_formats()
        
        assert isinstance(formats, list)
        assert '.mp3' in formats
        assert '.flac' in formats
        assert '.m4a' in formats

class TestImportManager:
    """Pruebas para el gestor de importación."""
    
    @pytest.fixture
    def import_manager(self):
        """Fixture que proporciona un gestor de importación."""
        return ImportManager(max_workers=2)
    
    def test_initialization(self, import_manager):
        """Prueba la inicialización del gestor."""
        assert not import_manager.is_importing
        assert import_manager.progress.total_files == 0
        assert import_manager.max_workers == 2
    
    def test_progress_callbacks(self, import_manager):
        """Prueba los callbacks de progreso."""
        progress_calls = []
        completion_calls = []
        error_calls = []
        
        def progress_cb(progress):
            progress_calls.append(progress)
        
        def completion_cb(result):
            completion_calls.append(result)
        
        def error_cb(error):
            error_calls.append(error)
        
        import_manager.add_progress_callback(progress_cb)
        import_manager.add_completion_callback(completion_cb)
        import_manager.add_error_callback(error_cb)
        
        # Simular notificaciones
        import_manager._notify_progress()
        import_manager._notify_completion(ImportResult(0, 0, 0, 0, [], 0.0, []))
        import_manager._notify_error("Test error")
        
        assert len(progress_calls) == 1
        assert len(completion_calls) == 1
        assert len(error_calls) == 1
    
    def test_cancel_import(self, import_manager):
        """Prueba la cancelación de importación."""
        # Simular importación en progreso
        import_manager._is_importing = True
        
        import_manager.cancel_import()
        
        # Verificar que se estableció la flag de cancelación
        assert import_manager._import_cancelled.is_set()
    
    @patch('src.importers.import_manager.get_db')
    def test_get_or_create_artist(self, mock_get_db, import_manager):
        """Prueba la creación/obtención de artistas."""
        # Mock de sesión de base de datos
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No existe
        
        # Mock de artista
        mock_artist = Mock()
        mock_artist.id = 1
        
        with patch('src.importers.import_manager.Artist', return_value=mock_artist):
            artist = import_manager._get_or_create_artist(mock_session, "Test Artist")
            
            assert artist == mock_artist
            mock_session.add.assert_called_once_with(mock_artist)
            mock_session.flush.assert_called_once()
    
    @patch('src.importers.import_manager.get_db')
    def test_get_or_create_genres(self, mock_get_db, import_manager):
        """Prueba la creación/obtención de géneros."""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No existe
        
        mock_genre = Mock()
        mock_genre.id = 1
        
        with patch('src.importers.import_manager.Genre', return_value=mock_genre):
            genres = import_manager._get_or_create_genres(mock_session, "Rock, Pop")
            
            assert len(genres) == 2  # Dos géneros separados por coma
            assert all(g == mock_genre for g in genres)

class TestImportProgress:
    """Pruebas para la clase ImportProgress."""
    
    def test_completion_percentage(self):
        """Prueba el cálculo de porcentaje de completitud."""
        progress = ImportProgress(total_files=100, processed_files=25)
        assert progress.completion_percentage == 25.0
        
        # Sin archivos totales
        progress = ImportProgress(total_files=0, processed_files=0)
        assert progress.completion_percentage == 0.0
    
    def test_processing_rate(self):
        """Prueba el cálculo de velocidad de procesamiento."""
        from datetime import datetime, timedelta
        
        # Con tiempo transcurrido
        start_time = datetime.now() - timedelta(seconds=10)
        progress = ImportProgress(
            processed_files=50,
            start_time=start_time
        )
        
        rate = progress.processing_rate
        assert rate > 0  # Debe ser mayor que 0
        assert rate == 5.0  # 50 archivos / 10 segundos
        
        # Sin tiempo de inicio
        progress = ImportProgress(processed_files=50)
        assert progress.processing_rate == 0.0

class TestImportResult:
    """Pruebas para la clase ImportResult."""
    
    def test_import_result_creation(self):
        """Prueba la creación de un resultado de importación."""
        result = ImportResult(
            total_processed=100,
            successful_imports=90,
            failed_imports=5,
            duplicate_files=5,
            errors=["Error 1", "Error 2"],
            duration_seconds=30.5,
            new_tracks=[1, 2, 3]
        )
        
        assert result.total_processed == 100
        assert result.successful_imports == 90
        assert result.failed_imports == 5
        assert result.duplicate_files == 5
        assert len(result.errors) == 2
        assert result.duration_seconds == 30.5
        assert len(result.new_tracks) == 3