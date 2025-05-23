"""Genre name normalization utilities."""
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher
import re

class GenreNormalizer:
    """Handle genre name normalization and standardization."""
    
    # Special cases that should be preserved
    SPECIAL_CASES = {
        # R&B variations
        'r&b': 'R&B',
        'rnb': 'R&B',
        'randb': 'R&B',
        'rb': 'R&B',
        'r n b': 'R&B',
        'r and b': 'R&B',
        'r & b': 'R&B',
        'rhythm & blues': 'R&B',
        'rhythm n blues': 'R&B',
        'rhythm and blues': 'R&B',
        'rythm and blues': 'R&B',
        'rythm & blues': 'R&B',
        'rythem and blues': 'R&B',
        'contemporary r&b': 'Contemporary R&B',
        'modern r&b': 'Contemporary R&B',
        
        # Hip-Hop variations
        'hip-hop': 'Hip-Hop',
        'hip hop': 'Hip-Hop',
        'hiphop': 'Hip-Hop',
        'hip hop music': 'Hip-Hop',
        'rap': 'Hip-Hop',
        'rap music': 'Hip-Hop',
        
        # Electronic music variations
        'drum & bass': 'Drum & Bass',
        'drum n bass': 'Drum & Bass',
        'drum and bass': 'Drum & Bass',
        'dnb': 'Drum & Bass',
        'd&b': 'Drum & Bass',
        'house music': 'House',
        'edm': 'Electronic Dance Music',
        'electronic': 'Electronic',
        'electronica': 'Electronic',
        'electronic dance': 'Electronic Dance Music',
        'electronic-dance': 'Electronic Dance Music',
        'techno music': 'Techno',
        
        # Rock variations
        'rock n roll': 'Rock & Roll',
        'rock and roll': 'Rock & Roll',
        'rock & roll': 'Rock & Roll',
        'alt rock': 'Alternative Rock',
        'alt': 'Alternative Rock',
        'alternative': 'Alternative Rock',
        'pop rock': 'Pop/Rock',
        'pop/rock': 'Pop/Rock',
        
        # Jazz variations
        'jazz music': 'Jazz',
        'modern jazz': 'Contemporary Jazz',
        'contemp jazz': 'Contemporary Jazz',
        
        # Classical variations
        'classical music': 'Classical',
        'classic': 'Classical',
        'classics': 'Classical',
        
        # Soul/Funk variations
        'soul music': 'Soul',
        'funk music': 'Funk',
        'funky': 'Funk',
        
        # Blues variations
        'blues music': 'Blues',
        'rhythm and blues': 'R&B',  # Mapping to R&B as it's more common in modern context
        
        # Pop variations
        'popular': 'Pop',
        'pop music': 'Pop',
        
        # UK/Electronic variations
        'uk garage': 'UK Garage',
        'garage': 'UK Garage',
        'dubstep': 'Dubstep',
        'grime': 'Grime',
    }

    # Genre hierarchy relationships
    GENRE_HIERARCHY = {
        'Rock': {'Alternative Rock', 'Hard Rock', 'Progressive Rock', 'Punk Rock', 'Rock & Roll'},
        'Electronic': {'House', 'Techno', 'Trance', 'Drum & Bass', 'Ambient', 'Electronic Dance Music', 'UK Garage', 'Dubstep', 'Grime'},
        'Hip-Hop': {'Trap', 'Rap', 'Old School Hip-Hop'},
        'R&B': {'Soul', 'Funk', 'Contemporary R&B'},
        'Jazz': {'Bebop', 'Swing', 'Fusion', 'Latin Jazz'},
        'Pop': {'Synth Pop', 'Pop/Rock', 'Dance Pop'},
        'Metal': {'Heavy Metal', 'Death Metal', 'Black Metal', 'Thrash Metal'},
        'Folk': {'Traditional Folk', 'Contemporary Folk', 'Folk Rock'},
        'Classical': {'Baroque', 'Romantic', 'Contemporary Classical'},
        'Blues': {'Delta Blues', 'Chicago Blues', 'Blues Rock'}
    }

    # Validated genre whitelist (includes both parent and child genres)
    VALID_GENRES = set()
    for parent, children in GENRE_HIERARCHY.items():
        VALID_GENRES.add(parent)
        VALID_GENRES.update(children)
        
    # Add special cases to valid genres
    VALID_GENRES.update(set(SPECIAL_CASES.values()))

    # Separadores comunes para géneros múltiples
    MULTI_GENRE_SEPARATORS = [
        ';',      # "R&B; Pop; Rock"
        ',',      # "R&B, Pop, Rock"
        '|',      # "R&B | Pop | Rock"
        '+',      # "R&B + Pop"
        ' and ',  # "R&B and Pop"
        '\n',     # Líneas separadas
        '\t',     # Tabs
    ]
    
    # Géneros que contienen separadores que NO deben dividirse
    PROTECTED_MULTI_GENRES = {
        'R&B', 'Rock & Roll', 'Drum & Bass', 'Contemporary R&B', 
        'Pop/Rock', 'Blues Rock', 'Folk Rock', 'Blues & Soul',
        'Hip-Hop', 'Electronic Dance Music', 'UK Garage',
        'Country & Western', 'Rhythm & Blues'
    }

    @classmethod
    def normalize(cls, genre: str, fuzzy_match: bool = True) -> Tuple[str, float]:
        """Normalize a genre name with confidence score.
        
        Args:
            genre: Raw genre name
            fuzzy_match: Whether to attempt fuzzy matching for unknown genres
            
        Returns:
            Tuple of (normalized genre name, confidence score)
        """
        if not genre:
            return "", 0.0
            
        # Remove extra whitespace and convert to lowercase for comparison
        cleaned_genre = ' '.join(genre.strip().split())
        if not cleaned_genre:  # If after cleaning, it's empty
            return "", 0.0
        lower_genre = cleaned_genre.lower()
        
        # Check special cases first (including common misspellings)
        if lower_genre in cls.SPECIAL_CASES:
            return cls.SPECIAL_CASES[lower_genre], 1.0
            
        # Split and normalize words
        words = lower_genre.replace('-', ' - ').replace('&', ' & ').replace('/', ' / ').split()
        
        # Words to keep lowercase when not at start
        small_words = {'and', 'or', 'the', 'in', 'of', 'a', 'an', 'but', 'for', 'on', 'to', 'with', 'n', 'feat', 'ft'}
        
        # Special words that should always be capitalized
        force_capitalize = {'R&B', 'DJ', 'UK', 'USA', 'MTV', 'EP', 'LP', 'CD'}
        
        # Capitalize each word with special rules
        result = []
        for i, word in enumerate(words):
            if word.upper() in force_capitalize:
                result.append(word.upper())
            elif word in {'-', '&', '/'}:
                result.append(word)
            elif i == 0 or word not in small_words:
                result.append(word.capitalize())
            else:
                result.append(word)
                
        normalized = ' '.join(result)

        # If normalized genre is in whitelist, return with full confidence
        if normalized in cls.VALID_GENRES:
            return normalized, 1.0

        # Try fuzzy matching if enabled
        if fuzzy_match:
            # First check if it's a parent genre
            if normalized in cls.GENRE_HIERARCHY:
                return normalized, 1.0
                
            # Then try exact substring matches with parent genres first
            for valid_genre in cls.GENRE_HIERARCHY.keys():
                if lower_genre in valid_genre.lower() or valid_genre.lower() in lower_genre:
                    return valid_genre, 0.95
                    
            # Then try other exact substring matches
            for valid_genre in cls.VALID_GENRES:
                if lower_genre in valid_genre.lower() or valid_genre.lower() in lower_genre:
                    return valid_genre, 0.9

            # Try fuzzy matching against parent genres first
            parent_match, parent_score = cls._find_best_match(normalized, cls.GENRE_HIERARCHY.keys())
            if parent_score >= 0.85:
                return parent_match, parent_score

            # Then try special cases
            special_match, special_score = cls._find_best_match(normalized, cls.SPECIAL_CASES.values())
            if special_score >= 0.9:
                return special_match, special_score

            # Finally try all valid genres
            valid_match, valid_score = cls._find_best_match(normalized, cls.VALID_GENRES)
            if valid_score >= 0.85:
                return valid_match, valid_score * 0.95  # Slightly reduce confidence for non-parent matches

            # Return the normalized form with low confidence for unknown genres
            if valid_score < 0.7:
                return normalized, 0.5
                
        # Return the normalized form with very low confidence for unmatched genres
        return normalized, 0.5

    @classmethod
    def _find_best_match(cls, genre: str, candidates: Set[str]) -> Tuple[str, float]:
        """Find the best matching genre from a set of candidates.
        
        Args:
            genre: The genre to find a match for
            candidates: Set of candidate genres to match against
            
        Returns:
            Tuple of (best matching genre, similarity score)
        """
        best_score = 0
        best_match = genre

        for candidate in candidates:
            # Calculate base similarity score
            score = SequenceMatcher(None, genre.lower(), candidate.lower()).ratio()
            
            # Apply bonuses for partial matches
            if genre.lower() in candidate.lower() or candidate.lower() in genre.lower():
                score += 0.1
                
            # Bonus for matching first word
            genre_first = genre.lower().split()[0]
            candidate_first = candidate.lower().split()[0]
            if genre_first == candidate_first:
                score += 0.1
                
            score = min(score, 1.0)  # Cap at 1.0
            
            if score > best_score:
                best_score = score
                best_match = candidate

        return best_match, best_score

    @classmethod
    def get_parent_genre(cls, genre: str) -> Optional[str]:
        """Get the parent genre for a given genre.
        
        Args:
            genre: The genre to find the parent for
            
        Returns:
            Parent genre name or None if no parent found
        """
        normalized, _ = cls.normalize(genre)
        for parent, children in cls.GENRE_HIERARCHY.items():
            if normalized in children:
                return parent
        return None

    @classmethod
    def normalize_list(cls, genres: List[str]) -> List[Tuple[str, float]]:
        """Normalize a list of genres with confidence scores.
        
        Args:
            genres: List of raw genre names
            
        Returns:
            List of tuples (normalized genre, confidence score)
        """
        return [cls.normalize(g) for g in genres if g]
        
    @classmethod
    def normalize_dict(cls, genres: Dict[str, float]) -> Dict[str, float]:
        """Normalize genre names in a confidence score dictionary with intelligent weighting.
        
        Args:
            genres: Dictionary of genre names to confidence scores
            
        Returns:
            Dictionary with normalized genre names and adjusted confidence scores
        """
        if not genres:
            return {}

        THRESHOLD = 0.4

        # First pass: Normalize and filter based on threshold
        intermediate = {}
        
        for genre, score in genres.items():
            if score < THRESHOLD:
                continue
            
            # Check special cases first
            lower_genre = genre.lower()
            if lower_genre in cls.SPECIAL_CASES:
                norm_name = cls.SPECIAL_CASES[lower_genre]
                intermediate[norm_name] = score
                continue
                
            # Keep valid genres as-is
            if genre in cls.VALID_GENRES:
                intermediate[genre] = score
                continue
                
            # Try normalizing unknown genres
            norm_name, norm_score = cls.normalize(genre)
            if norm_name and norm_score * score >= THRESHOLD:
                intermediate[norm_name] = score # Keep original score for consistency
                
        if not intermediate:
            return {}
            
        # Second pass: Add parent and base genres with derived scores
        all_genres = {}  # Start fresh to control order of addition
        
        # Add parent genres first (they get priority)
        for genre, score in intermediate.items():
            parent = cls.get_parent_genre(genre)
            if parent:
                parent_score = score * 0.95
                if parent not in all_genres or parent_score > all_genres[parent]:
                    all_genres[parent] = parent_score
                    
        # Add original genres next (preserving their scores)
        for genre, score in intermediate.items():
            if score >= THRESHOLD:
                all_genres[genre] = score
                    
        # Finally add base genres from compounds
        for genre, score in intermediate.items():
            if " " in genre:
                parts = genre.split()
                for part in parts:
                    if part in cls.GENRE_HIERARCHY:
                        base_score = score * 0.95
                        if part not in all_genres or base_score > all_genres[part]:
                            all_genres[part] = base_score
                            
        # Sort by confidence (descending) then name (ascending)
        sorted_genres = sorted(all_genres.items(), key=lambda x: (-x[1], x[0]))
        
        # Build final result with top 3 genres
        final = {}
        for genre, score in sorted_genres:
            if score >= THRESHOLD:
                final[genre] = score
                if len(final) >= 3:
                    break

        return final

    @classmethod
    def split_multi_genre_string(cls, genre_string: str) -> List[str]:
        """
        Divide una cadena de géneros múltiples respetando géneros protegidos.
        
        Args:
            genre_string: Cadena con géneros múltiples como "R&B; Pop/Rock; Pop"
            
        Returns:
            Lista de géneros individuales limpios
        """
        if not genre_string or not genre_string.strip():
            return []
        
        # Limpiar la cadena inicial
        cleaned = genre_string.strip()
        
        # Proteger géneros conocidos que contienen separadores
        protected_replacements = {}
        temp_string = cleaned
        
        for i, protected_genre in enumerate(cls.PROTECTED_MULTI_GENRES):
            if protected_genre.lower() in cleaned.lower():
                placeholder = f"__PROTECTED_{i}__"
                # Buscar coincidencias case-insensitive
                pattern = re.escape(protected_genre)
                temp_string = re.sub(pattern, placeholder, temp_string, flags=re.IGNORECASE)
                protected_replacements[placeholder] = protected_genre
        
        # Dividir por separadores (excluyendo '/' y '&' para géneros protegidos)
        genres = [temp_string]
        
        for separator in cls.MULTI_GENRE_SEPARATORS:
            new_genres = []
            for genre in genres:
                if separator in genre:
                    new_genres.extend([p.strip() for p in genre.split(separator) if p.strip()])
                else:
                    new_genres.append(genre)
            genres = new_genres
        
        # Manejar '/' de manera especial para evitar romper géneros como "Pop/Rock"
        final_split_genres = []
        for genre in genres:
            if '/' in genre and genre not in protected_replacements.values():
                # Solo dividir si ambas partes parecen géneros independientes
                parts = [p.strip() for p in genre.split('/') if p.strip()]
                if len(parts) > 1:
                    # Verificar si es un género compuesto conocido
                    combined = '/'.join(parts)
                    if any(protected in combined for protected in protected_replacements.values()):
                        final_split_genres.append(genre)
                    else:
                        # Dividir solo si todas las partes son géneros válidos
                        all_valid = True
                        for part in parts:
                            normalized, confidence = cls.normalize(part, fuzzy_match=False)
                            if confidence < 0.7:
                                all_valid = False
                                break
                        
                        if all_valid and len(parts) <= 3:  # Máximo 3 géneros por división
                            final_split_genres.extend(parts)
                        else:
                            final_split_genres.append(genre)
                else:
                    final_split_genres.append(genre)
            else:
                final_split_genres.append(genre)
        
        # Restaurar géneros protegidos
        restored_genres = []
        for genre in final_split_genres:
            restored_genre = genre
            for placeholder, original in protected_replacements.items():
                restored_genre = restored_genre.replace(placeholder, original)
            if restored_genre.strip():
                restored_genres.append(restored_genre.strip())
        
        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_genres = []
        for genre in restored_genres:
            normalized_key = genre.lower().strip()
            if normalized_key not in seen:
                seen.add(normalized_key)
                unique_genres.append(genre)
        
        return unique_genres

    @classmethod
    def normalize_multi_genre_string(cls, genre_string: str, max_genres: int = 3) -> Dict[str, float]:
        """
        Normaliza una cadena con múltiples géneros manejando separadores inconsistentes.
        
        Args:
            genre_string: Cadena con géneros múltiples como "R&B; Pop/Rock; Pop"
            max_genres: Número máximo de géneros a retornar
            
        Returns:
            Diccionario de géneros normalizados con puntajes de confianza
        """
        # Dividir los géneros
        individual_genres = cls.split_multi_genre_string(genre_string)
        
        if not individual_genres:
            return {}
        
        # Normalizar cada género individualmente
        normalized_genres = {}
        seen_normalized = set()  # Para evitar duplicados después de normalización
        
        for i, genre in enumerate(individual_genres):
            normalized, confidence = cls.normalize(genre)
            
            if not normalized or confidence < 0.3:
                continue
                
            # Verificar duplicados después de normalización
            normalized_key = normalized.lower()
            if normalized_key in seen_normalized:
                continue
                
            # Calcular puntaje basado en posición y confianza
            # Primer género tiene mayor peso
            position_weight = 1.0 - (i * 0.1)  # Decrece 0.1 por posición
            position_weight = max(position_weight, 0.5)  # Mínimo 0.5
            
            final_score = confidence * position_weight
            
            if final_score >= 0.3:  # Umbral mínimo
                normalized_genres[normalized] = final_score
                seen_normalized.add(normalized_key)
        
        # Detectar y resolver conflictos de géneros similares
        # Por ejemplo: "Pop/Rock" y "Pop" -> mantener solo "Pop/Rock" (más específico)
        conflicted_genres = {}
        for genre1, score1 in list(normalized_genres.items()):
            for genre2, score2 in list(normalized_genres.items()):
                if genre1 != genre2:
                    
                    # Normalizar géneros para comparación (separar palabras)
                    genre1_words = set(genre1.lower().replace('/', ' ').replace('&', ' ').split())
                    genre2_words = set(genre2.lower().replace('/', ' ').replace('&', ' ').split())
                    
                    # Si las palabras de genre1 están completamente contenidas en genre2
                    if genre1_words.issubset(genre2_words) and len(genre2_words) > len(genre1_words):
                        # genre2 es más específico
                        if genre1 in normalized_genres and genre2 in normalized_genres:
                            if score2 >= score1 * 0.7:  # Umbral permisivo
                                conflicted_genres[genre1] = genre2
                    
                    # Si las palabras de genre2 están completamente contenidas en genre1
                    elif genre2_words.issubset(genre1_words) and len(genre1_words) > len(genre2_words):
                        # genre1 es más específico
                        if genre1 in normalized_genres and genre2 in normalized_genres:
                            if score1 >= score2 * 0.7:  # Umbral permisivo
                                conflicted_genres[genre2] = genre1
        
        # Aplicar resolución de conflictos
        for to_remove, replacement in conflicted_genres.items():
            if to_remove in normalized_genres and replacement in normalized_genres:
                # Combinar scores tomando el máximo
                combined_score = max(normalized_genres[to_remove], normalized_genres[replacement])
                del normalized_genres[to_remove]
                normalized_genres[replacement] = combined_score
        
        # Aplicar límite de géneros y ordenar por score
        sorted_genres = sorted(normalized_genres.items(), key=lambda x: (-x[1], x[0]))
        
        # Retornar los top géneros limitados por max_genres
        final_result = {}
        for genre, score in sorted_genres:
            if len(final_result) < max_genres:
                final_result[genre] = score
            else:
                break
        
        return final_result

    @classmethod
    def analyze_genre_fusion_validity(cls, genre_string: str) -> Dict:
        """
        Analiza si una combinación de géneros es musicalmente válida.
        
        Args:
            genre_string: Cadena con géneros múltiples como "Heavy Metal; Hip-Hop; Punk Rock"
            
        Returns:
            Diccionario con análisis de validez musical
        """
        # Dividir géneros usando nuestro sistema existente
        individual_genres = cls.split_multi_genre_string(genre_string)
        
        if len(individual_genres) < 2:
            return {
                'validity': 'single_genre',
                'recommendation': 'keep_as_is',
                'explanation': 'Un solo género detectado'
            }
        
        # Fusiones conocidas y válidas con ejemplos reales
        known_fusions = {
            frozenset(['Heavy Metal', 'Hip-Hop']): {
                'fusion_genre': 'Rap Metal',
                'examples': ['Rage Against the Machine', 'Limp Bizkit', 'Body Count'],
                'validity': 'high',
                'recommendation': 'keep_both_or_use_fusion'
            },
            frozenset(['Heavy Metal', 'Punk Rock']): {
                'fusion_genre': 'Crossover Thrash',
                'examples': ['Suicidal Tendencies', 'D.R.I.', 'Municipal Waste'],
                'validity': 'high',
                'recommendation': 'keep_both_or_use_fusion'
            },
            frozenset(['Hip-Hop', 'Punk Rock']): {
                'fusion_genre': 'Punk Rap',
                'examples': ['Beastie Boys', 'The Transplants'],
                'validity': 'medium',
                'recommendation': 'consider_fusion'
            },
            frozenset(['Heavy Metal', 'Hip-Hop', 'Punk Rock']): {
                'fusion_genre': 'Nu Metal',
                'examples': ['Rage Against the Machine', 'Linkin Park', 'P.O.D.'],
                'validity': 'medium-high',
                'recommendation': 'use_fusion_genre'
            },
            frozenset(['Rock', 'Electronic']): {
                'fusion_genre': 'Electronic Rock',
                'examples': ['Nine Inch Nails', 'The Prodigy'],
                'validity': 'high',
                'recommendation': 'keep_both_or_use_fusion'
            },
            frozenset(['Jazz', 'Hip-Hop']): {
                'fusion_genre': 'Jazz Rap',
                'examples': ['A Tribe Called Quest', 'Guru'],
                'validity': 'very_high',
                'recommendation': 'keep_both'
            }
        }
        
        # Normalizar géneros para comparación
        normalized_genres = []
        for genre in individual_genres:
            norm_genre, _ = cls.normalize(genre)
            if norm_genre:
                normalized_genres.append(norm_genre)
        
        genre_set = frozenset(normalized_genres)
        
        # Verificar si es una fusión conocida
        if genre_set in known_fusions:
            fusion_info = known_fusions[genre_set]
            return {
                'validity': 'known_fusion',
                'original_genres': individual_genres,
                'normalized_genres': normalized_genres,
                'fusion_info': fusion_info,
                'recommendation': fusion_info['recommendation'],
                'explanation': f"Fusión musical válida: {fusion_info['fusion_genre']}"
            }
        
        # Análisis de compatibilidad para fusiones no conocidas
        compatibility_score = cls._calculate_genre_compatibility(normalized_genres)
        
        if compatibility_score >= 0.7:
            validity = 'likely_valid'
            recommendation = 'keep_all'
            explanation = 'Géneros musicalmente compatibles'
        elif compatibility_score >= 0.4:
            validity = 'possibly_valid'
            recommendation = 'review_manually'
            explanation = 'Fusión posible pero inusual'
        else:
            validity = 'unlikely_valid'
            recommendation = 'check_metadata'
            explanation = 'Combinación musicalmente improbable - verificar fuentes'
        
        return {
            'validity': validity,
            'original_genres': individual_genres,
            'normalized_genres': normalized_genres,
            'compatibility_score': compatibility_score,
            'recommendation': recommendation,
            'explanation': explanation
        }
    
    @classmethod
    def _calculate_genre_compatibility(cls, genres: List[str]) -> float:
        """
        Calcula un score de compatibilidad musical entre géneros.
        
        Args:
            genres: Lista de géneros normalizados
            
        Returns:
            Score de compatibilidad (0.0 - 1.0)
        """
        if len(genres) < 2:
            return 1.0
        
        # Características musicales básicas por género
        genre_characteristics = {
            'Rock': {'family': 'rock', 'energy': 'high', 'era': 'modern'},
            'Heavy Metal': {'family': 'rock', 'energy': 'very_high', 'era': 'modern'},
            'Punk Rock': {'family': 'rock', 'energy': 'very_high', 'era': 'modern'},
            'Hip-Hop': {'family': 'urban', 'energy': 'medium-high', 'era': 'modern'},
            'Electronic': {'family': 'electronic', 'energy': 'variable', 'era': 'modern'},
            'Jazz': {'family': 'jazz', 'energy': 'medium', 'era': 'classic'},
            'Blues': {'family': 'blues', 'energy': 'medium', 'era': 'classic'},
            'Pop': {'family': 'pop', 'energy': 'medium', 'era': 'modern'},
            'Classical': {'family': 'classical', 'energy': 'variable', 'era': 'classical'},
            'Folk': {'family': 'folk', 'energy': 'low-medium', 'era': 'traditional'}
        }
        
        # Score base que decrece con más géneros
        base_score = max(0.2, 1.0 - (len(genres) - 2) * 0.15)
        
        # Analizar compatibilidad por características
        families = set()
        energy_levels = []
        eras = set()
        
        for genre in genres:
            if genre in genre_characteristics:
                char = genre_characteristics[genre]
                families.add(char['family'])
                energy_levels.append(char['energy'])
                eras.add(char['era'])
        
        # Bonificaciones por compatibilidad
        compatibility_bonus = 0.0
        
        # Bonus si comparten familia musical
        if len(families) == 1:
            compatibility_bonus += 0.3
        elif 'rock' in families and len(families) == 2:
            # Rock se fusiona bien con otros géneros
            compatibility_bonus += 0.2
        
        # Bonus por era similar
        if len(eras) == 1:
            compatibility_bonus += 0.1
        elif 'modern' in eras:
            compatibility_bonus += 0.05
        
        # Penalizaciones por incompatibilidades extremas
        penalty = 0.0
        
        # Penalizar combinaciones muy dispares
        if 'classical' in [g.lower() for g in genres] and 'death metal' in [g.lower() for g in genres]:
            penalty += 0.4
        
        if 'ambient' in [g.lower() for g in genres] and any('punk' in g.lower() for g in genres):
            penalty += 0.3
        
        final_score = min(1.0, max(0.0, base_score + compatibility_bonus - penalty))
        return final_score
    
    @classmethod
    def normalize_multi_genre_string_with_fusion_analysis(cls, genre_string: str, 
                                                         max_genres: int = 3,
                                                         use_fusion_analysis: bool = True) -> Dict[str, float]:
        """
        Normaliza géneros múltiples con análisis de fusión musical inteligente.
        
        Args:
            genre_string: Cadena con géneros múltiples
            max_genres: Número máximo de géneros a retornar
            use_fusion_analysis: Si usar análisis de validez musical
            
        Returns:
            Diccionario de géneros normalizados con análisis incluido
        """
        if not use_fusion_analysis:
            return cls.normalize_multi_genre_string(genre_string, max_genres)
        
        # Realizar análisis de fusión primero
        fusion_analysis = cls.analyze_genre_fusion_validity(genre_string)
        
        # Procesar según recomendación del análisis
        recommendation = fusion_analysis.get('recommendation', 'keep_all')
        
        if recommendation == 'use_fusion_genre' and 'fusion_info' in fusion_analysis:
            # Usar el género de fusión en lugar de géneros múltiples
            fusion_genre = fusion_analysis['fusion_info']['fusion_genre']
            normalized, confidence = cls.normalize(fusion_genre)
            
            result = {normalized: confidence} if normalized else {}
            result['_fusion_analysis'] = fusion_analysis
            return result
            
        elif recommendation == 'keep_both_or_use_fusion' and 'fusion_info' in fusion_analysis:
            # Ofrecer tanto géneros originales como fusión (priorizar fusión)
            fusion_genre = fusion_analysis['fusion_info']['fusion_genre']
            fusion_normalized, fusion_confidence = cls.normalize(fusion_genre)
            
            # Obtener géneros originales normalizados
            original_result = cls.normalize_multi_genre_string(genre_string, max_genres - 1)
            
            # Combinar con prioridad a la fusión
            result = {}
            if fusion_normalized:
                result[fusion_normalized] = fusion_confidence * 1.1  # Bonus por ser fusión específica
            
            # Agregar géneros originales con score reducido
            for genre, score in original_result.items():
                if genre not in result:
                    result[genre] = score * 0.9
            
            # Limitar al máximo de géneros
            sorted_genres = sorted(result.items(), key=lambda x: -x[1])[:max_genres]
            result = dict(sorted_genres)
            result['_fusion_analysis'] = fusion_analysis
            return result
        
        else:
            # Usar normalización estándar
            result = cls.normalize_multi_genre_string(genre_string, max_genres)
            result['_fusion_analysis'] = fusion_analysis
            return result
