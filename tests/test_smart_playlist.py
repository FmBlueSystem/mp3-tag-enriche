import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from datetime import datetime

from src.core.smart_playlist import SmartPlaylist, SmartPlaylistError

class TestSmartPlaylist(unittest.TestCase):
    def setUp(self):
        """Configura el entorno de prueba."""
        self.test_dir = tempfile.mkdtemp()
        self.playlist = SmartPlaylist(
            playlist_id="test_001",
            name="Test Playlist",
            rule_text="genre = 'House'"
        )
        
    def tearDown(self):
        """Limpia el entorno después de las pruebas."""
        # Limpiar archivos temporales
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)
        
        # Detener triggers
        if hasattr(self, 'playlist'):
            self.playlist.trigger_manager.stop()
            
    def test_init_with_valid_rule(self):
        """Prueba la inicialización con una regla válida."""
        self.assertTrue(self.playlist.is_valid)
        self.assertIsNone(self.playlist.error_message)
        self.assertIsNotNone(self.playlist.ast)
        
    def test_init_with_invalid_rule(self):
        """Prueba la inicialización con una regla inválida."""
        playlist = SmartPlaylist(
            playlist_id="test_002",
            name="Invalid Playlist",
            rule_text="genre = 'House' AND AND bpm > 120"  # Regla inválida
        )
        self.assertFalse(playlist.is_valid)
        self.assertIsNotNone(playlist.error_message)
        self.assertIsNone(playlist.ast)
        
    def test_add_music_path(self):
        """Prueba agregar un directorio de música."""
        # Crear archivo temporal de prueba
        test_file = os.path.join(self.test_dir, "test.mp3")
        with open(test_file, 'w') as f:
            f.write("dummy content")
            
        # Agregar path y verificar
        self.playlist.add_music_path(self.test_dir)
        self.assertIn(self.test_dir, self.playlist._music_paths)
        self.assertIsNotNone(self.playlist.file_watcher)
        
    def test_add_invalid_music_path(self):
        """Prueba agregar un directorio inválido."""
        invalid_path = "/path/that/does/not/exist"
        with self.assertRaises(SmartPlaylistError):
            self.playlist.add_music_path(invalid_path)
            
    def test_setup_triggers(self):
        """Prueba la configuración de triggers."""
        # Configurar triggers
        self.playlist.add_music_path(self.test_dir)
        self.playlist.setup_triggers({
            'file_trigger': {
                'recursive': True,
                'file_patterns': {r'.*\.mp3$'}
            },
            'schedule_trigger': {
                'cron_expression': '*/5 * * * *',
                'skip_missed': True
            },
            'threshold_trigger': {
                'min_changes': 5,
                'max_wait_minutes': 10
            }
        })
        
        # Verificar configuración
        self.assertEqual(len(self.playlist.active_triggers), 3)
        stats = self.playlist.get_stats()
        self.assertIn('file', stats['active_triggers'])
        self.assertIn('schedule', stats['active_triggers'])
        self.assertIn('threshold', stats['active_triggers'])
        
    def test_set_rule(self):
        """Prueba cambios en la regla."""
        # Cambiar a regla válida
        new_rule = "(genre = 'Techno') AND (bpm > 120)"
        self.playlist.set_rule(new_rule)
        self.assertTrue(self.playlist.is_valid)
        self.assertEqual(self.playlist.rule_text, new_rule)
        
        # Cambiar a regla inválida
        bad_rule = "genre = 'House' AND AND bpm > 120"
        self.playlist.set_rule(bad_rule)
        self.assertFalse(self.playlist.is_valid)
        self.assertIsNotNone(self.playlist.error_message)
        
    def test_refresh(self):
        """Prueba la actualización de la playlist."""
        # Configurar regla válida
        self.playlist.set_rule("genre = 'House' AND year >= 2020")
        
        # La actualización debe ser exitosa con regla válida
        self.assertTrue(self.playlist.refresh())
        self.assertIsNotNone(self.playlist.last_update)
        
        # La actualización debe fallar con regla inválida
        self.playlist.set_rule("invalid rule")
        self.assertFalse(self.playlist.refresh())
        
    @patch('src.core.smart_playlist.TriggerManager')
    def test_trigger_integration(self, mock_manager):
        """Prueba la integración con el sistema de triggers."""
        # Configurar mock
        mock_manager.return_value = Mock()
        
        # Crear playlist con mock
        playlist = SmartPlaylist(
            playlist_id="test_003",
            name="Test Triggers",
            rule_text="genre = 'House'"
        )
        
        # Verificar que el manager se inicializa
        self.assertIsNotNone(playlist.trigger_manager)
        
        # Verificar que los cambios de regla notifican al manager
        playlist.set_rule("genre = 'Techno'")
        playlist.trigger_manager.process_event.assert_called()
        
    def test_get_stats(self):
        """Prueba la obtención de estadísticas."""
        stats = self.playlist.get_stats()
        
        # Verificar campos requeridos
        required_fields = [
            'id', 'name', 'is_valid', 'track_count',
            'creation_date', 'last_update', 'active_triggers',
            'music_paths', 'trigger_stats'
        ]
        for field in required_fields:
            self.assertIn(field, stats)
            
        # Verificar valores iniciales
        self.assertEqual(stats['id'], "test_001")
        self.assertEqual(stats['name'], "Test Playlist")
        self.assertTrue(stats['is_valid'])
        self.assertEqual(stats['track_count'], 0)
        self.assertEqual(len(stats['active_triggers']), 0)

if __name__ == '__main__':
    unittest.main()
