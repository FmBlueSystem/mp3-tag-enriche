import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from datetime import datetime

from src.core.triggers import (
    TriggerManager, MusicFileWatcher,
    FileTrigger, ScheduleTrigger, ThresholdTrigger,
    TriggerEvent, TriggerType
)

class TestTriggerSystem(unittest.TestCase):
    def setUp(self):
        """Configura el entorno de prueba."""
        self.manager = TriggerManager()
        self.playlist_id = "test_playlist_001"
        
        # Crear directorio temporal para archivos de prueba
        self.test_dir = tempfile.mkdtemp()
        self.watcher = MusicFileWatcher(self.manager)
        
    def tearDown(self):
        """Limpia el entorno después de las pruebas."""
        self.manager.stop()
        # Limpiar archivos temporales
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)
        
    def test_file_trigger(self):
        """Prueba el FileTrigger con eventos de archivo."""
        # Configurar trigger
        trigger = FileTrigger(self.playlist_id, self.watcher)
        trigger.configure({
            'watch_paths': {self.test_dir},
            'file_patterns': {r'.*\.mp3$'},
            'debounce_seconds': 0.1
        })
        self.manager.register_trigger(trigger)
        
        # Crear evento de prueba
        event = TriggerEvent(
            type=TriggerType.FILE_ADDED,
            playlist_id=self.playlist_id,
            timestamp=datetime.now(),
            source="test",
            data={"file_path": os.path.join(self.test_dir, "test.mp3")}
        )
        
        # Verificar que el trigger responde al evento
        self.assertTrue(trigger.should_trigger(event))
        self.assertTrue(trigger.execute(event))
        
    def test_schedule_trigger(self):
        """Prueba el ScheduleTrigger con eventos programados."""
        # Configurar trigger
        trigger = ScheduleTrigger(self.playlist_id)
        trigger.configure({
            'cron_expression': '* * * * *',  # Cada minuto
            'skip_missed': True
        })
        self.manager.register_trigger(trigger)
        
        # Crear evento de prueba
        event = TriggerEvent(
            type=TriggerType.SCHEDULED,
            playlist_id=self.playlist_id,
            timestamp=datetime.now(),
            source="test",
            data={}
        )
        
        # El trigger debería estar listo para la próxima ejecución
        self.assertIsNotNone(trigger.get_next_run())
        
    def test_threshold_trigger(self):
        """Prueba el ThresholdTrigger con acumulación de cambios."""
        # Configurar trigger
        trigger = ThresholdTrigger(self.playlist_id)
        trigger.configure({
            'min_changes': 2,
            'max_wait_minutes': 1
        })
        self.manager.register_trigger(trigger)
        
        # Crear eventos de prueba
        events = [
            TriggerEvent(
                type=TriggerType.FILE_MODIFIED,
                playlist_id=self.playlist_id,
                timestamp=datetime.now(),
                source="test",
                data={"file_path": f"test{i}.mp3"}
            )
            for i in range(3)
        ]
        
        # Los primeros eventos no deberían activar el trigger
        self.assertFalse(trigger.should_trigger(events[0]))
        
        # El evento que supera el umbral debería activarlo
        self.assertTrue(trigger.should_trigger(events[1]))
        
    def test_trigger_manager_integration(self):
        """Prueba la integración de todos los componentes."""
        # Configurar triggers
        file_trigger = FileTrigger(self.playlist_id, self.watcher)
        schedule_trigger = ScheduleTrigger(self.playlist_id)
        threshold_trigger = ThresholdTrigger(self.playlist_id)
        
        # Registrar triggers
        self.manager.register_trigger(file_trigger)
        self.manager.register_trigger(schedule_trigger)
        self.manager.register_trigger(threshold_trigger)
        
        # Verificar que los triggers están registrados
        triggers = self.manager.get_triggers(self.playlist_id)
        self.assertEqual(len(triggers), 3)
        
        # Verificar que el manager procesa eventos
        self.manager.start()
        event = TriggerEvent(
            type=TriggerType.FILE_ADDED,
            playlist_id=self.playlist_id,
            timestamp=datetime.now(),
            source="test",
            data={"file_path": "test.mp3"}
        )
        self.manager.process_event(event)
        
        # Verificar estadísticas
        stats = self.manager.get_stats()
        self.assertIn(self.playlist_id, stats["playlists"])

if __name__ == '__main__':
    unittest.main()
