"""
Pruebas unitarias para los modelos de datos.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.models.base import Base
from src.data.models.music import Artist, Album, Genre, Track

@pytest.fixture
def db_session():
    """Fixture que proporciona una sesión de base de datos en memoria."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()

@pytest.fixture
def sample_artist(db_session):
    """Fixture que crea un artista de ejemplo."""
    artist = Artist(
        name="Test Artist",
        normalized_name="test artist",
        country="US"
    )
    db_session.add(artist)
    db_session.commit()
    return artist

@pytest.fixture
def sample_album(db_session, sample_artist):
    """Fixture que crea un álbum de ejemplo."""
    album = Album(
        title="Test Album",
        normalized_title="test album",
        artist_id=sample_artist.id,
        year=2024,
        total_tracks=10
    )
    db_session.add(album)
    db_session.commit()
    return album

@pytest.fixture
def sample_genre(db_session):
    """Fixture que crea un género de ejemplo."""
    genre = Genre(
        name="Rock",
        normalized_name="rock"
    )
    db_session.add(genre)
    db_session.commit()
    return genre

class TestArtist:
    """Pruebas para el modelo Artist."""
    
    def test_create_artist(self, db_session):
        """Prueba la creación de un artista."""
        artist = Artist(
            name="Test Artist",
            normalized_name="test artist"
        )
        
        db_session.add(artist)
        db_session.commit()
        
        assert artist.id is not None
        assert artist.name == "Test Artist"
        assert artist.normalized_name == "test artist"
        assert artist.created_at is not None
        assert artist.updated_at is not None
    
    def test_artist_repr(self, sample_artist):
        """Prueba la representación string del artista."""
        repr_str = repr(sample_artist)
        assert "Test Artist" in repr_str
        assert str(sample_artist.id) in repr_str
    
    def test_artist_relationships(self, sample_artist, sample_album):
        """Prueba las relaciones del artista."""
        assert len(sample_artist.albums) == 1
        assert sample_artist.albums[0] == sample_album

class TestAlbum:
    """Pruebas para el modelo Album."""
    
    def test_create_album(self, db_session, sample_artist):
        """Prueba la creación de un álbum."""
        album = Album(
            title="Test Album",
            normalized_title="test album",
            artist_id=sample_artist.id,
            year=2024
        )
        
        db_session.add(album)
        db_session.commit()
        
        assert album.id is not None
        assert album.title == "Test Album"
        assert album.artist_id == sample_artist.id
        assert album.year == 2024
    
    def test_album_artist_relationship(self, sample_album, sample_artist):
        """Prueba la relación álbum-artista."""
        assert sample_album.artist == sample_artist
        assert sample_album in sample_artist.albums

class TestGenre:
    """Pruebas para el modelo Genre."""
    
    def test_create_genre(self, db_session):
        """Prueba la creación de un género."""
        genre = Genre(
            name="Jazz",
            normalized_name="jazz"
        )
        
        db_session.add(genre)
        db_session.commit()
        
        assert genre.id is not None
        assert genre.name == "Jazz"
        assert genre.normalized_name == "jazz"
    
    def test_genre_hierarchy(self, db_session):
        """Prueba la jerarquía de géneros."""
        parent_genre = Genre(name="Rock", normalized_name="rock")
        db_session.add(parent_genre)
        db_session.flush()
        
        child_genre = Genre(
            name="Progressive Rock",
            normalized_name="progressive rock",
            parent_id=parent_genre.id
        )
        db_session.add(child_genre)
        db_session.commit()
        
        assert child_genre.parent == parent_genre
        assert child_genre in parent_genre.children

