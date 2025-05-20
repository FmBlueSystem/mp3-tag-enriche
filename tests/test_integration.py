"""Tests de integración end-to-end para el sistema completo."""
import os
import pytest
import shutil
import time
from pathlib import Path
from typing import List

from src.core.genre_detector import GenreDetector
from src.core.music_apis import MusicBrainzAPI
from src.core.file_handler import Mp3FileHandler
from src.core.persistent_cache import PersistentCache
from src.gui.models.genre_model import GenreModel
from src.gui.threads.processing_thread import ProcessingThread
from src.gui.threads.task_queue import TaskQueue, TaskState

def setup_test_environment(mp3_collection: List[str], backup_dir: str) -> dict:
    """Configura el entorno de prueba.
    
    Args:
        mp3_collection: Lista de archivos MP3 de prueba
        backup_dir: Directorio para backups
        
    Returns:
        dict: Componentes inicializados del sistema
    """
    # Crear directorios de prueba
    test_cache_dir = Path(backup_dir) / "test_cache"
    test_cache_dir.mkdir(exist_ok=True)
    
    # Inicializar APIs (usando solo MusicBrainz por ahora)
    apis = [MusicBrainzAPI()]
    
    # Intentar cargar APIs adicionales si están disponibles
    try:
        from src.core.music_apis import LastFmAPI
        apis.append(LastFmAPI())
    except (ImportError, AttributeError):
        print("LastFmAPI no disponible")
        
    try:
        from src.core.music_apis import DiscogsAPI
        apis.append(DiscogsAPI())
    except (ImportError, AttributeError):
        print("DiscogsAPI no disponible")
    
    # Configurar sistema
    file_handler = Mp3FileHandler(backup_dir=backup_dir)
    detector = GenreDetector(apis=apis, file_handler=file_handler)
    cache = PersistentCache(cache_dir=str(test_cache_dir))
    model = GenreModel()
    task_queue = TaskQueue()
    
    return {
        "detector": detector,
        "file_handler": file_handler,
        "cache": cache,
        "model": model,
        "task_queue": task_queue,
        "test_files": mp3_collection
    }

