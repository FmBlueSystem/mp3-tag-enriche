"""
Tests para el extractor de metadatos
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from nueva_biblioteca.src.services.metadata_extractor import MetadataExtractor

@pytest.fixture
def extractor():
    """Fixture para el extractor de metadatos."""
    return MetadataExtractor()

@pytest.fixture
def mock_mp3_file(tmp_path):
    """Fixture que crea un archivo MP3 simulado."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.touch()
    return str(mp3_path)

def test_extract_from_file_nonexistent(extractor):
    """Prueba extracción de archivo inexistente."""
    result = extractor.extract_from_file("nonexistent.mp3")
    assert result is None

def test_extract_from_file_invalid_format(extractor, tmp_path):
    """Prueba extracción de archivo con formato inválido."""
    txt_file = tmp_path / "test.txt"
    txt_file.touch()
    result = extractor.extract_from_file(str(txt_file))
    assert result is None

@patch('nueva_biblioteca.src.services.metadata_extractor.MP3')
def test_extract_from_file_valid(mock_mp3, extractor, mock_mp3_file):
    """Prueba extracción exitosa de metadatos."""
    # Configurar mock
    mock_audio = MagicMock()
    mock_audio.get.side_effect = lambda x, default: {
        'title': ['Test Song'],
        'artist': ['Test Artist'],
        'album': ['Test Album'],
        'date': ['2023'],
        'genre': ['Rock'],
        'bpm': ['120']
    }.get(x, [default])
    
    mock_mp3.return_value = mock_audio
    mock_mp3.return_value.info.length = 180
    mock_mp3.return_value.info.bitrate = 320000
    mock_mp3.return_value.info.sample_rate = 44100
    mock_mp3.return_value.info.channels = 2
    
    # Ejecutar test
    result = extractor.extract_from_file(mock_mp3_file)
    
    # Verificar resultado
    assert result is not None
    assert result['title'] == 'Test Song'
    assert result['artist'] == 'Test Artist'
    assert result['album'] == 'Test Album'
    assert result['year'] == 2023
    assert result['genre'] == 'Rock'
    assert result['bpm'] == 120.0
    assert result['duration'] == 180
    assert result['bitrate'] == 320000
    assert result['sample_rate'] == 44100
    assert result['channels'] == 2
    assert result['path'] == mock_mp3_file

def test_scan_directory_nonexistent(extractor):
    """Prueba escaneo de directorio inexistente."""
    results = extractor.scan_directory("nonexistent")
    assert results['total'] == 0
    assert results['success'] == 0
    assert results['failed'] == 0
    assert len(results['errors']) == 1

@patch('nueva_biblioteca.src.services.metadata_extractor.MP3')
def test_scan_directory_with_files(mock_mp3, extractor, tmp_path):
    """Prueba escaneo de directorio con archivos."""
    # Crear archivos de prueba
    (tmp_path / "test1.mp3").touch()
    (tmp_path / "test2.mp3").touch()
    (tmp_path / "test3.txt").touch()
    
    # Configurar mock
    mock_audio = MagicMock()
    mock_audio.get.return_value = ['Test']
    mock_mp3.return_value = mock_audio
    mock_mp3.return_value.info.length = 180
    
    # Ejecutar test
    results = extractor.scan_directory(str(tmp_path))
    
    # Verificar resultados
    assert results['total'] == 2  # Solo archivos MP3
    assert results['success'] == 2
    assert results['failed'] == 0
    assert len(results['tracks']) == 2

@patch('nueva_biblioteca.src.services.metadata_extractor.MP3')
def test_scan_directory_with_errors(mock_mp3, extractor, tmp_path):
    """Prueba escaneo con errores de lectura."""
    # Crear archivo de prueba
    (tmp_path / "test.mp3").touch()
    
    # Configurar mock para lanzar error
    mock_mp3.side_effect = Exception("Error leyendo archivo")
    
    # Ejecutar test
    results = extractor.scan_directory(str(tmp_path))
    
    # Verificar resultados
    assert results['total'] == 1
    assert results['success'] == 0
    assert results['failed'] == 1
    assert len(results['errors']) == 1

def test_recursive_scan(extractor, tmp_path):
    """Prueba escaneo recursivo de directorios."""
    # Crear estructura de directorios
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (tmp_path / "test1.mp3").touch()
    (subdir / "test2.mp3").touch()
    
    # Probar con y sin recursión
    results_recursive = extractor.scan_directory(str(tmp_path), recursive=True)
    results_nonrecursive = extractor.scan_directory(str(tmp_path), recursive=False)
    
    assert results_recursive['total'] == 2
    assert results_nonrecursive['total'] == 1

def test_extract_year_variants(extractor):
    """Prueba extracción de año desde diferentes tags."""
    mock_audio = MagicMock()
    
    # Probar diferentes formatos de año
    test_cases = [
        (['2023'], 2023),  # Año simple
        (['2023-01-01'], 2023),  # Fecha ISO
        (['Released in 2023'], 2023),  # Texto con año
        (None, None),  # Sin año
        (['Invalid'], None),  # Formato inválido
    ]
    
    for tag_value, expected in test_cases:
        mock_audio.get.return_value = tag_value
        year = extractor._extract_year(mock_audio)
        assert year == expected

def test_extract_bpm_variants(extractor):
    """Prueba extracción de BPM desde diferentes formatos."""
    mock_audio = MagicMock()
    
    # Probar diferentes formatos de BPM
    test_cases = [
        (['120'], 120.0),  # Entero
        (['120.5'], 120.5),  # Decimal
        (None, None),  # Sin BPM
        (['Invalid'], None),  # Formato inválido
    ]
    
    for tag_value, expected in test_cases:
        mock_audio.get.return_value = tag_value
        bpm = extractor._extract_bpm(mock_audio)
        assert bpm == expected
