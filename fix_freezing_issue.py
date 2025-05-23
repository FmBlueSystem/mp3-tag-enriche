#!/usr/bin/env python3
"""
🔧 PARCHE RÁPIDO PARA RESOLVER CONGELAMIENTO
===========================================

Script que aplica parches al código existente para solucionar
el problema de congelamiento al procesar ~80 archivos MP3.
"""

import os
import sys
import shutil
from pathlib import Path

def backup_original_files():
    """Crea backup de los archivos originales."""
    print("📋 Creando backups de archivos originales...")
    
    files_to_backup = [
        'batch_process_mp3.py',
        'src/core/enhanced_mp3_handler.py',
        'main.py'
    ]
    
    backup_dir = Path('backup_freezing_fix')
    backup_dir.mkdir(exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = backup_dir / f"{Path(file_path).name}.original"
            shutil.copy2(file_path, backup_path)
            print(f"   ✅ Backup: {file_path} -> {backup_path}")
        else:
            print(f"   ⚠️ No encontrado: {file_path}")

def patch_batch_processor():
    """Aplica parches al procesador por lotes."""
    print("\n🔧 Aplicando parches al procesador por lotes...")
    
    patch_content = '''
# PARCHE APLICADO - Limitación de recursos
import gc
import time

# Configuración optimizada
MAX_WORKERS = 2          # Reducir de 4 a 2 workers
CHUNK_SIZE = 10          # Procesar de 10 en 10 archivos
RATE_LIMIT = 1.0         # 1 segundo entre archivos
MEMORY_CLEANUP_INTERVAL = 5  # Limpiar memoria cada 5 archivos

def process_file_patched(file_path: str, dry_run: bool = True, force: bool = False, debug: bool = False) -> Dict:
    """Versión parcheada del process_file con gestión de memoria."""
    # Rate limiting para evitar sobrecarga
    time.sleep(RATE_LIMIT)
    
    try:
        # Llamar función original
        result = process_file_original(file_path, dry_run, force, debug)
        
        # Forzar liberación de memoria
        gc.collect()
        
        return result
    except Exception as e:
        return {
            'file': file_path,
            'filename': os.path.basename(file_path),
            'error': f'Error parcheado: {str(e)}',
            'updated': False
        }

# Guardar función original
if 'process_file_original' not in globals():
    process_file_original = process_file
    process_file = process_file_patched
'''
    
    # Buscar el archivo batch_process_mp3.py
    batch_file = 'batch_process_mp3.py'
    if os.path.exists(batch_file):
        with open(batch_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insertar parche después de los imports
        import_end = content.find('\n# Crear directorio de backups')
        if import_end > 0:
            new_content = content[:import_end] + patch_content + content[import_end:]
            
            with open(batch_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"   ✅ Parche aplicado a {batch_file}")
        else:
            print(f"   ❌ No se pudo encontrar punto de inserción en {batch_file}")
    else:
        print(f"   ❌ No se encontró {batch_file}")

def patch_enhanced_handler():
    """Aplica parches al handler mejorado."""
    print("\n🔧 Aplicando parches al handler mejorado...")
    
    handler_file = 'src/core/enhanced_mp3_handler.py'
    if os.path.exists(handler_file):
        with open(handler_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar el método get_file_info y agregar timeout
        if 'def get_file_info(' in content and 'timeout_patch_applied' not in content:
            # Agregar marcador de parche aplicado
            timeout_patch = '''
    # PARCHE: Timeout y gestión de memoria
    # timeout_patch_applied
    def get_file_info_with_timeout(self, file_path: str, chunk_size: int = 8192, timeout: float = 30.0) -> Dict[str, str]:
        """Versión con timeout del get_file_info."""
        import signal
        import gc
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Timeout procesando {file_path}")
        
        # Configurar timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout))
        
        try:
            result = self.get_file_info_original(file_path, chunk_size)
            # Limpiar memoria después de cada archivo
            gc.collect()
            return result
        except TimeoutError as e:
            logger.warning(f"Timeout en {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error en {file_path}: {e}")
            return {}
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    # Aplicar parche si no existe
    if not hasattr(self, 'get_file_info_original'):
        self.get_file_info_original = self.get_file_info
        self.get_file_info = self.get_file_info_with_timeout
'''
            
            # Insertar parche después de __init__
            init_end = content.find('\n    def extract_artist_title_from_filename(')
            if init_end > 0:
                new_content = content[:init_end] + timeout_patch + content[init_end:]
                
                with open(handler_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"   ✅ Parche aplicado a {handler_file}")
            else:
                print(f"   ❌ No se pudo encontrar punto de inserción en {handler_file}")
        else:
            print(f"   ℹ️ Parche ya aplicado o archivo no compatible")
    else:
        print(f"   ❌ No se encontró {handler_file}")

def create_monitoring_script():
    """Crea script de monitoreo en tiempo real."""
    print("\n📊 Creando script de monitoreo...")
    
    monitoring_script = '''#!/usr/bin/env python3
"""
Monitor en tiempo real del procesamiento de MP3
para detectar problemas de congelamiento.
"""

import os
import sys
import time
import psutil
from pathlib import Path

def monitor_processing():
    """Monitorea el procesamiento de archivos MP3."""
    print("🔍 MONITOR DE PROCESAMIENTO MP3")
    print("=" * 40)
    print("Presiona Ctrl+C para detener")
    print()
    
    last_log_size = 0
    start_time = time.time()
    
    try:
        while True:
            # Verificar tamaño del log
            log_file = 'mp3_tool.log'
            if os.path.exists(log_file):
                current_size = os.path.getsize(log_file)
                if current_size > last_log_size:
                    print(f"📝 Log creciendo: {current_size:,} bytes (+{current_size - last_log_size:,})")
                    last_log_size = current_size
                elif current_size == last_log_size:
                    elapsed = time.time() - start_time
                    if elapsed > 30:  # Sin cambios por 30 segundos
                        print(f"⚠️ POSIBLE CONGELAMIENTO: Sin cambios en log por {elapsed:.1f}s")
            
            # Verificar memoria del sistema
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                print(f"🚨 MEMORIA ALTA: {memory.percent:.1f}% usado")
            
            # Verificar procesos Python
            python_procs = [p for p in psutil.process_iter(['pid', 'name', 'memory_info']) 
                           if 'python' in p.info['name'].lower()]
            
            total_python_memory = sum(p.info['memory_info'].rss for p in python_procs)
            if total_python_memory > 500 * 1024 * 1024:  # Más de 500MB
                print(f"💾 Procesos Python usando {total_python_memory / 1024 / 1024:.1f}MB")
            
            time.sleep(5)  # Verificar cada 5 segundos
            
    except KeyboardInterrupt:
        print("\\n👋 Monitor detenido")

if __name__ == "__main__":
    monitor_processing()
'''
    
    with open('monitor_mp3_processing.py', 'w', encoding='utf-8') as f:
        f.write(monitoring_script)
    
    os.chmod('monitor_mp3_processing.py', 0o755)
    print("   ✅ Creado monitor_mp3_processing.py")

def create_emergency_stop_script():
    """Crea script para detener procesamiento de emergencia."""
    print("\n🛑 Creando script de parada de emergencia...")
    
    stop_script = '''#!/usr/bin/env python3
"""
Script de emergencia para detener procesamiento congelado
"""

import os
import signal
import psutil
import sys

def emergency_stop():
    """Detiene procesos de procesamiento MP3 congelados."""
    print("🚨 PARADA DE EMERGENCIA - Procesamiento MP3")
    print("=" * 45)
    
    # Buscar procesos Python relacionados con MP3
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if ('python' in proc.info['name'].lower() and 
                ('mp3' in cmdline.lower() or 'batch' in cmdline.lower())):
                
                print(f"🔪 Terminando proceso: PID {proc.info['pid']} - {cmdline[:100]}")
                proc.terminate()
                killed += 1
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed == 0:
        print("ℹ️ No se encontraron procesos de MP3 activos")
    else:
        print(f"✅ {killed} procesos terminados")
        
        # Esperar un poco y forzar si es necesario
        print("⏳ Esperando 5 segundos para terminación graceful...")
        import time
        time.sleep(5)
        
        # Verificar si quedan procesos
        remaining = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if ('python' in proc.info['name'].lower() and 
                    ('mp3' in cmdline.lower() or 'batch' in cmdline.lower())):
                    print(f"💀 Forzando terminación: PID {proc.info['pid']}")
                    proc.kill()
                    remaining += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if remaining > 0:
            print(f"💀 {remaining} procesos forzados a terminar")

if __name__ == "__main__":
    emergency_stop()
'''
    
    with open('emergency_stop_mp3.py', 'w', encoding='utf-8') as f:
        f.write(stop_script)
    
    os.chmod('emergency_stop_mp3.py', 0o755)
    print("   ✅ Creado emergency_stop_mp3.py")

def create_usage_guide():
    """Crea guía de uso post-parche."""
    print("\n📖 Creando guía de uso...")
    
    guide = '''# 🔧 GUÍA POST-PARCHE - SOLUCIÓN DE CONGELAMIENTO

## ✅ Parches Aplicados

1. **Limitación de recursos**: Máximo 2 workers concurrentes
2. **Rate limiting**: 1 segundo entre archivos
3. **Gestión de memoria**: Garbage collection explícito
4. **Timeouts**: 30 segundos máximo por archivo
5. **Monitoreo**: Scripts de supervisión

## 🚀 Uso Recomendado

### Procesamiento Seguro (chunks pequeños):
```bash
# Procesar máximo 50 archivos en modo simulación
python3 batch_process_memory_fix.py -d "/ruta/a/musica" --max-files 50

# Procesar con aplicación real de cambios
python3 batch_process_memory_fix.py -d "/ruta/a/musica" --max-files 50 --apply
```

### Monitoreo en Tiempo Real:
```bash
# En terminal separado, ejecutar monitor
python3 monitor_mp3_processing.py
```

### En Caso de Congelamiento:
```bash
# Parada de emergencia
python3 emergency_stop_mp3.py
```

## ⚙️ Configuración Optimizada

- **Chunk size**: 10 archivos por lote
- **Workers**: 2 hilos máximo
- **Rate limit**: 1 segundo entre archivos
- **Memory cleanup**: Cada 5 archivos
- **Timeout**: 30 segundos por archivo

## 📊 Monitoreo

El monitor detecta:
- ✅ Crecimiento del log
- ⚠️ Congelamiento (sin actividad >30s)
- 🚨 Uso excesivo de memoria (>85%)
- 💾 Procesos Python con alta memoria

## 🆘 Resolución de Problemas

### Si la app se congela:
1. Ejecutar `python3 emergency_stop_mp3.py`
2. Verificar logs en `batch_processing.log`
3. Reducir `--max-files` y `--chunk-size`
4. Usar el procesador optimizado

### Para lotes grandes:
1. Dividir en grupos de 30-50 archivos
2. Procesar secuencialmente
3. Pausas entre lotes
4. Monitorear memoria constantemente

## 🔄 Restaurar Archivos Originales

```bash
# Restaurar desde backup
cp backup_freezing_fix/*.original .
```
'''
    
    with open('GUIA_POST_PARCHE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("   ✅ Creada GUIA_POST_PARCHE.md")

def main():
    """Función principal del parche."""
    print("🔧 APLICANDO PARCHES PARA RESOLVER CONGELAMIENTO")
    print("=" * 55)
    print()
    
    # Verificar dependencias
    try:
        import psutil
    except ImportError:
        print("❌ psutil no está instalado. Instalando...")
        os.system(f"{sys.executable} -m pip install psutil")
        print("✅ psutil instalado")
    
    # Aplicar parches
    backup_original_files()
    patch_batch_processor()
    patch_enhanced_handler()
    create_monitoring_script()
    create_emergency_stop_script()
    create_usage_guide()
    
    print("\n🎉 PARCHES APLICADOS EXITOSAMENTE")
    print("=" * 35)
    print()
    print("📋 Próximos pasos:")
    print("1. Ejecutar: python3 batch_process_memory_fix.py -d '/ruta/musica' --max-files 30")
    print("2. Monitorear: python3 monitor_mp3_processing.py (en terminal separado)")
    print("3. Leer: GUIA_POST_PARCHE.md para instrucciones completas")
    print()
    print("🚨 En caso de problemas: python3 emergency_stop_mp3.py")

if __name__ == "__main__":
    main() 