class TestIntegrationEndToEnd:
    """Suite de pruebas de integración end-to-end."""
    
    def teardown_method(self, method):
        """Limpia recursos después de cada prueba."""
        # Limpiar directorio de caché de pruebas
        if hasattr(self, 'env'):
            cache_dir = Path(self.env["cache"]._cache_dir)
            if cache_dir.exists():
                for cache_file in cache_dir.glob("*.json"):
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
                try:
                    cache_dir.rmdir()
                except OSError:
                    pass
    
    def test_flujo_normal_completo(self, mp3_collection, backup_dir, mock_musicbrainz_api):
        """Verifica el flujo completo del sistema con un caso normal."""
        # Configurar
        self.env = setup_test_environment(mp3_collection, backup_dir)
        env = self.env
        detector = env["detector"]
        model = env["model"]
        
        # 1. Analizar archivos
        start_time = time.time()
        results = detector.analyze_files(env["test_files"])
        processing_time = time.time() - start_time
        
        # Verificar resultados básicos
        assert results, "Debe haber resultados"
        assert len(results) == len(env["test_files"]), "Debe procesar todos los archivos"
        
        # 2. Verificar detección de géneros
        for path, result in results.items():
            assert "detected_genres" in result, f"Debe detectar géneros para {path}"
            genres = result["detected_genres"]
            assert genres, f"Debe tener al menos un género para {path}"
            
            # Verificar normalización
            for genre in genres:
                assert isinstance(genre, str), "Géneros deben ser strings"
                assert len(genre) > 0, "Géneros no deben estar vacíos"
                
        # 3. Verificar métricas
        assert processing_time < 30, "El procesamiento no debe tomar más de 30 segundos"
        
        # 4. Verificar integración con el modelo
        model.update_results(results)
        assert model.rowCount() == len(results), "Modelo debe reflejar todos los resultados"
    
    def test_manejo_errores_y_recuperacion(self, mp3_collection, backup_dir, caplog):
        """Verifica el manejo de errores y la capacidad de recuperación."""
        self.env = setup_test_environment(mp3_collection, backup_dir)
        env = self.env
        detector = env["detector"]
        
        # 1. Probar con archivo corrupto
        corrupt_file = Path(mp3_collection[0]).parent / "corrupt.mp3"
        shutil.copy2(mp3_collection[0], corrupt_file)
        with open(corrupt_file, "wb") as f:
            f.write(b"datos corruptos")
            
        test_files = [str(corrupt_file)] + env["test_files"]
        results = detector.analyze_files(test_files)
        
        # Verificar manejo de error
        assert str(corrupt_file) in results
        assert "error" in results[str(corrupt_file)]
        
        # Verificar recuperación
        valid_results = {k: v for k, v in results.items() if k != str(corrupt_file)}
        assert len(valid_results) == len(env["test_files"])
        
        # 2. Verificar logging de errores
        assert any("Error" in record.message for record in caplog.records)
    
    def test_limites_sistema(self, mp3_collection, backup_dir):
        """Verifica los límites y restricciones del sistema."""
        self.env = setup_test_environment(mp3_collection, backup_dir)
        env = self.env
        detector = env["detector"]
        
        # 1. Verificar límite de géneros
        results = detector.analyze_files(env["test_files"])
        for result in results.values():
            if "detected_genres" in result:
                assert len(result["detected_genres"]) <= detector.max_genres
                
        # 2. Verificar umbral de confianza
        for result in results.values():
            if "detected_genres" in result and result["detected_genres"]:
                scores = result["detected_genres"].values()
                assert all(score >= detector.confidence_threshold for score in scores)
    
    def test_escenarios_concurrentes(self, mp3_collection, backup_dir):
        """Verifica el comportamiento en escenarios concurrentes."""
        self.env = setup_test_environment(mp3_collection, backup_dir)
        env = self.env
        task_queue = env["task_queue"]
        model = env["model"]
        
        # 1. Configurar procesamiento concurrente
        processing_thread = ProcessingThread(task_queue=task_queue, model=model)
        processing_thread.start()
        
        try:
            # 2. Encolar múltiples tareas
            for i, file_path_str in enumerate(env["test_files"]):
                task_id = f"test_task_{i}_{Path(file_path_str).name}"
                task_queue.add_task(task_id, lambda f=file_path_str: env["detector"].analyze_file(f))
            
            # 3. Esperar completación
            all_done = False
            max_wait_time = 30  # Esperar un máximo de 30 segundos
            wait_start_time = time.time()
            
            # Bucle para esperar a que todas las tareas se procesen
            while not all_done and (time.time() - wait_start_time) < max_wait_time:
                if not task_queue.queue.empty(): # Comprobar si la cola de entrada tiene tareas pendientes
                    all_done = False
                    time.sleep(0.1) 
                    continue

                all_done = True # Asumir que todo está hecho hasta encontrar una tarea no finalizada
                with task_queue._lock: # Acceder a _active_tasks de forma segura
                    for task in task_queue._active_tasks:
                        if task.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                            all_done = False
                            break # Salir del bucle for si se encuentra una tarea no finalizada
                
                if not all_done:
                    time.sleep(0.1) # Esperar un poco antes de volver a verificar

            if not all_done:
                pending_tasks_details = []
                with task_queue._lock:
                    for task in task_queue._active_tasks:
                        if task.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                            pending_tasks_details.append(f"ID: {task.id}, Estado: {task.state.value}")
                details_str = "; ".join(pending_tasks_details)
                raise TimeoutError(f"Las tareas no se completaron en {max_wait_time} segundos. Detalles: {details_str}")

            # Calcular completed_count y has_errors a partir de _active_tasks
            completed_count = 0
            has_errors_flag = False # Renombrar para evitar conflicto con un posible método has_errors
            with task_queue._lock:
                for task in task_queue._active_tasks:
                    if task.state == TaskState.COMPLETED:
                        completed_count += 1
                    elif task.state == TaskState.FAILED:
                        has_errors_flag = True
            
            # 4. Verificar resultados
            assert completed_count == len(env["test_files"]), \
                f"Esperado {len(env['test_files'])} tareas completadas, pero fueron {completed_count}"
            assert not has_errors_flag, "Se encontraron errores en las tareas procesadas"
            
        finally:
            # Limpiar
            processing_thread.stop()
            processing_thread.wait()