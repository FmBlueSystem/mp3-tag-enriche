#!/usr/bin/env python3
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
        print("\n👋 Monitor detenido")

if __name__ == "__main__":
    monitor_processing()
