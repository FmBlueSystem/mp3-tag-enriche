"""Pruebas unitarias para ProcessingThread."""
import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QThread
from src.gui.threads.processing_thread import ProcessingThread
from src.gui.threads.task_queue import TaskState
from src.gui.models.genre_model import GenreModel

@pytest.fixture
def mock_model():
    """Fixture que proporciona un modelo simulado."""
    model = MagicMock(spec=GenreModel)
    model.analyze.return_value = {
        "detected_genres": {"Rock": 0.8, "Pop": 0.6},
        "error": None
    }
    model.process.return_value = {
        "written": True,
        "renamed": False,
        "message": "Éxito",
        "error": None
    }
    return model

@pytest.fixture
def test_files(tmp_path):
    """Fixture que crea archivos de prueba temporales."""
    files = []
    for i in range(3):
        file_path = tmp_path / f"test_{i}.mp3"
        file_path.touch()
        files.append(str(file_path))
    return files

@pytest.fixture
def processing_thread(mock_model, test_files):
    """Fixture que proporciona un thread de procesamiento configurado."""
    return ProcessingThread(
        file_paths=test_files,
        model=mock_model,
        analyze_only=True,
        confidence=0.3,
        max_genres=3,
        rename_files=False,
        backup_dir=None
    )

def test_thread_initialization(processing_thread, test_files):
    """Prueba la inicialización correcta del thread."""
    assert isinstance(processing_thread, QThread)
    assert processing_thread.file_paths == test_files
    assert processing_thread.analyze_only is True
    assert processing_thread.confidence == 0.3
    assert processing_thread.max_genres == 3
    assert processing_thread.rename_files is False
    assert processing_thread.is_running is True

def test_stop_thread(processing_thread):
    """Prueba la detención segura del thread."""
    assert processing_thread.is_running is True
    processing_thread.stop()
    assert processing_thread.is_running is False

def test_process_file_analyze(processing_thread, mock_model):
    """Prueba el procesamiento en modo análisis."""
    result = processing_thread.process_file("test.mp3")
    assert "detected_genres" in result
    assert result["detected_genres"]["Rock"] == 0.8
    mock_model.analyze.assert_called_once()

def test_process_file_full(mock_model):
    """Prueba el procesamiento completo de archivo."""
    thread = ProcessingThread(
        file_paths=["test.mp3"],
        model=mock_model,
        analyze_only=False,
        confidence=0.3,
        max_genres=3
    )
    result = thread.process_file("test.mp3")
    assert result["written"] is True
    assert result["message"] == "Éxito"
    mock_model.process.assert_called_once()

def test_process_file_error(processing_thread, mock_model):
    """Prueba manejo de errores en procesamiento."""
    mock_model.analyze.side_effect = Exception("Test error")
    result = processing_thread.process_file("test.mp3")
    assert "error" in result
    assert result["error"] == "Test error"

def test_run_empty_files(processing_thread):
    """Prueba ejecución sin archivos."""
    processing_thread.file_paths = []
    
    # Capturar señales
    progress_signals = []
    finished_data = [None]  # Usar lista para mutabilidad
    
    processing_thread.progress.connect(lambda msg: progress_signals.append(msg))
    processing_thread.finished.connect(lambda data: finished_data.__setitem__(0, data))
    
    processing_thread.run()
    
    assert len(progress_signals) == 1
    assert "No hay archivos seleccionados" in progress_signals[0]
    assert finished_data[0] is not None
    assert finished_data[0]["total"] == 0

def test_run_with_files(processing_thread, test_files):
    """Prueba ejecución con archivos válidos."""
    # Capturar señales
    progress_signals = []
    finished_data = [None]
    processed_files = []
    state_changes = []
    
    processing_thread.progress.connect(lambda msg: progress_signals.append(msg))
    processing_thread.finished.connect(lambda data: finished_data.__setitem__(0, data))
    processing_thread.file_processed.connect(
        lambda fp, msg, error: processed_files.append((fp, msg, error))
    )
    processing_thread.task_state_changed.connect(
        lambda tid, state: state_changes.append((tid, state))
    )
    
    processing_thread.run()
    
    assert len(processed_files) == len(test_files)
    assert all(not error for _, _, error in processed_files)
    assert finished_data[0]["success"] == len(test_files)
    assert finished_data[0]["errors"] == 0

def test_run_with_errors(processing_thread, test_files, mock_model):
    """Prueba ejecución con errores de procesamiento."""
    mock_model.analyze.side_effect = Exception("Test error")
    
    # Capturar señales
    processed_files = []
    finished_data = [None]
    
    processing_thread.file_processed.connect(
        lambda fp, msg, error: processed_files.append((fp, msg, error))
    )
    processing_thread.finished.connect(lambda data: finished_data.__setitem__(0, data))
    
    processing_thread.run()
    
    assert all(error for _, _, error in processed_files)
    assert finished_data[0]["errors"] == len(test_files)
    assert finished_data[0]["success"] == 0

def test_circuit_breaker_integration(processing_thread, mock_model):
    """Prueba integración con circuit breaker."""
    # Configurar el modelo para fallar consistentemente
    mock_model.analyze.side_effect = Exception("Test error")
    
    # Capturar señales del circuit breaker
    breaker_signals = {"opened": False, "closed": False}
    
    def on_breaker_opened():
        breaker_signals["opened"] = True
        
    def on_breaker_closed():
        breaker_signals["closed"] = True
    
    processing_thread.circuit_breaker_opened.connect(on_breaker_opened)
    processing_thread.circuit_breaker_closed.connect(on_breaker_closed)
    
    # Reducir el umbral del circuit breaker para la prueba
    processing_thread.task_queue.circuit_breaker.failure_threshold = 2
    
    processing_thread.run()
    
    assert breaker_signals["opened"] is True

