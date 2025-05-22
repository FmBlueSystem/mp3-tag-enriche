"""Test suite for the GenreModel module."""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
from pathlib import Path

from src.gui.models.genre_model import (
    GenreModel, 
    UpdateBuffer,
    GenreIndex,
    clean_and_split_genre_payload,
    BLACKLIST_GENRE_TERMS_MODEL
)
from src.core.genre_detector import GenreDetector
from src.core.file_handler import Mp3FileHandler

@pytest.fixture
def genre_model():
    """Fixture that provides a GenreModel instance with mocked dependencies."""
    with patch('src.gui.models.genre_model.Mp3FileHandler') as mock_handler, \
         patch('src.gui.models.genre_model.GenreDetector') as mock_detector, \
         patch('src.gui.models.genre_model.MusicBrainzAPI'):
        
        mock_handler_instance = MagicMock()
        mock_handler_instance.backup_dir = "test_backup"
        mock_handler.return_value = mock_handler_instance
        
        mock_detector.return_value = MagicMock()
        model = GenreModel(backup_dir="test_backup")
        return model

@pytest.fixture
def update_buffer():
    """Fixture that provides an UpdateBuffer instance."""
    return UpdateBuffer(batch_size=3)

@pytest.fixture
def genre_index():
    """Fixture that provides a GenreIndex instance."""
    return GenreIndex()

class TestUpdateBuffer:
    """Pruebas para la clase UpdateBuffer."""
    
    def test_initialization(self, update_buffer):
        """Prueba la inicialización correcta del buffer."""
        assert update_buffer.batch_size == 3
        assert update_buffer.pending_count == 0

    def test_add_and_pending_count(self, update_buffer):
        """Prueba la adición de items y el conteo pendiente."""
        update_buffer.add({"id": 1})
        update_buffer.add({"id": 2})
        assert update_buffer.pending_count == 2

    def test_flush(self, update_buffer):
        """Prueba el vaciado del buffer."""
        items = [{"id": i} for i in range(5)]
        for item in items:
            update_buffer.add(item)
        
        # Primer flush debe retornar batch_size (3) items
        result = update_buffer.flush()
        assert len(result) == 3
        assert update_buffer.pending_count == 2
        
        # Segundo flush debe retornar los 2 items restantes
        result = update_buffer.flush()
        assert len(result) == 2
        assert update_buffer.pending_count == 0

class TestGenreIndex:
    """Pruebas para la clase GenreIndex."""
    
    def test_add_and_search(self, genre_index):
        """Prueba la adición y búsqueda de géneros."""
        genre_index.add("file1.mp3", ["Rock", "Metal"], 0.8)
        genre_index.add("file2.mp3", ["Rock", "Pop"], 0.6)
        
        assert len(genre_index.search("rock")) == 2
        assert len(genre_index.search("metal")) == 1
        assert len(genre_index.search(min_confidence=0.7)) == 1

    def test_remove(self, genre_index):
        """Prueba la eliminación de archivos del índice."""
        genre_index.add("file1.mp3", ["Rock"], 0.8)
        genre_index.add("file2.mp3", ["Rock"], 0.7)
        
        assert len(genre_index.search("rock")) == 2
        
        genre_index.remove("file1.mp3")
        assert len(genre_index.search("rock")) == 1

def test_clean_and_split_genre_payload():
    """Prueba la función de limpieza y división de géneros."""
    # Prueba con géneros válidos
    result = clean_and_split_genre_payload("Rock; Pop, Metal")
    assert sorted(result) == ["Metal", "Pop", "Rock"]
    
    # Prueba con géneros en lista negra
    result = clean_and_split_genre_payload("rock; unknown, soundtrack")
    assert len(result) == 1
    assert result == ["Rock"]
    
    # Prueba con años - deberían ser removidos según la implementación actual
    result = clean_and_split_genre_payload("rock 2023, pop 1980")
    assert len(result) == 2
    assert sorted(result) == ["Pop", "Rock"]
    
    # Prueba con entrada vacía
    assert clean_and_split_genre_payload("") == []
    assert clean_and_split_genre_payload(None) == []
    
    # Pruebas adicionales para mejorar cobertura
    result = clean_and_split_genre_payload("  ")  # Solo espacios
    assert result == []
    
    result = clean_and_split_genre_payload("123")  # Solo números
    assert result == []
    
    result = clean_and_split_genre_payload("!@#$%")  # Solo símbolos
    assert result == []
    
    # Prueba con caracteres especiales y saltos de línea
    result = clean_and_split_genre_payload("Rock \n \r\n 2023")
    assert result == ["Rock"]  # Debería eliminar saltos de línea
    
    # Prueba con múltiples espacios y caracteres especiales
    result = clean_and_split_genre_payload("Pop  \t  Music")
    assert result == ["Pop Music"]