class TestTrack:
    """Pruebas para el modelo Track."""
    
    def test_create_track(self, db_session, sample_album):
        """Prueba la creación de un track."""
        track = Track(
            file_path="/test/path/song.mp3",
            filename="song.mp3",
            title="Test Song",
            normalized_title="test song",
            album_id=sample_album.id,
            duration=180.5,
            track_number=1
        )
        
        db_session.add(track)
        db_session.commit()
        
        assert track.id is not None
        assert track.title == "Test Song"
        assert track.file_path == "/test/path/song.mp3"
        assert track.duration == 180.5
        assert track.album_id == sample_album.id
    
    def test_track_duration_formatted(self, db_session):
        """Prueba el formateo de duración."""
        track = Track(
            file_path="/test/song.mp3",
            filename="song.mp3",
            title="Test Song",
            normalized_title="test song",
            duration=125.0  # 2:05
        )
        
        assert track.duration_formatted == "2:05"
        
        # Sin duración
        track.duration = None
        assert track.duration_formatted == "0:00"
    
    def test_track_relationships(self, db_session, sample_album, sample_artist, sample_genre):
        """Prueba las relaciones del track."""
        track = Track(
            file_path="/test/song.mp3",
            filename="song.mp3",
            title="Test Song",
            normalized_title="test song",
            album_id=sample_album.id
        )
        
        # Asociar artistas y géneros
        track.artists.append(sample_artist)
        track.genres.append(sample_genre)
        
        db_session.add(track)
        db_session.commit()
        
        assert track.album == sample_album
        assert sample_artist in track.artists
        assert sample_genre in track.genres
        assert track.primary_artist == sample_artist
        assert "Test Artist" in track.artist_names
        assert "Rock" in track.genre_names
    
    def test_track_properties(self, db_session, sample_artist):
        """Prueba las propiedades del track."""
        track = Track(
            file_path="/test/song.mp3",
            filename="song.mp3",
            title="Test Song",
            normalized_title="test song"
        )
        track.artists.append(sample_artist)
        
        db_session.add(track)
        db_session.commit()
        
        assert track.primary_artist == sample_artist
        assert track.artist_names == ["Test Artist"]
        
        # Sin artistas
        track.artists.clear()
        db_session.commit()
        assert track.primary_artist is None
        assert track.artist_names == []

class TestModelConstraints:
    """Pruebas para constraints y validaciones de modelos."""
    
    def test_artist_unique_normalized_name(self, db_session):
        """Prueba que los nombres normalizados de artistas sean únicos."""
        artist1 = Artist(name="Test Artist", normalized_name="test artist")
        db_session.add(artist1)
        db_session.commit()
        
        # Intentar crear otro artista con el mismo nombre normalizado
        artist2 = Artist(name="TEST ARTIST", normalized_name="test artist")
        db_session.add(artist2)
        
        with pytest.raises(Exception):  # Debe fallar por constraint único
            db_session.commit()
    
    def test_track_unique_file_path(self, db_session):
        """Prueba que las rutas de archivos sean únicas."""
        track1 = Track(
            file_path="/test/song.mp3",
            filename="song.mp3",
            title="Song 1",
            normalized_title="song 1"
        )
        db_session.add(track1)
        db_session.commit()
        
        # Intentar crear otro track con la misma ruta
        track2 = Track(
            file_path="/test/song.mp3",
            filename="song.mp3",
            title="Song 2", 
            normalized_title="song 2"
        )
        db_session.add(track2)
        
        with pytest.raises(Exception):  # Debe fallar por constraint único
            db_session.commit()

class TestModelTimestamps:
    """Pruebas para los timestamps automáticos."""
    
    def test_created_at_auto_set(self, db_session):
        """Prueba que created_at se establezca automáticamente."""
        artist = Artist(name="Test", normalized_name="test")
        db_session.add(artist)
        db_session.commit()
        
        assert artist.created_at is not None
        assert isinstance(artist.created_at, datetime)
    
    def test_updated_at_auto_update(self, db_session):
        """Prueba que updated_at se actualice automáticamente."""
        artist = Artist(name="Test", normalized_name="test")
        db_session.add(artist)
        db_session.commit()
        
        original_updated = artist.updated_at
        
        # Actualizar el artista
        artist.name = "Updated Test"
        db_session.commit()
        
        assert artist.updated_at > original_updated