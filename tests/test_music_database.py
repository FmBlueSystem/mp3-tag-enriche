"""
Pruebas para el sistema de bases de datos de música.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from typing import Dict

from src.core.database.music_database import (
    TrackMetadata, DatabaseFactory, 
    SQLiteDatabase, JSONDatabase
)

class TestTrackMetadata(unittest.TestCase):
    """Pruebas para la clase TrackMetadata."""
    
    def test_create_metadata(self):
        """Prueba crear metadata con diferentes combinaciones de datos."""
        # Metadata completa
        metadata = TrackMetadata(
            id="track1",
            title="Test Track",
            artist="Test Artist",
            album="Test Album",
            key="G maj",
            bpm=128.0,
            energy=0.8,
            danceability=0.7,
            year=2025,
            genre="Test Genre",
            path="/test/path.mp3"
        )
        
        self.assertEqual(metadata.id, "track1")
        self.assertEqual(metadata.title, "Test Track")
        self.assertEqual(metadata.key, "G maj")
        self.assertEqual(metadata.bpm, 128.0)
        
        # Metadata mínima
        metadata = TrackMetadata(
            id="track2",
            title="Test Track 2",
            artist="Test Artist 2",
            album="Test Album 2"
        )
        
        self.assertIsNone(metadata.key)
        self.assertIsNone(metadata.bpm)
        self.assertIsNone(metadata.energy)

class TestSQLiteDatabase(unittest.TestCase):
    """Pruebas para la base de datos SQLite."""
    
    def setUp(self):
        """Configura ambiente de prueba."""
        # Crear base de datos temporal
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        
        # Crear instancia
        self.db = SQLiteDatabase(self.db_path)
        self.db.connect()
        
        # Datos de prueba
        self.test_track = {
            'id': 'test1',
            'title': 'Test Track',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'key': 'G maj',
            'bpm': 128.0,
            'energy': 0.8,
            'danceability': 0.7,
            'year': 2025,
            'genre': 'Test Genre',
            'path': '/test/path.mp3'
        }
        
    def tearDown(self):
        """Limpia ambiente de prueba."""
        self.db.disconnect()
        try:
            os.remove(self.db_path)
            os.rmdir(self.temp_dir)
        except:
            pass
            
    def test_connect_disconnect(self):
        """Prueba conexión y desconexión."""
        # Ya conectada en setUp
        self.assertIsNotNone(self.db.conn)
        self.assertIsNotNone(self.db.cursor)
        
        # Desconectar
        self.db.disconnect()
        self.assertIsNone(self.db.conn)
        self.assertIsNone(self.db.cursor)
        
        # Reconectar
        self.assertTrue(self.db.connect())
        
    def test_track_crud(self):
        """Prueba operaciones CRUD de tracks."""
        # Insertar track
        self.assertTrue(
            self.db.update_track(self.test_track['id'], self.test_track)
        )
        
        # Obtener track
        track = self.db.get_track(self.test_track['id'])
        self.assertIsNotNone(track)
        self.assertEqual(track.title, self.test_track['title'])
        self.assertEqual(track.key, self.test_track['key'])
        
        # Actualizar track
        update_data = {'bpm': 130.0, 'energy': 0.9}
        self.assertTrue(
            self.db.update_track(self.test_track['id'], update_data)
        )
        
        track = self.db.get_track(self.test_track['id'])
        self.assertEqual(track.bpm, 130.0)
        self.assertEqual(track.energy, 0.9)
        
    def test_get_tracks_with_filters(self):
        """Prueba obtener tracks con filtros."""
        # Insertar tracks de prueba
        tracks_data = [
            {
                'id': 'test1',
                'title': 'Track 1',
                'artist': 'Artist 1',
                'album': 'Album 1',
                'key': 'G maj',
                'bpm': 128.0
            },
            {
                'id': 'test2',
                'title': 'Track 2',
                'artist': 'Artist 1',
                'album': 'Album 2',
                'key': 'A min',
                'bpm': 130.0
            },
            {
                'id': 'test3',
                'title': 'Track 3',
                'artist': 'Artist 2',
                'album': 'Album 3',
                'key': 'G maj',
                'bpm': 126.0
            }
        ]
        
        for track in tracks_data:
            self.db.update_track(track['id'], track)
            
        # Filtrar por artista
        tracks = self.db.get_tracks({'artist': 'Artist 1'})
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0].artist, 'Artist 1')
        
        # Filtrar por clave
        tracks = self.db.get_tracks({'key': 'G maj'})
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0].key, 'G maj')
        
        # Múltiples filtros
        tracks = self.db.get_tracks({
            'key': 'G maj',
            'artist': 'Artist 1'
        })
        self.assertEqual(len(tracks), 1)
        
        # Filtro con lista de valores
        tracks = self.db.get_tracks({
            'key': ['G maj', 'A min']
        })
        self.assertEqual(len(tracks), 3)

class TestJSONDatabase(unittest.TestCase):
    """Pruebas para la base de datos JSON."""
    
    def setUp(self):
        """Configura ambiente de prueba."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.json")
        
        self.db = JSONDatabase(self.db_path)
        self.db.connect()
        
        self.test_track = {
            'id': 'test1',
            'title': 'Test Track',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'key': 'G maj',
            'bpm': 128.0,
            'energy': 0.8,
            'danceability': 0.7,
            'year': 2025,
            'genre': 'Test Genre',
            'path': '/test/path.mp3'
        }
        
    def tearDown(self):
        """Limpia ambiente de prueba."""
        self.db.disconnect()
        try:
            os.remove(self.db_path)
            os.rmdir(self.temp_dir)
        except:
            pass
            
    def test_file_operations(self):
        """Prueba operaciones de archivo."""
        # Archivo creado en connect()
        self.assertTrue(os.path.exists(self.db_path))
        
        # Verificar estructura inicial
        with open(self.db_path, 'r') as f:
            data = json.load(f)
            self.assertIn('tracks', data)
            self.assertEqual(len(data['tracks']), 0)
            
    def test_track_crud(self):
        """Prueba operaciones CRUD de tracks."""
        # Insertar track
        self.assertTrue(
            self.db.update_track(self.test_track['id'], self.test_track)
        )
        
        # Verificar en memoria
        self.assertIn(self.test_track['id'], self.db.data['tracks'])
        
        # Verificar en archivo
        with open(self.db_path, 'r') as f:
            data = json.load(f)
            self.assertIn(self.test_track['id'], data['tracks'])
            
        # Obtener track
        track = self.db.get_track(self.test_track['id'])
        self.assertIsNotNone(track)
        self.assertEqual(track.title, self.test_track['title'])
        
        # Actualizar track
        update_data = {'bpm': 130.0}
        self.assertTrue(
            self.db.update_track(self.test_track['id'], update_data)
        )
        
        track = self.db.get_track(self.test_track['id'])
        self.assertEqual(track.bpm, 130.0)
        
    def test_get_tracks_with_filters(self):
        """Prueba obtener tracks con filtros."""
        # Insertar tracks de prueba
        tracks_data = [
            {
                'id': 'test1',
                'title': 'Track 1',
                'artist': 'Artist 1',
                'album': 'Album 1',
                'key': 'G maj'
            },
            {
                'id': 'test2',
                'title': 'Track 2',
                'artist': 'Artist 1',
                'album': 'Album 2',
                'key': 'A min'
            },
            {
                'id': 'test3',
                'title': 'Track 3',
                'artist': 'Artist 2',
                'album': 'Album 3',
                'key': 'G maj'
            }
        ]
        
        for track in tracks_data:
            self.db.update_track(track['id'], track)
            
        # Filtrar por artista
        tracks = self.db.get_tracks({'artist': 'Artist 1'})
        self.assertEqual(len(tracks), 2)
        
        # Filtrar por clave
        tracks = self.db.get_tracks({'key': 'G maj'})
        self.assertEqual(len(tracks), 2)
        
        # Múltiples filtros
        tracks = self.db.get_tracks({
            'key': 'G maj',
            'artist': 'Artist 2'
        })
        self.assertEqual(len(tracks), 1)

class TestDatabaseFactory(unittest.TestCase):
    """Pruebas para el DatabaseFactory."""
    
    def test_create_sqlite(self):
        """Prueba crear base de datos SQLite."""
        db = DatabaseFactory.create('sqlite', ':memory:')
        self.assertIsInstance(db, SQLiteDatabase)
        
    def test_create_json(self):
        """Prueba crear base de datos JSON."""
        db = DatabaseFactory.create('json', 'test.json')
        self.assertIsInstance(db, JSONDatabase)
        
    def test_invalid_type(self):
        """Prueba tipo de base de datos inválido."""
        with self.assertRaises(ValueError):
            DatabaseFactory.create('invalid', 'test.db')

if __name__ == '__main__':
    unittest.main()