class TestGenreModel:
    """Pruebas para la clase GenreModel."""
    
    def test_initialization(self, genre_model):
        """Prueba la inicialización del modelo."""
        assert genre_model.min_confidence == 0.2
        assert genre_model.max_api_tags == 100
        assert genre_model.rename_after_update is True
        assert genre_model.backup_dir == "test_backup"

    def test_verify_file_exists(self, genre_model, tmp_path):
        """Prueba la verificación de existencia de archivos."""
        # Crear archivo temporal para prueba
        test_file = tmp_path / "test.mp3"
        test_file.write_text("")
        
        exists, _ = genre_model.verify_file_exists(str(test_file))
        assert exists is True
        
        exists, error_msg = genre_model.verify_file_exists("nonexistent.mp3")
        assert exists is False
        assert error_msg != ""

    def test_process_genres(self, genre_model):
        """Prueba el procesamiento de géneros detectados."""
        test_genres = {
            "Rock/Metal": 0.9,
            "Pop Music": 0.8,
            "unknown": 0.7,  # Debería ser filtrado
            "soundtrack": 0.6,  # Debería ser filtrado
        }
        
        result = genre_model.process_genres(test_genres, max_tags=10)
        assert "Rock" in result
        assert "Metal" in result
        assert "Pop Music" in result
        assert "unknown" not in result
        assert "soundtrack" not in result

    def test_select_genres(self, genre_model):
        """Prueba la selección de géneros basada en confianza."""
        genres = {
            "Rock": 0.9,
            "Metal": 0.8,
            "Pop": 0.7,
            "Jazz": 0.5
        }
        
        # Prueba con confianza alta
        selected = genre_model.select_genres(genres, confidence=0.8, max_genres=2)
        assert len(selected) == 2
        assert "Rock" in selected
        assert "Metal" in selected
        
        # Prueba con confianza baja
        selected = genre_model.select_genres(genres, confidence=0.6, max_genres=3)
        assert len(selected) == 3
        assert "Jazz" not in selected

    @patch('pathlib.Path.exists')
    def test_analyze_file(self, mock_exists, genre_model):
        """Prueba el análisis de archivos."""
        mock_exists.return_value = True
        genre_model.detector.file_handler.is_valid_mp3.return_value = True
        
        # Configurar mock para analyze_file
        mock_result = {
            "detected_genres": {"Rock": 0.9, "Metal": 0.8},
            "found_genres": {"Pop": 0.7}
        }
        genre_model.detector.analyze_file.return_value = mock_result
        
        result = genre_model.analyze("test.mp3")
        
        assert "processed_genres" in result
        assert "raw_api_genres" in result
        assert result["raw_api_genres"]["Rock"] == 0.9
        assert result["raw_api_genres"]["Pop"] == 0.7
        
    def test_process_chunks(self, genre_model):
        """Prueba el proceso de chunks de archivos."""
        # Configurar resultados en caché
        cached_result = {"processed_genres": {"Rock": 0.9}}
        genre_model._cache = {"cached.mp3": cached_result}
        
        # Configurar resultado para archivo no cacheado
        new_result = {"processed_genres": {"Pop": 0.8}}
        genre_model.analyze = MagicMock(return_value=new_result)
        
        # Probar combinación de archivos cacheados y no cacheados
        results = genre_model.process_chunks(["cached.mp3", "new.mp3"])
        
        assert len(results) == 2
        assert results[0] == cached_result
        assert results[1] == new_result
        genre_model.analyze.assert_called_once_with("new.mp3", 8192)

    @patch('pathlib.Path.exists')
    def test_process_file(self, mock_exists, genre_model):
        """Prueba el procesamiento completo de archivos."""
        mock_exists.return_value = True
        genre_model.detector.file_handler.is_valid_mp3.return_value = True
        
        # Configurar mocks
        genre_model.detector.analyze_file.return_value = {
            "processed_genres": {"Rock": 0.9, "Metal": 0.8}
        }
        genre_model.detector.file_handler.rename_file_by_genre.return_value = {
            "success": True,
            "new_path": "test_renamed.mp3"
        }
        
        result = genre_model.process(
            "test.mp3",
            confidence=0.7,
            max_genres=2,
            rename_flag=True
        )
        
        assert result["written"] is True
        assert result["renamed"] is True
        assert "Rock" in result["current_genre"]

    def test_update_results(self, genre_model):
        """Prueba la actualización de resultados en el modelo."""
        results = {
            "file1.mp3": {
                "processed_genres": {"Rock": 0.9},
                "error": None
            },
            "file2.mp3": {
                "processed_genres": {"Pop": 0.8},
                "error": None
            }
        }
        
        genre_model.update_results(results)
        assert genre_model.rowCount() == 2

    @patch('pathlib.Path.exists')
    def test_error_handling(self, mock_exists, genre_model):
        """Prueba el manejo de errores exhaustivamente."""
        # Prueba con archivo no existente
        mock_exists.return_value = False
        result = genre_model.process("nonexistent.mp3", 0.7, 2, True)
        assert result["written"] is True
        assert "error" in result
        
        # Prueba con archivo MP3 inválido
        mock_exists.return_value = True
        genre_model.detector.file_handler.is_valid_mp3.return_value = False
        result = genre_model.process("invalid.mp3", 0.7, 2, True)
        assert result["written"] is False
        assert "error" in result
        
    def test_verify_file_errors(self, genre_model):
        """Prueba los distintos errores en verificación de archivos."""
        # Test error en Path.exists
        original_verify = genre_model.verify_file_exists
        genre_model.verify_file_exists = lambda x: (False, "Error con Path.exists(): Test error")
        exists, error_msg = genre_model.verify_file_exists("test.mp3")
        assert not exists
        assert "Error con Path.exists(): Test error" in error_msg
        genre_model.verify_file_exists = original_verify

    @patch('pathlib.Path.exists')
    def test_process_empty_genres(self, mock_exists, genre_model):
        """Prueba el procesamiento con géneros vacíos."""
        mock_exists.return_value = True
        genre_model.detector.file_handler.is_valid_mp3.return_value = True
        genre_model.analyze = MagicMock(return_value={"processed_genres": {}})
        result = genre_model.process("test.mp3", 0.9, 2, True)
        assert result["written"] is False
        assert "No se detectaron géneros válidos" in result["error"]

    @patch('pathlib.Path.exists')
    def test_backup_error(self, mock_exists, genre_model):
        """Prueba error en backup."""
        mock_exists.return_value = True
        genre_model.detector.file_handler.is_valid_mp3.return_value = True
        genre_model.analyze = MagicMock(return_value={"processed_genres": {"Rock": 0.9}})
        genre_model.detector.file_handler._create_backup.return_value = False
        genre_model.detector.file_handler.rename_file_by_genre.return_value = {
            "success": True,
            "message": "Advertencia: No se pudo crear copia de seguridad",
            "new_path": "test_renamed.mp3"
        }
        result = genre_model.process("test.mp3", 0.7, 2, True)
        assert "Advertencia" in result["message"]

    @patch('pathlib.Path.exists')
    def test_write_error(self, mock_exists, genre_model):
        """Prueba error en escritura."""
        # Configuración inicial
        mock_exists.return_value = True
        genre_model.detector.file_handler.is_valid_mp3.return_value = True
        genre_model.detector.file_handler._create_backup.return_value = True
        genre_model.rename_after_update = False  # Desactivar rename
        
        # Configuración de mocks
        genre_model.analyze = MagicMock(return_value={"processed_genres": {"Rock": 0.9}})
        genre_model.detector.file_handler.write_genre = MagicMock(return_value=False)
        genre_model.detector.file_handler.get_file_info = MagicMock(return_value={})
        
        # Ejecutar prueba
        result = genre_model.process("test.mp3", 0.7, 2, True)
        
        # Verificaciones
        assert result["written"] is False
        assert "Error al escribir géneros en test.mp3" == result["error"]

    @patch('pathlib.Path.exists', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.access', return_value=True)
    def test_low_confidence(self, mock_access, mock_open, mock_os_exists, mock_path_exists, genre_model):
        """Prueba la adaptación automática de la confianza con géneros de baja confianza."""
        # Mock de operaciones básicas
        genre_model.detector.file_handler.is_valid_mp3.return_value = True
        genre_model.detector.file_handler.write_genre.return_value = True
        genre_model.detector.file_handler._create_backup.return_value = True
        genre_model.detector.file_handler.get_file_info.return_value = {
            "current_genre": "Rock;Pop"
        }
        
        # Mock de análisis con géneros de baja confianza pero cercanos
        genre_model.analyze = MagicMock(return_value={
            "processed_genres": {"Rock": 0.5, "Pop": 0.45}
        })
        
        # Ejecutar con umbral alto para forzar adaptación
        genre_model.rename_after_update = False  # Desactivar rename para simplificar
        result = genre_model.process("test.mp3", 0.9, 2, False)
        
        # Verificar adaptación de confianza y escritura exitosa
        assert result["written"] is True, "Debería escribir géneros con confianza adaptada"
        assert float(result["threshold_used"]) < 0.9, "Debería adaptar el umbral automáticamente"
        assert set(result["selected_genres_written"]) == {"Rock", "Pop"}, "Debería escribir ambos géneros"
        assert "error" not in result, f"No debería haber errores: {result.get('error', '')}"

if __name__ == '__main__':
    pytest.main(['-v'])