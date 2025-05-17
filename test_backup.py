#!/usr/bin/env python3
"""
Script para probar el respaldo de archivos en la nueva ubicación.
"""
from pathlib import Path
import os
import sys

# Importamos directamente desde la ubicación del archivo
sys.path.append('/Users/freddymolina/Proyectos/basico')
from src.core.file_handler import Mp3FileHandler

def test_backup():
    """Prueba la creación de respaldos en la nueva ubicación."""
    print("Probando la creación de respaldos en la nueva ubicación")
    
    # Ruta a la carpeta de respaldo
    backup_dir = "/Volumes/My Passport/Dj compilation 2025/Respados mp3"
    
    # Archivo de prueba
    test_file = "/Volumes/My Passport/Dj compilation 2025/DMS/Mayo25/X-MIX CLUB CLASSICS BEST OF 320 (Seperated Tracks)/Cheryl Lynn - Got To Be Real ( Part 1 ) [RAndB].mp3"
    
    # Crear manejador de archivos
    file_handler = Mp3FileHandler(backup_dir=backup_dir)
    
    print(f"Directorio de respaldo configurado en: {file_handler.backup_dir}")
    
    # Verificar que el archivo existe
    if not os.path.exists(test_file):
        print(f"El archivo no existe: {test_file}")
        return
        
    # Leer etiquetas actuales
    tags = file_handler.read_tags(test_file)
    print(f"Etiquetas actuales: {tags}")
    
    # Escribir las mismas etiquetas para forzar un respaldo
    genres = ['RAndB', 'Disco']
    print(f"Escribiendo géneros: {genres}")
    
    success = file_handler.write_genre(test_file, genres)
    print(f"Resultado de la escritura: {'Éxito' if success else 'Error'}")
    
    # Verificar si se creó el respaldo
    print("\nVerificando archivos de respaldo:")
    backup_files = list(Path(backup_dir).glob("*"))
    print(f"Número de archivos de respaldo encontrados: {len(backup_files)}")
    for backup_file in backup_files:
        print(f"  - {backup_file.name}")

if __name__ == "__main__":
    test_backup()
