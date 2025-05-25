#!/usr/bin/env python3
"""
Script de instalación para Nueva Biblioteca.
Configura automáticamente el entorno y las dependencias.
"""
import sys
import subprocess
import os
from pathlib import Path


def print_banner():
    """Muestra el banner de instalación."""
    print("""
🎵 ═══════════════════════════════════════════════════════════════════════════════
   ███╗   ██╗██╗   ██╗███████╗██╗   ██╗ █████╗     ██████╗ ██╗██████╗ ██╗     
   ████╗  ██║██║   ██║██╔════╝██║   ██║██╔══██╗    ██╔══██╗██║██╔══██╗██║     
   ██╔██╗ ██║██║   ██║█████╗  ██║   ██║███████║    ██████╔╝██║██████╔╝██║     
   ██║╚██╗██║██║   ██║██╔══╝  ╚██╗ ██╔╝██╔══██║    ██╔══██╗██║██╔══██╗██║     
   ██║ ╚████║╚██████╔╝███████╗ ╚████╔╝ ██║  ██║    ██████╔╝██║██████╔╝███████╗
   ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝    ╚═════╝ ╚═╝╚═════╝ ╚══════╝
                                                                                
                    BIBLIOTECA - Sistema de Gestión Musical                    
                         con Material 3 Expressive Design                      
═══════════════════════════════════════════════════════════════════════════════ 🎵
""")


def check_python_version():
    """Verifica que la versión de Python sea compatible."""
    print("🔍 Verificando versión de Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Compatible")
    return True


def check_pip():
    """Verifica que pip esté disponible."""
    print("🔍 Verificando pip...")
    
    try:
        import pip
        print("✅ pip está disponible")
        return True
    except ImportError:
        print("❌ Error: pip no está instalado")
        return False


def create_virtual_environment():
    """Crea el entorno virtual."""
    print("🔧 Creando entorno virtual...")
    
    venv_path = Path("nueva_biblioteca_env")
    
    if venv_path.exists():
        print("⚠️  El entorno virtual ya existe")
        response = input("¿Desea recrearlo? (s/N): ").lower()
        if response == 's':
            import shutil
            shutil.rmtree(venv_path)
        else:
            print("✅ Usando entorno virtual existente")
            return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("✅ Entorno virtual creado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear entorno virtual: {e}")
        return False


def get_venv_python():
    """Obtiene la ruta del ejecutable Python del entorno virtual."""
    venv_path = Path("nueva_biblioteca_env")
    
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        return venv_path / "bin" / "python"


def install_dependencies():
    """Instala las dependencias necesarias."""
    print("📦 Instalando dependencias...")
    
    python_exe = get_venv_python()
    
    if not python_exe.exists():
        print("❌ Error: No se encontró el ejecutable Python del entorno virtual")
        return False
    
    dependencies = [
        "PySide6>=6.5.0",
        "qt-material>=2.14"
    ]
    
    for dep in dependencies:
        print(f"   Instalando {dep}...")
        try:
            subprocess.run([
                str(python_exe), "-m", "pip", "install", dep
            ], check=True, capture_output=True, text=True)
            print(f"   ✅ {dep} instalado")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error instalando {dep}: {e}")
            return False
    
    print("✅ Todas las dependencias instaladas correctamente")
    return True


def create_directories():
    """Crea los directorios necesarios."""
    print("📁 Creando directorios...")
    
    directories = [
        "data",
        "logs",
        "config",
        "cache"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"   ✅ {dir_name}/")
    
    print("✅ Directorios creados")


def create_desktop_shortcut():
    """Crea un acceso directo en el escritorio (opcional)."""
    print("🖥️  ¿Desea crear un acceso directo en el escritorio?")
    response = input("(s/N): ").lower()
    
    if response != 's':
        return
    
    try:
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Escritorio"  # Español
        
        if desktop.exists():
            shortcut_content = f"""#!/bin/bash
cd "{Path.cwd()}"
source nueva_biblioteca_env/bin/activate
python main.py
"""
            shortcut_path = desktop / "Nueva Biblioteca.sh"
            shortcut_path.write_text(shortcut_content)
            shortcut_path.chmod(0o755)
            print("✅ Acceso directo creado en el escritorio")
        else:
            print("⚠️  No se pudo encontrar el escritorio")
    except Exception as e:
        print(f"⚠️  No se pudo crear el acceso directo: {e}")


def show_completion_message():
    """Muestra el mensaje de finalización."""
    print("""
🎉 ═══════════════════════════════════════════════════════════════════════════════
                            ¡INSTALACIÓN COMPLETADA!                           
═══════════════════════════════════════════════════════════════════════════════

✨ Nueva Biblioteca está listo para usar con Material 3 Expressive

🚀 Para ejecutar la aplicación:

   1. Activar el entorno virtual:
      • Linux/macOS: source nueva_biblioteca_env/bin/activate
      • Windows:     nueva_biblioteca_env\\Scripts\\activate

   2. Ejecutar la aplicación:
      python main.py

📚 Características incluidas:
   • Interfaz Material 3 Expressive
   • Gestión inteligente de bibliotecas musicales
   • Búsqueda avanzada con autocompletado
   • Playlists inteligentes
   • Controles de reproductor expresivos
   • Configuración completa de preferencias

🎵 ¡Disfruta gestionando tu música con estilo!

═══════════════════════════════════════════════════════════════════════════════ 🎉
""")


def main():
    """Función principal del instalador."""
    print_banner()
    
    # Verificaciones previas
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    # Instalación
    steps = [
        ("Crear entorno virtual", create_virtual_environment),
        ("Instalar dependencias", install_dependencies),
        ("Crear directorios", create_directories),
        ("Configurar acceso directo", create_desktop_shortcut)
    ]
    
    print("\n🔧 Iniciando instalación...\n")
    
    for step_name, step_func in steps:
        print(f"📋 {step_name}...")
        if not step_func():
            print(f"\n❌ Error en: {step_name}")
            print("💡 Revise los mensajes de error anteriores")
            sys.exit(1)
        print()
    
    show_completion_message()


if __name__ == "__main__":
    main() 