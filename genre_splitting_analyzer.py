#!/usr/bin/env python3
"""
Analizador y solucionador para problemas de géneros múltiples con separadores inconsistentes.
Casos problemáticos como: "R&B; Pop/Rock; Pop"
"""

import re
from typing import List, Dict, Set, Tuple
from src.core.genre_normalizer import GenreNormalizer

class MultiGenreSplitter:
    """Maneja la división y normalización de géneros múltiples con separadores inconsistentes."""
    
    # Separadores comunes para géneros múltiples
    SEPARATORS = [
        ';',      # "R&B; Pop; Rock"
        ',',      # "R&B, Pop, Rock"
        '/',      # Solo para casos específicos como "Pop/Rock" vs "Pop / Rock"
        '|',      # "R&B | Pop | Rock"
        '+',      # "R&B + Pop"
        ' and ',  # "R&B and Pop"
        ' & ',    # Solo cuando no es parte del género (R&B vs Pop & Rock)
        '\n',     # Líneas separadas
        '\t',     # Tabs
    ]
    
    # Géneros que contienen separadores que NO deben dividirse
    PROTECTED_GENRES = {
        'R&B', 'Rock & Roll', 'Drum & Bass', 'Contemporary R&B', 
        'Pop/Rock', 'Blues Rock', 'Folk Rock', 'Blues & Soul',
        'Hip-Hop', 'Electronic Dance Music', 'UK Garage',
        'Country & Western', 'Rhythm & Blues'
    }
    
    @classmethod
    def split_genres(cls, genre_string: str) -> List[str]:
        """
        Divide una cadena de géneros múltiples respetando géneros protegidos.
        
        Args:
            genre_string: Cadena con géneros múltiples como "R&B; Pop/Rock; Pop"
            
        Returns:
            Lista de géneros individuales
        """
        if not genre_string or not genre_string.strip():
            return []
        
        # Limpiar la cadena inicial
        cleaned = genre_string.strip()
        
        # Proteger géneros conocidos que contienen separadores
        protected_replacements = {}
        temp_string = cleaned
        
        for i, protected_genre in enumerate(cls.PROTECTED_GENRES):
            if protected_genre.lower() in cleaned.lower():
                placeholder = f"__PROTECTED_{i}__"
                # Buscar coincidencias case-insensitive
                pattern = re.escape(protected_genre)
                temp_string = re.sub(pattern, placeholder, temp_string, flags=re.IGNORECASE)
                protected_replacements[placeholder] = protected_genre
        
        # Dividir por separadores
        genres = [temp_string]
        
        for separator in cls.SEPARATORS:
            new_genres = []
            for genre in genres:
                if separator in genre:
                    # Manejar caso especial de "/" para evitar romper "Pop/Rock"
                    if separator == '/':
                        # Solo dividir si no es un género compuesto conocido
                        parts = genre.split('/')
                        if len(parts) == 2:
                            # Verificar si es un género compuesto válido
                            combined = parts[0].strip() + '/' + parts[1].strip()
                            if any(protected in combined for protected in protected_replacements.values()):
                                new_genres.append(genre)
                                continue
                            # Si ambas partes son géneros válidos independientes, dividir
                            if cls._is_likely_genre(parts[0]) and cls._is_likely_genre(parts[1]):
                                new_genres.extend([p.strip() for p in parts if p.strip()])
                            else:
                                new_genres.append(genre)
                        else:
                            new_genres.append(genre)
                    else:
                        new_genres.extend([p.strip() for p in genre.split(separator) if p.strip()])
                else:
                    new_genres.append(genre)
            genres = new_genres
        
        # Restaurar géneros protegidos
        final_genres = []
        for genre in genres:
            restored_genre = genre
            for placeholder, original in protected_replacements.items():
                restored_genre = restored_genre.replace(placeholder, original)
            if restored_genre.strip():
                final_genres.append(restored_genre.strip())
        
        return final_genres
    
    @classmethod
    def _is_likely_genre(cls, text: str) -> bool:
        """Determina si un texto es probablemente un nombre de género."""
        if not text or len(text.strip()) < 2:
            return False
        
        # Verificar si está en géneros conocidos
        normalized, confidence = GenreNormalizer.normalize(text.strip())
        return confidence > 0.6
    
    @classmethod
    def normalize_multi_genre(cls, genre_string: str, max_genres: int = 3) -> Dict[str, float]:
        """
        Normaliza una cadena con múltiples géneros y devuelve un diccionario ponderado.
        
        Args:
            genre_string: Cadena con géneros múltiples
            max_genres: Número máximo de géneros a retornar
            
        Returns:
            Diccionario de géneros normalizados con puntajes de confianza
        """
        # Dividir los géneros
        individual_genres = cls.split_genres(genre_string)
        
        if not individual_genres:
            return {}
        
        # Normalizar cada género individualmente
        normalized_genres = {}
        seen_normalized = set()  # Para evitar duplicados
        
        for i, genre in enumerate(individual_genres):
            normalized, confidence = GenreNormalizer.normalize(genre)
            
            if not normalized or normalized.lower() in seen_normalized:
                continue
                
            # Calcular puntaje basado en posición y confianza
            # Primer género tiene mayor peso
            position_weight = 1.0 - (i * 0.1)  # Decrece 0.1 por posición
            position_weight = max(position_weight, 0.5)  # Mínimo 0.5
            
            final_score = confidence * position_weight
            
            if final_score >= 0.3:  # Umbral mínimo
                normalized_genres[normalized] = final_score
                seen_normalized.add(normalized.lower())
        
        # Usar el normalizador de diccionarios para post-procesamiento
        return GenreNormalizer.normalize_dict(normalized_genres)
    
    @classmethod
    def analyze_genre_string(cls, genre_string: str) -> Dict:
        """
        Analiza una cadena de géneros y proporciona información detallada.
        
        Args:
            genre_string: Cadena con géneros múltiples
            
        Returns:
            Diccionario con análisis detallado
        """
        analysis = {
            'original': genre_string,
            'individual_genres': cls.split_genres(genre_string),
            'normalized_result': cls.normalize_multi_genre(genre_string),
            'detected_separators': [],
            'potential_issues': []
        }
        
        # Detectar separadores utilizados
        for separator in cls.SEPARATORS:
            if separator in genre_string:
                analysis['detected_separators'].append(separator)
        
        # Detectar posibles problemas
        if len(analysis['detected_separators']) > 1:
            analysis['potential_issues'].append('Múltiples tipos de separadores')
        
        if any(genre.lower() == other.lower() for i, genre in enumerate(analysis['individual_genres']) 
               for j, other in enumerate(analysis['individual_genres']) if i != j):
            analysis['potential_issues'].append('Géneros duplicados')
        
        # Verificar géneros muy similares
        individual = analysis['individual_genres']
        for i in range(len(individual)):
            for j in range(i + 1, len(individual)):
                if cls._are_similar_genres(individual[i], individual[j]):
                    analysis['potential_issues'].append(f'Géneros similares: "{individual[i]}" y "{individual[j]}"')
        
        return analysis
    
    @classmethod
    def _are_similar_genres(cls, genre1: str, genre2: str) -> bool:
        """Determina si dos géneros son muy similares."""
        # Normalizar ambos géneros
        norm1, _ = GenreNormalizer.normalize(genre1)
        norm2, _ = GenreNormalizer.normalize(genre2)
        
        # Son similares si se normalizan al mismo género
        return norm1.lower() == norm2.lower() and genre1.lower() != genre2.lower()

