#!/usr/bin/env python3
"""
🚀 INICIO RÁPIDO - SOLUCIÓN DE CONGELAMIENTO
===========================================

Script interactivo para resolver el problema de congelamiento
al procesar archivos MP3.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    """Muestra encabezado del script."""
    print()
    print("🎵" + "=" * 50 + "🎵")
    print("🚀 SOLUCIONADOR DE CONGELAMIENTO MP3")
    print("🎵" + "=" * 50 + "🎵")
    print()

def check_dependencies():
    """Verifica dependencias necesarias."""
    print("🔍 Verificando dependencias...")
    
    missing = []
    
    try:
        import psutil
        print("✅ psutil: Instalado")
    except ImportError:
        missing.append('psutil')
        print("❌ psutil: Faltante")
    
    # Verificar archivos necesarios
    required_files = [
        'simple_batch_processor.py',
        'monitor_mp3_processing.py',
        'emergency_stop_mp3.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}: Disponible")
        else:
            print(f"❌ {file}: Faltante")
            missing.append(file)
    
    if missing:
        print(f"\n⚠️ Faltan dependencias: {', '.join(missing)}")
        
        if 'psutil' in missing:
            print("📦 Instalando psutil...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil'])
        
        if any(f.endswith('.py') for f in missing):
            print("🔧 Ejecuta primero: python3 fix_freezing_issue.py")
            return False
    
    print("✅ Todas las dependencias están listas")
    return True

def get_directory():
    """Obtiene el directorio a procesar."""
    print("\n📁 SELECCIÓN DE DIRECTORIO")
    print("-" * 30)
    
    # Sugerir directorios comunes
    common_dirs = [
        "/Volumes/My Passport/Dj compilation 2025/DMS/DMS 80s",
        "/Volumes/My Passport/Dj compilation 2025/DMS",
        "/Users/" + os.getenv('USER', 'user') + "/Music",
        "/Volumes/My Passport"
    ]
    
    print("📋 Directorios sugeridos:")
    for i, dir_path in enumerate(common_dirs, 1):
        if os.path.exists(dir_path):
            print(f"   {i}. {dir_path} ✅")
        else:
            print(f"   {i}. {dir_path} ❌")
    
    print(f"   {len(common_dirs) + 1}. Escribir ruta personalizada")
    
    while True:
        try:
            choice = input(f"\n🎯 Selecciona opción (1-{len(common_dirs) + 1}): ").strip()
            
            if choice.isdigit():
                choice_int = int(choice)
                if 1 <= choice_int <= len(common_dirs):
                    selected_dir = common_dirs[choice_int - 1]
                    if os.path.exists(selected_dir):
                        return selected_dir
                    else:
                        print(f"❌ Directorio no existe: {selected_dir}")
                        continue
                elif choice_int == len(common_dirs) + 1:
                    custom_dir = input("📝 Escribe la ruta completa: ").strip()
                    if os.path.exists(custom_dir):
                        return custom_dir
                    else:
                        print(f"❌ Directorio no existe: {custom_dir}")
                        continue
            
            print("❌ Opción no válida. Intenta de nuevo.")
            
        except KeyboardInterrupt:
            print("\n👋 Cancelado por usuario")
            sys.exit(0)

def get_max_files():
    """Obtiene el número máximo de archivos a procesar."""
    print("\n📊 CONFIGURACIÓN DE LOTE")
    print("-" * 25)
    print("🎯 Recomendaciones por tamaño:")
    print("   • Hasta 30 archivos: Procesamiento rápido")
    print("   • 30-50 archivos: Procesamiento estándar")
    print("   • Más de 50: Dividir en múltiples lotes")
    
    while True:
        try:
            max_files = input("\n🔢 Número máximo de archivos (Enter para todos): ").strip()
            
            if not max_files:
                return None
            
            max_files_int = int(max_files)
            
            if max_files_int <= 0:
                print("❌ Debe ser un número positivo")
                continue
            
            if max_files_int > 100:
                confirm = input(f"⚠️ {max_files_int} archivos es mucho. ¿Continuar? (s/N): ").strip().lower()
                if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
                    continue
            
            return max_files_int
            
        except ValueError:
            print("❌ Debe ser un número válido")
        except KeyboardInterrupt:
            print("\n👋 Cancelado por usuario")
            sys.exit(0)

def choose_mode():
    """Elige el modo de procesamiento."""
    print("\n🎛️ MODO DE PROCESAMIENTO")
    print("-" * 25)
    print("1. 🔍 Solo analizar (recomendado para primera vez)")
    print("2. ✏️ Analizar y aplicar cambios")
    print("3. 📊 Solo monitorear sistema")
    print("4. 🛑 Detener procesos colgados")
    
    while True:
        try:
            mode = input("\n🎯 Selecciona modo (1-4): ").strip()
            
            if mode in ['1', '2', '3', '4']:
                return int(mode)
            
            print("❌ Opción no válida (1-4)")
            
        except KeyboardInterrupt:
            print("\n👋 Cancelado por usuario")
            sys.exit(0)

def run_processing(directory, max_files, apply_changes):
    """Ejecuta el procesamiento."""
    print(f"\n🚀 INICIANDO PROCESAMIENTO")
    print("-" * 30)
    print(f"📁 Directorio: {directory}")
    print(f"📊 Max archivos: {max_files or 'Todos'}")
    print(f"🎛️ Modo: {'APLICAR CAMBIOS' if apply_changes else 'SOLO ANALIZAR'}")
    print()
    
    # Construir comando
    cmd = [sys.executable, 'simple_batch_processor.py', '-d', directory]
    
    if max_files:
        cmd.extend(['--max-files', str(max_files)])
    
    if apply_changes:
        cmd.append('--apply')
    
    print(f"🔧 Comando: {' '.join(cmd)}")
    print()
    
    try:
        # Ejecutar comando
        subprocess.run(cmd, check=True)
        print("\n🎉 ¡Procesamiento completado exitosamente!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error en procesamiento: {e}")
        print("🔧 Intenta con menos archivos o usa modo monitoreo")
        
    except KeyboardInterrupt:
        print("\n🛑 Procesamiento interrumpido por usuario")

def run_monitor():
    """Ejecuta el monitor."""
    print("\n📊 INICIANDO MONITOR DEL SISTEMA")
    print("-" * 35)
    print("ℹ️ Presiona Ctrl+C para detener el monitor")
    print()
    
    try:
        subprocess.run([sys.executable, 'monitor_mp3_processing.py'])
    except KeyboardInterrupt:
        print("\n👋 Monitor detenido")
    except FileNotFoundError:
        print("❌ Script de monitoreo no encontrado")

def run_emergency_stop():
    """Ejecuta parada de emergencia."""
    print("\n🛑 PARADA DE EMERGENCIA")
    print("-" * 25)
    
    confirm = input("⚠️ ¿Detener todos los procesos MP3? (s/N): ").strip().lower()
    
    if confirm in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            subprocess.run([sys.executable, 'emergency_stop_mp3.py'])
        except FileNotFoundError:
            print("❌ Script de emergencia no encontrado")
    else:
        print("ℹ️ Parada de emergencia cancelada")

def main():
    """Función principal."""
    print_header()
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n❌ No se pueden ejecutar las herramientas")
        print("🔧 Ejecuta: python3 fix_freezing_issue.py")
        return
    
    # Elegir modo
    mode = choose_mode()
    
    if mode == 3:  # Monitor
        run_monitor()
        return
    
    if mode == 4:  # Emergencia
        run_emergency_stop()
        return
    
    # Para procesamiento (modos 1 y 2)
    directory = get_directory()
    max_files = get_max_files()
    apply_changes = (mode == 2)
    
    # Confirmación final
    print(f"\n✅ CONFIGURACIÓN FINAL")
    print("-" * 25)
    print(f"📁 Directorio: {directory}")
    print(f"📊 Max archivos: {max_files or 'Todos'}")
    print(f"🎛️ Modo: {'APLICAR CAMBIOS' if apply_changes else 'SOLO ANALIZAR'}")
    
    confirm = input("\n🚀 ¿Continuar? (S/n): ").strip().lower()
    
    if confirm in ['', 's', 'si', 'sí', 'y', 'yes']:
        run_processing(directory, max_files, apply_changes)
    else:
        print("ℹ️ Procesamiento cancelado")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Hasta luego!")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        print("🔧 Revisa SOLUCION_CONGELAMIENTO.md para ayuda") 