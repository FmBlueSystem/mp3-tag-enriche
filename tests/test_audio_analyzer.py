"""
Tests para el analizador de audio
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from nueva_biblioteca.src.services.audio_analyzer import AudioAnalyzer

@pytest.fixture
def analyzer():
    """Fixture que retorna un analizador de audio."""
    return AudioAnalyzer()

@pytest.fixture
def mock_audio_data():
    """Fixture que retorna datos de audio simulados."""
    # Generar onda sinusoidal simple
    sample_rate = 44100
    duration = 1.0  # 1 segundo
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440  # 440 Hz (nota A4)
    return np.sin(2 * np.pi * frequency * t)

def test_load_file_nonexistent(analyzer):
    """Prueba cargar archivo inexistente."""
    result = analyzer.load_file("nonexistent.mp3")
    assert result is False
    assert analyzer.current_audio is None
    assert analyzer.sample_rate is None

@patch('nueva_biblioteca.src.services.audio_analyzer.librosa.load')
def test_load_file_success(mock_load, analyzer, mock_audio_data, tmp_path):
    """Prueba cargar archivo exitosamente."""
    # Preparar archivo de prueba
    test_file = tmp_path / "test.mp3"
    test_file.touch()
    
    # Configurar mock
    mock_load.return_value = (mock_audio_data, 44100)
    
    # Probar carga
    result = analyzer.load_file(str(test_file))
    assert result is True
    assert analyzer.current_audio is not None
    assert analyzer.sample_rate == 44100
    
    mock_load.assert_called_once_with(str(test_file), sr=None)

def test_analyze_segment_no_audio(analyzer):
    """Prueba analizar segmento sin audio cargado."""
    results = analyzer.analyze_segment(0, 1)
    assert results == {}

@patch('nueva_biblioteca.src.services.audio_analyzer.librosa.beat.beat_track')
@patch('nueva_biblioteca.src.services.audio_analyzer.librosa.feature.chroma_cqt')
def test_analyze_segment_success(mock_chroma, mock_beat_track, analyzer, mock_audio_data):
    """Prueba analizar segmento exitosamente."""
    # Configurar analizador
    analyzer.current_audio = mock_audio_data
    analyzer.sample_rate = 44100
    
    # Configurar mocks
    mock_beat_track.return_value = (120, None)  # 120 BPM
    mock_chroma.return_value = np.zeros((12, 100))  # Cromagrama simulado
    mock_chroma.return_value[0] = 1  # Simular nota C como dominante
    
    # Analizar segmento
    results = analyzer.analyze_segment(0, 1)
    
    # Verificar resultados
    assert 'bpm' in results
    assert 'key' in results
    assert 'energy' in results
    assert 'spectrum' in results
    assert 'volume' in results
    
    assert results['bpm'] == 120.0
    assert results['key'] == 'C'
    assert isinstance(results['energy'], float)
    assert isinstance(results['spectrum'], list)
    assert isinstance(results['volume'], float)
    
    # Verificar que energía y volumen están normalizados
    assert 0 <= results['energy'] <= 1
    assert 0 <= results['volume'] <= 1

def test_get_waveform_no_audio(analyzer):
    """Prueba obtener forma de onda sin audio cargado."""
    result = analyzer.get_waveform()
    assert result is None

def test_get_waveform_success(analyzer, mock_audio_data):
    """Prueba obtener forma de onda exitosamente."""
    analyzer.current_audio = mock_audio_data
    analyzer.sample_rate = 44100
    
    waveform = analyzer.get_waveform(width=100, height=200)
    assert waveform is not None
    assert len(waveform) == 100  # Ancho especificado
    assert all(0 <= x <= 100 for x in waveform)  # Altura/2 especificada

def test_extract_bpm_invalid_audio(analyzer):
    """Prueba extraer BPM de audio inválido."""
    result = analyzer._extract_bpm(np.array([]))
    assert result is None

@patch('nueva_biblioteca.src.services.audio_analyzer.librosa.beat.beat_track')
def test_extract_bpm_success(mock_beat_track, analyzer, mock_audio_data):
    """Prueba extraer BPM exitosamente."""
    analyzer.sample_rate = 44100
    mock_beat_track.return_value = (120, None)
    
    result = analyzer._extract_bpm(mock_audio_data)
    assert result == 120.0

def test_extract_key_invalid_audio(analyzer):
    """Prueba extraer tonalidad de audio inválido."""
    result = analyzer._extract_key(np.array([]))
    assert result is None

@patch('nueva_biblioteca.src.services.audio_analyzer.librosa.feature.chroma_cqt')
def test_extract_key_success(mock_chroma, analyzer, mock_audio_data):
    """Prueba extraer tonalidad exitosamente."""
    analyzer.sample_rate = 44100
    
    # Simular cromagrama con G como nota dominante
    chroma = np.zeros((12, 100))
    chroma[7] = 1  # G es índice 7 (C=0, C#=1, etc.)
    mock_chroma.return_value = chroma
    
    result = analyzer._extract_key(mock_audio_data)
    assert result == 'G'

def test_extract_energy_invalid_audio(analyzer):
    """Prueba extraer energía de audio inválido."""
    result = analyzer._extract_energy(np.array([]))
    assert result is None

def test_extract_energy_success(analyzer):
    """Prueba extraer energía exitosamente."""
    # Crear audio de prueba con amplitud conocida
    audio = np.array([0.5] * 1000)  # Señal constante de amplitud 0.5
    
    result = analyzer._extract_energy(audio)
    assert result is not None
    assert 0 <= result <= 1
    assert result == 0.5  # La energía debe ser aproximadamente la amplitud RMS

def test_extract_volume_invalid_audio(analyzer):
    """Prueba extraer volumen de audio inválido."""
    result = analyzer._extract_volume(np.array([]))
    assert result is None

@patch('nueva_biblioteca.src.services.audio_analyzer.librosa.feature.rms')
def test_extract_volume_success(mock_rms, analyzer, mock_audio_data):
    """Prueba extraer volumen exitosamente."""
    # Simular RMS con valor conocido
    mock_rms.return_value = np.array([[0.5]])
    
    result = analyzer._extract_volume(mock_audio_data)
    assert result is not None
    assert 0 <= result <= 1

def test_extract_spectrum_invalid_audio(analyzer):
    """Prueba extraer espectro de audio inválido."""
    result = analyzer._extract_spectrum(np.array([]))
    assert result is None

@patch('nueva_biblioteca.src.services.audio_analyzer.librosa.stft')
def test_extract_spectrum_success(mock_stft, analyzer, mock_audio_data):
    """Prueba extraer espectro exitosamente."""
    # Simular espectrograma
    mock_stft.return_value = np.ones((128, 100)) * 0.5
    
    result = analyzer._extract_spectrum(mock_audio_data)
    assert result is not None
    assert len(result) <= 128  # No más de 128 bandas
    assert all(isinstance(x, float) for x in result)
