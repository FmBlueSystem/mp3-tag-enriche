#!/usr/bin/env python3
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
