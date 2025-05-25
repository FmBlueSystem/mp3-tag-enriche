"""
Tests para el servicio de música
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from nueva_biblioteca.src.services.music_service import MusicService
from nueva_biblioteca.src.core.database.music_database import TrackMetadata

@pytest.fixture
def mock_database():
    """Fixture que retorna una base de datos simulada."""
    db = MagicMock()
    db.connect.return_value = True
    return db

@pytest.fixture
def music_service(mock_database):
    """Fixture que retorna un servicio de música con base de datos simulada."""
    with patch('nueva_biblioteca.src.services.music_service.DatabaseFactory.create') as mock_create:
        mock_create.return_value = mock_database
        service = MusicService()
        return service

def test_init_success(mock_database):
    """Prueba inicialización exitosa del servicio."""
    with patch('nueva_biblioteca.src.services.music_service.DatabaseFactory.create') as mock_create:
        mock_create.return_value = mock_database
        service = MusicService()
        assert service.db == mock_database
        mock_database.connect.assert_called_once()

def test_init_failure(mock_database):
    """Prueba inicialización fallida por error de conexión."""
    mock_database.connect.return_value = False
    with patch('nueva_biblioteca.src.services.music_service.DatabaseFactory.create') as mock_create:
        mock_create.return_value = mock_database
        with pytest.raises(RuntimeError):
            MusicService()

def test_add_track_success(music_service, mock_database):
    """Prueba añadir track exitosamente."""
    metadata = {
        'id': 'test123',
        'title': 'Test Song',
        'artist': 'Test Artist',
        'album': 'Test Album'
    }
    mock_database.update_track.return_value = True
    
    track_id = music_service.add_track(metadata)
    assert track_id == 'test123'
    mock_database.update_track.assert_called_with('test123', metadata)

def test_add_track_failure(music_service, mock_database):
    """Prueba añadir track con error."""
    metadata = {
        'id': 'test123',
        'title': 'Test Song',
        'artist': 'Test Artist',
        'album': 'Test Album'
    }
    mock_database.update_track.return_value = False
    
    track_id = music_service.add_track(metadata)
    assert track_id is None

def test_get_track_success(music_service, mock_database):
    """Prueba obtener track exitosamente."""
    track = TrackMetadata(
        id='test123',
        title='Test Song',
        artist='Test Artist',
        album='Test Album'
    )
    mock_database.get_track.return_value = track
    
    result = music_service.get_track('test123')
    assert result is not None
    assert result['id'] == 'test123'
    assert result['title'] == 'Test Song'
    mock_database.get_track.assert_called_with('test123')

def test_get_track_not_found(music_service, mock_database):
    """Prueba obtener track inexistente."""
    mock_database.get_track.return_value = None
    result = music_service.get_track('nonexistent')
    assert result is None

def test_search_tracks_by_query(music_service, mock_database):
    """Prueba búsqueda por texto."""
    tracks = [
        TrackMetadata(id='1', title='Test Song', artist='Artist', album='Album'),
        TrackMetadata(id='2', title='Another Song', artist='Test Artist', album='Album'),
        TrackMetadata(id='3', title='Song', artist='Artist', album='Test Album')
    ]
    mock_database.get_tracks.return_value = tracks
    
    results = music_service.search_tracks(query='test')
    assert len(results) == 3
    assert any(r['title'] == 'Test Song' for r in results)
    assert any(r['artist'] == 'Test Artist' for r in results)
    assert any(r['album'] == 'Test Album' for r in results)

def test_search_tracks_by_filters(music_service, mock_database):
    """Prueba búsqueda por filtros."""
    filters = {'genre': 'Rock', 'year': 2023}
    music_service.search_tracks(filters=filters)
    mock_database.get_tracks.assert_called_with(filters=filters)

def test_get_statistics(music_service, mock_database):
    """Prueba obtener estadísticas."""
    tracks = [
        TrackMetadata(
            id='1',
            title='Song 1',
            artist='Artist 1',
            album='Album 1',
            genre='Rock',
            year=2022
        ),
        TrackMetadata(
            id='2',
            title='Song 2',
            artist='Artist 2',
            album='Album 2',
            genre='Pop',
            year=2023
        )
    ]
    mock_database.get_tracks.return_value = tracks
    
    stats = music_service.get_statistics()
    assert stats['total_tracks'] == 2
    assert stats['total_genres'] == 2
    assert stats['total_artists'] == 2
    assert stats['total_albums'] == 2
    assert stats['year_range'] == [2022, 2023]
    assert sorted(stats['genres']) == ['Pop', 'Rock']

@patch('nueva_biblioteca.src.services.music_service.MetadataExtractor')
def test_import_tracks_success(mock_extractor_class, music_service, tmp_path):
    """Prueba importación exitosa de tracks."""
    # Configurar directorio de prueba
    (tmp_path / "test1.mp3").touch()
    (tmp_path / "test2.mp3").touch()
    
    # Configurar mock del extractor
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor.scan_directory.return_value = {
        'total': 2,
        'success': 2,
        'failed': 0,
        'errors': [],
        'tracks': [
            {'id': 'test1', 'title': 'Song 1', 'artist': 'Artist 1', 'album': 'Album 1'},
            {'id': 'test2', 'title': 'Song 2', 'artist': 'Artist 2', 'album': 'Album 2'}
        ]
    }
    
    # Configurar mock de la base de datos
    music_service.db.update_track.return_value = True
    
    # Ejecutar importación
    results = music_service.import_tracks(str(tmp_path))
    
    # Verificar resultados
    assert results['total'] == 2
    assert results['success'] == 2
    assert results['failed'] == 0
    assert len(results['imported_tracks']) == 2
    music_service.db.update_track.call_count == 2

@patch('nueva_biblioteca.src.services.music_service.MetadataExtractor')
def test_import_tracks_with_errors(mock_extractor_class, music_service, tmp_path):
    """Prueba importación con errores."""
    # Configurar mock del extractor
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    mock_extractor.scan_directory.return_value = {
        'total': 2,
        'success': 1,
        'failed': 1,
        'errors': ['Error procesando archivo'],
        'tracks': [
            {'id': 'test1', 'title': 'Song 1', 'artist': 'Artist 1', 'album': 'Album 1'}
        ]
    }
    
    # Configurar mock de la base de datos para fallar en la segunda actualización
    music_service.db.update_track.side_effect = [True, False]
    
    # Ejecutar importación
    results = music_service.import_tracks(str(tmp_path))
    
    # Verificar resultados
    assert results['total'] == 2
    assert results['success'] == 1
    assert results['failed'] == 1
    assert len(results['imported_tracks']) == 1
    assert len(results['errors']) == 1

def test_export_playlist_success(music_service, mock_database):
    """Prueba exportación exitosa de playlist."""
    tracks = [
        TrackMetadata(
            id='1',
            title='Song 1',
            artist='Artist 1',
            album='Album 1',
            path='/music/song1.mp3'
        ),
        TrackMetadata(
            id='2',
            title='Song 2',
            artist='Artist 2',
            album='Album 2',
            path='/music/song2.mp3'
        )
    ]
    mock_database.get_track.side_effect = tracks
    
    content = music_service.export_playlist(['1', '2'])
    assert content is not None
    assert '#EXTM3U' in content
    assert 'Artist 1 - Song 1' in content
    assert 'Artist 2 - Song 2' in content
    assert '/music/song1.mp3' in content
    assert '/music/song2.mp3' in content

def test_export_playlist_invalid_format(music_service):
    """Prueba exportación con formato inválido."""
    content = music_service.export_playlist(['1'], format='invalid')
    assert content is None

def test_export_playlist_missing_tracks(music_service, mock_database):
    """Prueba exportación con tracks faltantes."""
    mock_database.get_track.return_value = None
    content = music_service.export_playlist(['1'])
    assert content == '#EXTM3U'