def test_problematic_cases():
    """Prueba casos problemáticos específicos."""
    test_cases = [
        "R&B; Pop/Rock; Pop",
        "Hip-Hop, R&B, Pop",
        "Rock & Roll; Metal; Blues",
        "Electronic, Dance, House Music",
        "Pop/Rock/Alternative",
        "Jazz; Blues; Soul Music",
        "Drum & Bass, Electronic, Techno",
        "Country & Western, Folk, Bluegrass",
        "Hip-Hop / Rap / Urban",
        "Pop | Rock | Alternative",
        "R&B + Soul + Funk",
        "Electronic Dance Music; House; Techno",
        "",
        "Pop",
        "Unknown Genre XYZ; Pop; Rock"
    ]
    
    print("🎵 ANÁLISIS DE GÉNEROS MÚLTIPLES - CASOS PROBLEMÁTICOS")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i:2d}. Caso: '{test_case}'")
        print("-" * 50)
        
        if not test_case.strip():
            print("    ⚠️  Caso vacío")
            continue
        
        analysis = MultiGenreSplitter.analyze_genre_string(test_case)
        
        print(f"    📋 Géneros individuales: {analysis['individual_genres']}")
        print(f"    🔧 Separadores detectados: {analysis['detected_separators']}")
        
        if analysis['potential_issues']:
            print(f"    ⚠️  Problemas: {', '.join(analysis['potential_issues'])}")
        
        print(f"    ✅ Resultado normalizado:")
        for genre, score in analysis['normalized_result'].items():
            print(f"       • {genre}: {score:.2f}")

if __name__ == "__main__":
    test_problematic_cases() 