#!/usr/bin/env python3
"""
🎵 ANALIZADOR DE FUSIÓN DE GÉNEROS MUSICALES
===========================================

Analiza si combinaciones de géneros múltiples son musicalmente válidas
o resultado de sobre-clasificación/errores de metadatos.

Caso específico: "Heavy Metal; Hip-Hop; Punk Rock"
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import re

@dataclass
class GenreCompatibility:
    """Información de compatibilidad entre géneros."""
    primary_genre: str
    compatible_genres: Set[str]
    fusion_names: Set[str]
    incompatible_genres: Set[str]
    confidence: float

class GenreFusionAnalyzer:
    """Analiza la validez de combinaciones de géneros múltiples."""
    
    # Géneros base y sus características musicales
    GENRE_CHARACTERISTICS = {
        'Heavy Metal': {
            'tempo': 'medium-fast',
            'instruments': ['distorted_guitar', 'bass', 'drums', 'vocals'],
            'vocal_style': ['clean', 'growl', 'scream'],
            'rhythm': 'driving',
            'energy': 'high',
            'origins': ['rock', 'blues']
        },
        'Hip-Hop': {
            'tempo': 'medium',
            'instruments': ['beats', 'bass', 'samples', 'turntables'],
            'vocal_style': ['rap', 'spoken'],
            'rhythm': 'syncopated',
            'energy': 'medium-high',
            'origins': ['funk', 'disco', 'soul']
        },
        'Punk Rock': {
            'tempo': 'fast',
            'instruments': ['guitar', 'bass', 'drums'],
            'vocal_style': ['raw', 'shouted', 'aggressive'],
            'rhythm': 'straight',
            'energy': 'very_high',
            'origins': ['rock', 'garage_rock']
        },
        'Nu Metal': {
            'tempo': 'medium-fast',
            'instruments': ['distorted_guitar', 'bass', 'drums', 'turntables'],
            'vocal_style': ['rap', 'clean', 'scream'],
            'rhythm': 'heavy',
            'energy': 'high',
            'origins': ['metal', 'hip_hop', 'alternative']
        },
        'Rap Metal': {
            'tempo': 'medium-fast',
            'instruments': ['heavy_guitar', 'bass', 'drums'],
            'vocal_style': ['rap', 'aggressive'],
            'rhythm': 'heavy_syncopated',
            'energy': 'very_high',
            'origins': ['metal', 'hip_hop']
        }
    }
    
    # Fusiones conocidas y válidas
    KNOWN_FUSIONS = {
        frozenset(['Heavy Metal', 'Hip-Hop']): {
            'fusion_genre': 'Rap Metal',
            'examples': ['Rage Against the Machine', 'Limp Bizkit', 'Body Count'],
            'validity': 'high',
            'characteristics': 'Metal guitars + rap vocals'
        },
        frozenset(['Heavy Metal', 'Punk Rock']): {
            'fusion_genre': 'Crossover Thrash',
            'examples': ['Suicidal Tendencies', 'D.R.I.', 'Municipal Waste'],
            'validity': 'high',
            'characteristics': 'Metal power + punk attitude'
        },
        frozenset(['Hip-Hop', 'Punk Rock']): {
            'fusion_genre': 'Punk Rap',
            'examples': ['Beastie Boys', 'Scroobius Pip', 'The Transplants'],
            'validity': 'medium',
            'characteristics': 'Punk energy + rap vocals'
        },
        frozenset(['Heavy Metal', 'Hip-Hop', 'Punk Rock']): {
            'fusion_genre': 'Nu Metal / Rap Metal Hybrid',
            'examples': ['Rage Against the Machine', 'Linkin Park (early)', 'P.O.D.'],
            'validity': 'medium-high',
            'characteristics': 'Triple fusion - metal/punk guitars + rap vocals'
        },
        frozenset(['Heavy Metal', 'Alternative Rock']): {
            'fusion_genre': 'Alternative Metal',
            'examples': ['Tool', 'Alice in Chains', 'Soundgarden'],
            'validity': 'very_high',
            'characteristics': 'Metal + alternative sensibilities'
        }
    }
    
    # Incompatibilidades conocidas (géneros que raramente se fusionan exitosamente)
    INCOMPATIBLE_PAIRS = {
        frozenset(['Classical', 'Death Metal']): 'Orchestral elements vs extreme aggression',
        frozenset(['Country', 'Black Metal']): 'Rural vs extreme underground',
        frozenset(['Ambient', 'Hardcore Punk']): 'Atmospheric vs intense energy',
        # Pero nota: siempre hay excepciones en música!
    }
    
    @classmethod
    def analyze_genre_combination(cls, genres: List[str]) -> Dict:
        """
        Analiza si una combinación de géneros es musicalmente válida.
        
        Args:
            genres: Lista de géneros a analizar
            
        Returns:
            Diccionario con análisis detallado
        """
        if not genres or len(genres) < 2:
            return {'validity': 'single_genre', 'analysis': 'Un solo género o lista vacía'}
        
        # Normalizar nombres de géneros
        normalized_genres = [cls._normalize_genre_name(g) for g in genres]
        genre_set = frozenset(normalized_genres)
        
        analysis = {
            'original_genres': genres,
            'normalized_genres': normalized_genres,
            'combination_type': cls._classify_combination(normalized_genres),
            'known_fusion': None,
            'validity_score': 0.0,
            'validity_level': 'unknown',
            'musical_analysis': {},
            'recommendations': [],
            'examples': [],
            'potential_issues': []
        }
        
        # Verificar si es una fusión conocida
        if genre_set in cls.KNOWN_FUSIONS:
            fusion_info = cls.KNOWN_FUSIONS[genre_set]
            analysis['known_fusion'] = fusion_info
            analysis['validity_level'] = fusion_info['validity']
            analysis['examples'] = fusion_info['examples']
            analysis['validity_score'] = cls._validity_to_score(fusion_info['validity'])
        
        # Análisis musical detallado
        analysis['musical_analysis'] = cls._analyze_musical_compatibility(normalized_genres)
        
        # Determinar nivel de validez si no es fusión conocida
        if not analysis['known_fusion']:
            analysis['validity_score'] = cls._calculate_compatibility_score(normalized_genres)
            analysis['validity_level'] = cls._score_to_validity(analysis['validity_score'])
        
        # Generar recomendaciones
        analysis['recommendations'] = cls._generate_recommendations(analysis)
        
        # Detectar posibles problemas
        analysis['potential_issues'] = cls._detect_potential_issues(normalized_genres)
        
        return analysis
    
    @classmethod
    def _normalize_genre_name(cls, genre: str) -> str:
        """Normaliza nombres de géneros para análisis."""
        # Mapeo de variaciones comunes
        mappings = {
            'metal': 'Heavy Metal',
            'rap': 'Hip-Hop',
            'punk': 'Punk Rock',
            'hip hop': 'Hip-Hop',
            'hiphop': 'Hip-Hop',
            'heavy metal': 'Heavy Metal',
            'punk rock': 'Punk Rock'
        }
        
        normalized = genre.strip()
        lower_genre = normalized.lower()
        
        return mappings.get(lower_genre, normalized)
    
    @classmethod
    def _classify_combination(cls, genres: List[str]) -> str:
        """Clasifica el tipo de combinación de géneros."""
        if len(genres) == 2:
            return 'dual_fusion'
        elif len(genres) == 3:
            return 'triple_fusion'
        elif len(genres) > 3:
            return 'multi_fusion'
        else:
            return 'single'
    
    @classmethod
    def _analyze_musical_compatibility(cls, genres: List[str]) -> Dict:
        """Analiza la compatibilidad musical entre géneros."""
        compatibility = {
            'tempo_compatibility': 'unknown',
            'instrument_overlap': [],
            'vocal_compatibility': 'unknown',
            'energy_match': 'unknown',
            'rhythm_compatibility': 'unknown',
            'shared_origins': []
        }
        
        # Obtener características de cada género
        genre_chars = []
        for genre in genres:
            if genre in cls.GENRE_CHARACTERISTICS:
                genre_chars.append(cls.GENRE_CHARACTERISTICS[genre])
        
        if not genre_chars:
            return compatibility
        
        # Analizar solapamiento de instrumentos
        all_instruments = set()
        for chars in genre_chars:
            all_instruments.update(chars.get('instruments', []))
        
        # Instrumentos compartidos
        shared_instruments = set(genre_chars[0].get('instruments', []))
        for chars in genre_chars[1:]:
            shared_instruments &= set(chars.get('instruments', []))
        
        compatibility['instrument_overlap'] = list(shared_instruments)
        
        # Analizar orígenes compartidos
        shared_origins = set(genre_chars[0].get('origins', []))
        for chars in genre_chars[1:]:
            shared_origins &= set(chars.get('origins', []))
        
        compatibility['shared_origins'] = list(shared_origins)
        
        return compatibility
    
    @classmethod
    def _calculate_compatibility_score(cls, genres: List[str]) -> float:
        """Calcula un score de compatibilidad entre géneros."""
        if len(genres) < 2:
            return 1.0
        
        # Score base por número de géneros (más géneros = menos probable)
        base_score = max(0.1, 1.0 - (len(genres) - 2) * 0.2)
        
        # Bonificaciones por características compartidas
        musical_analysis = cls._analyze_musical_compatibility(genres)
        
        # Bonus por instrumentos compartidos
        instrument_bonus = len(musical_analysis['instrument_overlap']) * 0.15
        
        # Bonus por orígenes compartidos
        origin_bonus = len(musical_analysis['shared_origins']) * 0.2
        
        # Penalización por géneros muy diferentes
        penalty = 0.0
        genre_set = frozenset(genres)
        for incompatible_pair in cls.INCOMPATIBLE_PAIRS:
            if incompatible_pair.issubset(genre_set):
                penalty += 0.3
        
        final_score = min(1.0, max(0.0, base_score + instrument_bonus + origin_bonus - penalty))
        return final_score
    
    @classmethod
    def _validity_to_score(cls, validity: str) -> float:
        """Convierte nivel de validez textual a score numérico."""
        mapping = {
            'very_high': 0.95,
            'high': 0.8,
            'medium-high': 0.7,
            'medium': 0.5,
            'medium-low': 0.3,
            'low': 0.2,
            'very_low': 0.1
        }
        return mapping.get(validity, 0.5)
    
    @classmethod
    def _score_to_validity(cls, score: float) -> str:
        """Convierte score numérico a nivel de validez textual."""
        if score >= 0.9:
            return 'very_high'
        elif score >= 0.7:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        elif score >= 0.3:
            return 'low'
        else:
            return 'very_low'
    
    @classmethod
    def _generate_recommendations(cls, analysis: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []
        
        validity_level = analysis['validity_level']
        
        if validity_level in ['high', 'very_high']:
            recommendations.append("✅ Combinación musicalmente válida - mantener todos los géneros")
        elif validity_level == 'medium':
            recommendations.append("⚠️ Fusión posible pero inusual - considerar género híbrido específico")
        else:
            recommendations.append("❌ Combinación poco probable - verificar metadatos")
            recommendations.append("🔍 Sugerir usar género híbrido más específico")
        
        # Recomendaciones específicas basadas en fusiones conocidas
        if analysis['known_fusion']:
            fusion_genre = analysis['known_fusion']['fusion_genre']
            recommendations.append(f"💡 Considerar usar '{fusion_genre}' como género único")
        
        return recommendations
    
    @classmethod
    def _detect_potential_issues(cls, genres: List[str]) -> List[str]:
        """Detecta posibles problemas en la combinación."""
        issues = []
        
        # Demasiados géneros
        if len(genres) > 4:
            issues.append("Demasiados géneros - posible sobre-clasificación")
        
        # Géneros muy específicos juntos
        specific_genres = ['Death Metal', 'Black Metal', 'Thrash Metal', 'Doom Metal']
        if any(g in specific_genres for g in genres) and len(genres) > 2:
            issues.append("Subgéneros específicos mezclados - verificar precisión")
        
        # Géneros de diferentes eras
        old_genres = ['Blues', 'Jazz', 'Classical', 'Folk']
        modern_genres = ['Electronic', 'Dubstep', 'Trap', 'Future Bass']
        
        has_old = any(g in old_genres for g in genres)
        has_modern = any(g in modern_genres for g in genres)
        
        if has_old and has_modern:
            issues.append("Géneros de eras muy diferentes - posible fusión experimental")
        
        return issues

def test_specific_case():
    """Prueba el caso específico: Heavy Metal; Hip-Hop; Punk Rock"""
    print("🎵 ANÁLISIS DE FUSIÓN: Heavy Metal; Hip-Hop; Punk Rock")
    print("=" * 60)
    
    test_genres = ['Heavy Metal', 'Hip-Hop', 'Punk Rock']
    
    analyzer = GenreFusionAnalyzer()
    result = analyzer.analyze_genre_combination(test_genres)
    
    print(f"📋 Géneros originales: {result['original_genres']}")
    print(f"🔧 Géneros normalizados: {result['normalized_genres']}")
    print(f"📊 Tipo de combinación: {result['combination_type']}")
    print(f"⭐ Score de validez: {result['validity_score']:.2f}")
    print(f"✅ Nivel de validez: {result['validity_level']}")
    
    if result['known_fusion']:
        fusion = result['known_fusion']
        print(f"\n🎯 FUSIÓN CONOCIDA:")
        print(f"   Género híbrido: {fusion['fusion_genre']}")
        print(f"   Características: {fusion['characteristics']}")
        print(f"   Ejemplos: {', '.join(fusion['examples'])}")
    
    print(f"\n🎼 ANÁLISIS MUSICAL:")
    musical = result['musical_analysis']
    print(f"   Instrumentos compartidos: {musical['instrument_overlap']}")
    print(f"   Orígenes compartidos: {musical['shared_origins']}")
    
    print(f"\n💡 RECOMENDACIONES:")
    for rec in result['recommendations']:
        print(f"   {rec}")
    
    if result['potential_issues']:
        print(f"\n⚠️ POSIBLES PROBLEMAS:")
        for issue in result['potential_issues']:
            print(f"   {issue}")

def test_multiple_cases():
    """Prueba múltiples casos de fusión."""
    print("\n\n🧪 PRUEBAS MÚLTIPLES DE FUSIÓN")
    print("=" * 40)
    
    test_cases = [
        ['Heavy Metal', 'Hip-Hop'],
        ['Hip-Hop', 'Punk Rock'],
        ['Classical', 'Electronic'],
        ['Jazz', 'Hip-Hop'],
        ['Country', 'Death Metal'],
        ['Pop', 'Rock', 'Electronic'],
        ['Ambient', 'Hardcore Punk']
    ]
    
    analyzer = GenreFusionAnalyzer()
    
    for i, genres in enumerate(test_cases, 1):
        result = analyzer.analyze_genre_combination(genres)
        print(f"\n{i}. {' + '.join(genres)}")
        print(f"   Validez: {result['validity_level']} ({result['validity_score']:.2f})")
        
        if result['known_fusion']:
            print(f"   Fusión: {result['known_fusion']['fusion_genre']}")
        
        if result['recommendations']:
            print(f"   Rec: {result['recommendations'][0]}")

if __name__ == "__main__":
    test_specific_case()
    test_multiple_cases() 