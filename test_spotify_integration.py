#!/usr/bin/env python3
"""
🎵 ANÁLISIS COMPLETO DE INTEGRACIÓN DE SPOTIFY
============================================

Script que analiza y prueba la integración de Spotify en el sistema
para identificar problemas y mejoras.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar directorio del proyecto
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

def check_spotify_dependencies():
    """Verificar dependencias de Spotify."""
    print("🔍 VERIFICANDO DEPENDENCIAS DE SPOTIFY")
    print("=" * 50)
    
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        # Intentar obtener versión de diferentes formas
        version = "desconocida"
        try:
            version = spotipy.__version__
        except AttributeError:
            try:
                import pkg_resources
                version = pkg_resources.get_distribution("spotipy").version
            except:
                pass
        
        print(f"✅ spotipy instalado: versión {version}")
        return True
    except ImportError as e:
        print(f"❌ spotipy no disponible: {e}")
        return False

def load_spotify_credentials():
    """Cargar credenciales de Spotify."""
    print("\n🔑 CARGANDO CREDENCIALES DE SPOTIFY")
    print("=" * 50)
    
    # Método 1: Desde config/api_keys.json
    config_file = Path("config/api_keys.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                spotify_config = config.get("spotify", {})
                client_id = spotify_config.get("client_id")
                client_secret = spotify_config.get("client_secret")
                
                if client_id and client_secret:
                    print(f"✅ Credenciales encontradas en {config_file}")
                    print(f"   Client ID: {client_id[:4]}...{client_id[-4:]}")
                    print(f"   Client Secret: {client_secret[:4]}...{client_secret[-4:]}")
                    return client_id, client_secret
                else:
                    print(f"⚠️ Credenciales incompletas en {config_file}")
        except Exception as e:
            print(f"❌ Error leyendo {config_file}: {e}")
    else:
        print(f"⚠️ Archivo {config_file} no encontrado")
    
    # Método 2: Variables de entorno
    env_client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    env_client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    
    if env_client_id and env_client_secret:
        print("✅ Credenciales encontradas en variables de entorno")
        print(f"   SPOTIPY_CLIENT_ID: {env_client_id[:4]}...{env_client_id[-4:]}")
        print(f"   SPOTIPY_CLIENT_SECRET: {'*' * 8}")
        return env_client_id, env_client_secret
    else:
        print("❌ Variables de entorno no configuradas")
    
    return None, None

def test_spotify_authentication(client_id: str, client_secret: str):
    """Probar autenticación con Spotify."""
    print("\n🔐 PROBANDO AUTENTICACIÓN CON SPOTIFY")
    print("=" * 50)
    
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        
        # Crear cliente de autenticación
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Prueba simple de búsqueda
        result = sp.search(q="Queen Bohemian Rhapsody", type='track', limit=1)
        
        if result and result.get('tracks', {}).get('items'):
            track = result['tracks']['items'][0]
            print("✅ Autenticación exitosa")
            print(f"   Prueba exitosa: {track['name']} - {track['artists'][0]['name']}")
            return True
        else:
            print("⚠️ Autenticación OK pero sin resultados de búsqueda")
            return True
            
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return False

def test_spotify_api_integration():
    """Probar integración con SpotifyAPI del sistema."""
    print("\n🎵 PROBANDO INTEGRACIÓN CON SPOTIFYAPI")
    print("=" * 50)
    
    try:
        from src.core.spotify_api import SpotifyAPI
        print("✅ SpotifyAPI importada correctamente")
        
        # Cargar credenciales
        client_id, client_secret = load_spotify_credentials()
        if not client_id or not client_secret:
            print("❌ No se pueden probar sin credenciales")
            return False
        
        # Crear instancia de SpotifyAPI
        spotify_api = SpotifyAPI(client_id=client_id, client_secret=client_secret)
        
        if not spotify_api.sp:
            print("❌ No se pudo inicializar cliente Spotify")
            return False
        
        print("✅ SpotifyAPI inicializada correctamente")
        
        # Probar get_track_info
        test_cases = [
            ("Queen", "Bohemian Rhapsody"),
            ("The Beatles", "Hey Jude"),
            ("Madonna", "Like a Virgin"),
            ("", ""),  # Caso edge: valores vacíos
            (None, None),  # Caso edge: valores None
        ]
        
        print("\n📋 Probando método get_track_info:")
        success_count = 0
        
        for artist, track in test_cases:
            try:
                result = spotify_api.get_track_info(artist, track)
                
                if artist and track:
                    print(f"   🎵 {artist} - {track}")
                    print(f"      Géneros: {result.get('genres', [])}")
                    print(f"      Año: {result.get('year', 'N/A')}")
                    print(f"      Álbum: {result.get('album', 'N/A')}")
                    
                    if result.get('genres') or result.get('year') or result.get('album'):
                        success_count += 1
                        print("      ✅ Datos obtenidos")
                    else:
                        print("      ⚠️ Sin datos específicos")
                else:
                    print(f"   🧪 Caso edge: artist={artist}, track={track}")
                    if result == {"genres": [], "year": None, "album": None, "source_api": "Spotify"}:
                        print("      ✅ Manejo correcto de valores vacíos")
                    else:
                        print(f"      ⚠️ Resultado inesperado: {result}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Resumen: {success_count}/{len([t for t in test_cases if t[0] and t[1]])} casos exitosos")
        return success_count > 0
        
    except ImportError as e:
        print(f"❌ Error importando SpotifyAPI: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def analyze_integration_in_main_system():
    """Analizar cómo está integrada Spotify en el sistema principal."""
    print("\n🔍 ANALIZANDO INTEGRACIÓN EN SISTEMA PRINCIPAL")
    print("=" * 50)
    
    integration_points = []
    
    # 1. Verificar en mp3_enricher.py
    enricher_file = Path("mp3_enricher.py")
    if enricher_file.exists():
        with open(enricher_file, 'r') as f:
            content = f.read()
            if "SpotifyAPI" in content:
                integration_points.append("mp3_enricher.py")
                print("✅ Integración encontrada en mp3_enricher.py")
            else:
                print("⚠️ No se encontró integración en mp3_enricher.py")
    
    # 2. Verificar en src/__main__.py
    main_file = Path("src/__main__.py")
    if main_file.exists():
        with open(main_file, 'r') as f:
            content = f.read()
            if "SpotifyAPI" in content:
                integration_points.append("src/__main__.py")
                print("✅ Integración encontrada en src/__main__.py")
            else:
                print("⚠️ No se encontró integración en src/__main__.py")
    
    # 3. Verificar en enriquecer_mp3_cli.py
    cli_file = Path("enriquecer_mp3_cli.py")
    if cli_file.exists():
        with open(cli_file, 'r') as f:
            content = f.read()
            if "SpotifyAPI" in content:
                integration_points.append("enriquecer_mp3_cli.py")
                print("✅ Integración encontrada en enriquecer_mp3_cli.py")
            else:
                print("⚠️ No se encontró integración en enriquecer_mp3_cli.py")
    
    # 4. Verificar en los procesadores batch
    batch_files = ["batch_process_mp3.py", "simple_batch_processor.py"]
    for batch_file in batch_files:
        if Path(batch_file).exists():
            with open(batch_file, 'r') as f:
                content = f.read()
                if "SpotifyAPI" in content:
                    integration_points.append(batch_file)
                    print(f"✅ Integración encontrada en {batch_file}")
                else:
                    print(f"⚠️ No se encontró integración en {batch_file}")
    
    return integration_points

def identify_spotify_issues():
    """Identificar problemas específicos de la integración de Spotify."""
    print("\n🚨 IDENTIFICANDO PROBLEMAS DE INTEGRACIÓN")
    print("=" * 50)
    
    issues = []
    
    # Issue 1: Credenciales hardcodeadas
    config_file = Path("config/api_keys.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                spotify_config = config.get("spotify", {})
                client_id = spotify_config.get("client_id", "")
                
                # Verificar si son credenciales de ejemplo/prueba
                if client_id.startswith("8e5333") or len(client_id) < 30:
                    issues.append("🔑 Credenciales potencialmente de prueba/ejemplo")
                    print("⚠️ Las credenciales parecen ser de prueba")
        except Exception:
            pass
    
    # Issue 2: Verificar rate limiting
    try:
        from src.core.spotify_api import SpotifyAPI
        # Crear instancia temporal para revisar configuración
        api_code = open("src/core/spotify_api.py", 'r').read()
        if "fill_rate=1.0" in api_code:
            print("⚠️ Rate limiting puede ser agresivo (1.0 req/sec)")
            issues.append("📊 Rate limiting agresivo")
    except Exception:
        pass
    
    # Issue 3: Verificar manejo de errores
    try:
        from src.core.spotify_api import SpotifyAPI
        # Revisar si maneja correctamente cliente no inicializado
        spotify_api = SpotifyAPI(client_id="invalid", client_secret="invalid")
        result = spotify_api.get_track_info("Test", "Test")
        if result.get("source_api") == "Spotify":
            print("✅ Manejo correcto de cliente no inicializado")
        else:
            issues.append("🔧 Manejo incorrecto de errores de inicialización")
    except Exception:
        issues.append("🔧 Error en manejo de excepciones")
    
    # Issue 4: Verificar timeouts
    spotify_api_code = ""
    try:
        with open("src/core/spotify_api.py", 'r') as f:
            spotify_api_code = f.read()
    except Exception:
        pass
    
    if "timeout" not in spotify_api_code.lower():
        issues.append("⏱️ Sin configuración de timeout específico")
        print("⚠️ No se encontró configuración de timeout específico")
    
    return issues

def generate_improvement_recommendations():
    """Generar recomendaciones de mejora."""
    print("\n💡 RECOMENDACIONES DE MEJORA")
    print("=" * 50)
    
    recommendations = [
        "🔑 Usar variables de entorno para credenciales en producción",
        "📊 Ajustar rate limiting según límites reales de Spotify (2000 req/min)",
        "⏱️ Implementar timeouts específicos para Spotify API",
        "🔧 Mejorar manejo de errores específicos de Spotify",
        "📝 Agregar logging más detallado para debug",
        "🧪 Implementar tests unitarios para SpotifyAPI",
        "💾 Optimizar cache para reducir llamadas redundantes",
        "🔄 Implementar retry automático para errores temporales"
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    return recommendations

def main():
    """Función principal."""
    print("🎵 ANÁLISIS COMPLETO DE INTEGRACIÓN DE SPOTIFY")
    print("=" * 60)
    print()
    
    # 1. Verificar dependencias
    deps_ok = check_spotify_dependencies()
    
    if not deps_ok:
        print("\n❌ No se puede continuar sin dependencias")
        return 1
    
    # 2. Cargar credenciales
    client_id, client_secret = load_spotify_credentials()
    
    if not client_id or not client_secret:
        print("\n❌ No se pueden hacer pruebas sin credenciales")
        auth_ok = False
    else:
        # 3. Probar autenticación
        auth_ok = test_spotify_authentication(client_id, client_secret)
    
    # 4. Probar integración API
    if auth_ok:
        api_ok = test_spotify_api_integration()
    else:
        api_ok = False
    
    # 5. Analizar integración en sistema
    integration_points = analyze_integration_in_main_system()
    
    # 6. Identificar problemas
    issues = identify_spotify_issues()
    
    # 7. Generar recomendaciones
    recommendations = generate_improvement_recommendations()
    
    # Resumen final
    print("\n🎯 RESUMEN EJECUTIVO")
    print("=" * 30)
    print(f"✅ Dependencias: {'OK' if deps_ok else 'FALLO'}")
    print(f"✅ Autenticación: {'OK' if auth_ok else 'FALLO'}")
    print(f"✅ Integración API: {'OK' if api_ok else 'FALLO'}")
    print(f"📍 Puntos de integración: {len(integration_points)}")
    print(f"🚨 Problemas identificados: {len(issues)}")
    print(f"💡 Recomendaciones: {len(recommendations)}")
    
    if auth_ok and api_ok:
        print("\n🎉 ¡Integración de Spotify funcionando correctamente!")
        return 0
    else:
        print("\n⚠️ Se encontraron problemas en la integración de Spotify")
        return 1

if __name__ == "__main__":
    exit(main()) 