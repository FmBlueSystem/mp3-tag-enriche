#!/usr/bin/env python3
"""Script para probar la funcionalidad de renombrado de archivos MP3."""
from pathlib import Path
import os
import sys
from src.core.file_handler import Mp3FileHandler

def main():
    """Función principal para probar el renombrado de archivos."""
    print("Probando la funcionalidad de renombrado de archivos MP3")
    
    # Crear una instancia del manejador de archivos con directorio de respaldo
    backup_dir = Path("/Volumes/My Passport/Dj compilation 2025/Respados mp3")
    file_handler = Mp3FileHandler(backup_dir=str(backup_dir))
    
    # Verificar si hay archivos MP3 en el directorio actual o en un directorio especificado
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    test_path = Path(test_dir)
    
    if not test_path.exists():
        print(f"El directorio {test_dir} no existe")
        return
    
    # Buscar archivos MP3 en el directorio
    mp3_files = list(test_path.glob("*.mp3"))
    
    if not mp3_files:
        print(f"No se encontraron archivos MP3 en {test_dir}")
        return
    
    print(f"Se encontraron {len(mp3_files)} archivos MP3 en {test_dir}")
    
    # Determinar si se debe incluir género en el nombre
    include_genre = True
    if len(sys.argv) > 2:
        include_genre = sys.argv[2].lower() in ('true', 't', '1', 'yes', 'y')
    print(f"Incluir género en nombres de archivo: {include_genre}")
    
    # Determinar cuántos archivos procesar
    max_files = 5  # Por defecto procesar 5 archivos
    if len(sys.argv) > 3:
        try:
            max_files = int(sys.argv[3])
        except ValueError:
            pass
    
    # Probar el renombrado en los archivos
    for i, mp3_file in enumerate(mp3_files[:max_files], 1):  # Procesar los primeros archivos según el límite
        file_path = str(mp3_file)
        print(f"\n[{i}] Procesando: {mp3_file.name}")
        
        # Leer metadatos
        tags = file_handler.read_tags(file_path)
        print(f"Etiquetas actuales: {tags}")
        
        # Información del archivo
        info = file_handler.get_file_info(file_path)
        print(f"Información del archivo: {info}")
        
        # Intentar renombrar el archivo basado en los metadatos
        print("Intentando renombrar el archivo...")
        result = file_handler.rename_file_by_genre(file_path, include_genre=include_genre)
        
        if result["success"]:
            print(f"¡Éxito! {result['message']}")
            print(f"Ruta original: {result['original_path']}")
            print(f"Nueva ruta: {result.get('new_path', 'No cambió')}")
        else:
            print(f"Error: {result.get('error', 'Error desconocido')}")

if __name__ == "__main__":
    main()