def test_renaming_integration(mock_model):
    """Prueba integración con renombrado de archivos."""
    # Configurar el modelo para simular renombrado exitoso
    mock_model.process.return_value = {
        "written": True,
        "renamed": True,
        "new_filepath": "new_test.mp3",
        "message": "Archivo renombrado exitosamente"
    }
    
    thread = ProcessingThread(
        file_paths=["test.mp3"],
        model=mock_model,
        analyze_only=False,
        rename_files=True
    )
    
    # Capturar señales
    processed_files = []
    finished_data = [None]
    
    thread.file_processed.connect(
        lambda fp, msg, error: processed_files.append((fp, msg, error))
    )
    thread.finished.connect(lambda data: finished_data.__setitem__(0, data))
    
    thread.run()
    
    assert len(processed_files) == 1
    assert not processed_files[0][2]  # no error
    assert "renombrado" in processed_files[0][1].lower()
    assert finished_data[0]["renamed"] == 1

def test_backup_directory_handling(tmp_path):
    """Prueba manejo del directorio de respaldo."""
    backup_dir = str(tmp_path / "backups")
    model = MagicMock(spec=GenreModel)
    
    # Simular el detector y file_handler en el modelo
    model.detector = MagicMock()
    model.detector.file_handler = MagicMock()
    
    thread = ProcessingThread(
        file_paths=["test.mp3"],
        model=model,
        backup_dir=backup_dir
    )
    
    # Verificar que se configuró el backup_dir en el file_handler
    model.detector.file_handler.set_backup_dir.assert_called_once_with(backup_dir)

def test_concurrent_processing(processing_thread, test_files, mock_model):
    """Prueba procesamiento concurrente de archivos."""
    # Simular procesamiento que toma tiempo
    def slow_process(*args, **kwargs):
        import time
        time.sleep(0.1)
        return {
            "detected_genres": {"Rock": 0.8},
            "error": None
        }
    
    mock_model.analyze.side_effect = slow_process
    
    # Capturar orden de procesamiento
    processed_order = []
    processing_thread.file_processed.connect(
        lambda fp, msg, error: processed_order.append(fp)
    )
    
    processing_thread.run()
    
    # Verificar que todos los archivos fueron procesados
    assert set(processed_order) == set(test_files)
    assert len(processed_order) == len(test_files)

def test_progress_reporting(processing_thread, test_files):
    """Prueba reportes de progreso."""
    progress_updates = []
    processing_thread.progress.connect(
        lambda msg: progress_updates.append(msg)
    )
    
    processing_thread.run()
    
    # Verificar mensajes de progreso
    assert len(progress_updates) > len(test_files)
    assert any("Procesando" in msg for msg in progress_updates)
    assert any(f"{len(test_files)}/{len(test_files)}" in msg 
              for msg in progress_updates)

def test_error_result_details(processing_thread, test_files, mock_model):
    """Prueba detalles en resultados de error."""
    # Simular error específico
    mock_model.analyze.return_value = {
        "error": "Error de análisis",
        "detected_genres_initial_clean": {},
        "threshold_used": 0.3
    }
    
    finished_data = [None]
    processing_thread.finished.connect(lambda data: finished_data.__setitem__(0, data))
    
    processing_thread.run()
    
    # Verificar detalles del resultado
    assert finished_data[0] is not None
    assert len(finished_data[0]["details"]) == len(test_files)
    for detail in finished_data[0]["details"]:
        assert "error" in detail
        assert detail["error"] == "Error de análisis"
        assert "threshold_used" in detail
        assert detail["threshold_used"] == 0.3

def test_real_mp3_processing():
    """Prueba procesamiento con archivos MP3 reales."""
    # Directorio con archivos MP3 reales
    mp3_dir = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-Mix Club Classics/X-MIX CLUB CLASSICS BEST OF 320 (Seperated Tracks)"
    
    # Obtener lista de archivos MP3
    file_paths = [
        os.path.join(mp3_dir, f)
        for f in os.listdir(mp3_dir)
        if f.endswith('.mp3')
    ][:3]  # Tomar solo 3 archivos para la prueba
    
    assert len(file_paths) > 0, "No se encontraron archivos MP3"
    
    # Crear modelo real
    model = GenreModel()
    
    # Configurar thread
    thread = ProcessingThread(
        file_paths=file_paths,
        model=model,
        analyze_only=True,
        confidence=0.3,
        max_genres=3,
        rename_files=False
    )
    
    # Capturar señales
    processed_files = []
    finished_data = [None]
    
    thread.file_processed.connect(
        lambda fp, msg, error: processed_files.append((fp, msg, error))
    )
    thread.finished.connect(lambda data: finished_data.__setitem__(0, data))
    
    # Ejecutar procesamiento
    thread.run()
    
    # Verificar resultados
    assert len(processed_files) == len(file_paths)
    assert finished_data[0]["total"] == len(file_paths)
    assert finished_data[0]["success"] + finished_data[0]["errors"] == len(file_paths)
    
    # Verificar que cada archivo tenga resultados
    for fp, msg, error in processed_files:
        assert os.path.exists(fp), f"Archivo no existe: {fp}"
        if not error:
            assert "Géneros detectados" in msg, f"No se detectaron géneros en {fp}"