#!/usr/bin/env python3
"""
🎵 GENRE NORMALIZER - NUEVA BIBLIOTECA v2.0
==========================================
Normalización y categorización de géneros musicales
"""

import re
import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GenreMapping:
    """Mapeo de género con información adicional."""
    canonical_name: str
    aliases: Set[str]
    category: str
    confidence: float = 1.0

class GenreNormalizer:
    """
    Normalizador de géneros musicales que convierte variaciones
    de nombres de géneros a formas canónicas estandarizadas.
    """
    
    # Mapeos de géneros principales
    GENRE_MAPPINGS = {
        # Rock y subgéneros
        'rock': GenreMapping(
            canonical_name='Rock',
            aliases={'rock', 'rock music', 'rock and roll', 'rock & roll', 'rock n roll'},
            category='Rock'
        ),
        'alternative_rock': GenreMapping(
            canonical_name='Alternative Rock',
            aliases={'alternative rock', 'alt rock', 'alternative', 'indie rock', 'indie'},
            category='Rock'
        ),
        'hard_rock': GenreMapping(
            canonical_name='Hard Rock',
            aliases={'hard rock', 'hardrock'},
            category='Rock'
        ),
        'punk_rock': GenreMapping(
            canonical_name='Punk Rock',
            aliases={'punk rock', 'punk', 'punk music'},
            category='Rock'
        ),
        'progressive_rock': GenreMapping(
            canonical_name='Progressive Rock',
            aliases={'progressive rock', 'prog rock', 'prog', 'progressive'},
            category='Rock'
        ),
        'classic_rock': GenreMapping(
            canonical_name='Classic Rock',
            aliases={'classic rock', 'classical rock'},
            category='Rock'
        ),
        
        # Pop y subgéneros
        'pop': GenreMapping(
            canonical_name='Pop',
            aliases={'pop', 'pop music', 'popular music'},
            category='Pop'
        ),
        'pop_rock': GenreMapping(
            canonical_name='Pop Rock',
            aliases={'pop rock', 'pop/rock', 'pop-rock'},
            category='Pop'
        ),
        'synthpop': GenreMapping(
            canonical_name='Synthpop',
            aliases={'synthpop', 'synth-pop', 'synth pop', 'electropop'},
            category='Pop'
        ),
        
        # Electronic y subgéneros
        'electronic': GenreMapping(
            canonical_name='Electronic',
            aliases={'electronic', 'electronic music', 'electronica'},
            category='Electronic'
        ),
        'house': GenreMapping(
            canonical_name='House',
            aliases={'house', 'house music'},
            category='Electronic'
        ),
        'techno': GenreMapping(
            canonical_name='Techno',
            aliases={'techno', 'techno music'},
            category='Electronic'
        ),
        'ambient': GenreMapping(
            canonical_name='Ambient',
            aliases={'ambient', 'ambient music'},
            category='Electronic'
        ),
        'edm': GenreMapping(
            canonical_name='EDM',
            aliases={'edm', 'electronic dance music', 'dance music'},
            category='Electronic'
        ),
        
        # Hip Hop y subgéneros
        'hip_hop': GenreMapping(
            canonical_name='Hip Hop',
            aliases={'hip hop', 'hip-hop', 'hiphop', 'rap', 'rap music'},
            category='Hip Hop'
        ),
        'trap': GenreMapping(
            canonical_name='Trap',
            aliases={'trap', 'trap music'},
            category='Hip Hop'
        ),
        
        # Jazz y subgéneros
        'jazz': GenreMapping(
            canonical_name='Jazz',
            aliases={'jazz', 'jazz music'},
            category='Jazz'
        ),
        'smooth_jazz': GenreMapping(
            canonical_name='Smooth Jazz',
            aliases={'smooth jazz', 'contemporary jazz'},
            category='Jazz'
        ),
        'bebop': GenreMapping(
            canonical_name='Bebop',
            aliases={'bebop', 'bop'},
            category='Jazz'
        ),
        
        # Blues y subgéneros
        'blues': GenreMapping(
            canonical_name='Blues',
            aliases={'blues', 'blues music'},
            category='Blues'
        ),
        'electric_blues': GenreMapping(
            canonical_name='Electric Blues',
            aliases={'electric blues', 'chicago blues'},
            category='Blues'
        ),
        
        # Country y subgéneros
        'country': GenreMapping(
            canonical_name='Country',
            aliases={'country', 'country music'},
            category='Country'
        ),
        'country_rock': GenreMapping(
            canonical_name='Country Rock',
            aliases={'country rock', 'country-rock'},
            category='Country'
        ),
        
        # Folk y subgéneros
        'folk': GenreMapping(
            canonical_name='Folk',
            aliases={'folk', 'folk music', 'traditional folk'},
            category='Folk'
        ),
        'folk_rock': GenreMapping(
            canonical_name='Folk Rock',
            aliases={'folk rock', 'folk-rock'},
            category='Folk'
        ),
        
        # Metal y subgéneros
        'metal': GenreMapping(
            canonical_name='Metal',
            aliases={'metal', 'heavy metal', 'metal music'},
            category='Metal'
        ),
        'death_metal': GenreMapping(
            canonical_name='Death Metal',
            aliases={'death metal'},
            category='Metal'
        ),
        'black_metal': GenreMapping(
            canonical_name='Black Metal',
            aliases={'black metal'},
            category='Metal'
        ),
        
        # R&B y Soul
        'rnb': GenreMapping(
            canonical_name='R&B',
            aliases={'r&b', 'rnb', 'rhythm and blues', 'rhythm & blues'},
            category='R&B'
        ),
        'soul': GenreMapping(
            canonical_name='Soul',
            aliases={'soul', 'soul music'},
            category='R&B'
        ),
        
        # Reggae
        'reggae': GenreMapping(
            canonical_name='Reggae',
            aliases={'reggae', 'reggae music'},
            category='Reggae'
        ),
        
        # Classical
        'classical': GenreMapping(
            canonical_name='Classical',
            aliases={'classical', 'classical music', 'orchestral'},
            category='Classical'
        ),
        
        # World Music
        'world': GenreMapping(
            canonical_name='World Music',
            aliases={'world music', 'world', 'ethnic'},
            category='World'
        ),
        
        # Instrumental
        'instrumental': GenreMapping(
            canonical_name='Instrumental',
            aliases={'instrumental', 'instrumental music'},
            category='Instrumental'
        )
    }
    
    # Patrones de limpieza
    CLEANUP_PATTERNS = [
        (r'\s+', ' '),  # Múltiples espacios a uno solo
        (r'[^\w\s&-]', ''),  # Remover caracteres especiales excepto &, -, espacios
        (r'\b(music|genre)\b', ''),  # Remover palabras comunes
        (r'\s*&\s*', ' & '),  # Normalizar &
        (r'\s*-\s*', '-'),  # Normalizar -
    ]
    
    @classmethod
    def normalize(cls, genre: str) -> Tuple[str, float]:
        """
        Normalizar un género musical a su forma canónica.
        
        Args:
            genre: Nombre del género a normalizar
            
        Returns:
            Tupla con (nombre_normalizado, confianza)
        """
        if not genre or not isinstance(genre, str):
            return 'Unknown', 0.0
            
        # Limpiar y normalizar el input
        cleaned = cls._clean_genre_name(genre)
        
        if not cleaned:
            return 'Unknown', 0.0
            
        # Buscar coincidencia exacta
        exact_match = cls._find_exact_match(cleaned)
        if exact_match:
            return exact_match.canonical_name, exact_match.confidence
            
        # Buscar coincidencia parcial
        partial_match = cls._find_partial_match(cleaned)
        if partial_match:
            return partial_match.canonical_name, partial_match.confidence * 0.8
            
        # Buscar por palabras clave
        keyword_match = cls._find_keyword_match(cleaned)
        if keyword_match:
            return keyword_match.canonical_name, keyword_match.confidence * 0.6
            
        # Si no se encuentra coincidencia, devolver capitalizado
        return cls._capitalize_genre(cleaned), 0.3
        
    @classmethod
    def _clean_genre_name(cls, genre: str) -> str:
        """Limpiar y normalizar el nombre del género."""
        cleaned = genre.lower().strip()
        
        # Aplicar patrones de limpieza
        for pattern, replacement in cls.CLEANUP_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned)
            
        return cleaned.strip()
        
    @classmethod
    def _find_exact_match(cls, cleaned_genre: str) -> Optional[GenreMapping]:
        """Buscar coincidencia exacta en aliases."""
        for mapping in cls.GENRE_MAPPINGS.values():
            if cleaned_genre in mapping.aliases:
                return mapping
        return None
        
    @classmethod
    def _find_partial_match(cls, cleaned_genre: str) -> Optional[GenreMapping]:
        """Buscar coincidencia parcial en aliases."""
        for mapping in cls.GENRE_MAPPINGS.values():
            for alias in mapping.aliases:
                if cleaned_genre in alias or alias in cleaned_genre:
                    return mapping
        return None
        
    @classmethod
    def _find_keyword_match(cls, cleaned_genre: str) -> Optional[GenreMapping]:
        """Buscar por palabras clave en el género."""
        words = set(cleaned_genre.split())
        
        best_match = None
        best_score = 0
        
        for mapping in cls.GENRE_MAPPINGS.values():
            for alias in mapping.aliases:
                alias_words = set(alias.split())
                common_words = words.intersection(alias_words)
                
                if common_words:
                    score = len(common_words) / len(alias_words)
                    if score > best_score:
                        best_score = score
                        best_match = mapping
                        
        return best_match if best_score > 0.5 else None
        
    @classmethod
    def _capitalize_genre(cls, genre: str) -> str:
        """Capitalizar apropiadamente un género."""
        # Palabras que no se capitalizan (excepto al inicio)
        lowercase_words = {'and', 'or', 'of', 'the', 'in', 'on', 'at', 'to', 'for', 'with'}
        
        words = genre.split()
        capitalized = []
        
        for i, word in enumerate(words):
            if i == 0 or word not in lowercase_words:
                capitalized.append(word.capitalize())
            else:
                capitalized.append(word)
                
        return ' '.join(capitalized)
        
    @classmethod
    def get_genre_category(cls, genre: str) -> str:
        """
        Obtener la categoría de un género.
        
        Args:
            genre: Nombre del género
            
        Returns:
            Categoría del género
        """
        normalized, _ = cls.normalize(genre)
        
        for mapping in cls.GENRE_MAPPINGS.values():
            if mapping.canonical_name == normalized:
                return mapping.category
                
        return 'Other'
        
    @classmethod
    def get_all_genres(cls) -> List[str]:
        """
        Obtener lista de todos los géneros canónicos.
        
        Returns:
            Lista de nombres de géneros canónicos
        """
        return [mapping.canonical_name for mapping in cls.GENRE_MAPPINGS.values()]
        
    @classmethod
    def get_genres_by_category(cls, category: str) -> List[str]:
        """
        Obtener géneros por categoría.
        
        Args:
            category: Categoría a filtrar
            
        Returns:
            Lista de géneros en la categoría
        """
        return [
            mapping.canonical_name 
            for mapping in cls.GENRE_MAPPINGS.values()
            if mapping.category == category
        ]
        
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """
        Obtener lista de todas las categorías.
        
        Returns:
            Lista de categorías únicas
        """
        categories = {mapping.category for mapping in cls.GENRE_MAPPINGS.values()}
        return sorted(list(categories))
        
    @classmethod
    def normalize_genre_list(cls, genres: List[str]) -> Dict[str, float]:
        """
        Normalizar una lista de géneros y combinar duplicados.
        
        Args:
            genres: Lista de géneros a normalizar
            
        Returns:
            Diccionario con géneros normalizados y confianza máxima
        """
        normalized_genres = {}
        
        for genre in genres:
            if not genre:
                continue
                
            norm_genre, confidence = cls.normalize(genre)
            
            if norm_genre in normalized_genres:
                # Mantener la confianza más alta
                normalized_genres[norm_genre] = max(
                    normalized_genres[norm_genre], 
                    confidence
                )
            else:
                normalized_genres[norm_genre] = confidence
                
        return normalized_genres
        
    @classmethod
    def add_custom_mapping(cls, 
                          canonical_name: str,
                          aliases: Set[str],
                          category: str,
                          confidence: float = 1.0) -> None:
        """
        Añadir un mapeo personalizado de género.
        
        Args:
            canonical_name: Nombre canónico del género
            aliases: Set de aliases para el género
            category: Categoría del género
            confidence: Nivel de confianza (0.0-1.0)
        """
        key = canonical_name.lower().replace(' ', '_')
        cls.GENRE_MAPPINGS[key] = GenreMapping(
            canonical_name=canonical_name,
            aliases=aliases,
            category=category,
            confidence=confidence
        )
        
        logger.info(f"Added custom genre mapping: {canonical_name} -> {category}")
        
    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """
        Obtener estadísticas del normalizador.
        
        Returns:
            Diccionario con estadísticas
        """
        total_mappings = len(cls.GENRE_MAPPINGS)
        total_aliases = sum(len(m.aliases) for m in cls.GENRE_MAPPINGS.values())
        categories = cls.get_all_categories()
        
        category_counts = {}
        for category in categories:
            category_counts[category] = len(cls.get_genres_by_category(category))
            
        return {
            'total_mappings': total_mappings,
            'total_aliases': total_aliases,
            'total_categories': len(categories),
            'category_counts': category_counts
        }
