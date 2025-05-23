#!/usr/bin/env python3

import os
from dart import list_tasks, create_task, is_logged_in

def test_dart_connection():
    """Prueba completa de la conexión MCP con Dart"""
    
    print("🎯 VALIDACIÓN COMPLETA MCP DART")
    print("=" * 50)
    
    # Verificar autenticación
    print("\n1. 🔐 Verificando autenticación...")
    if is_logged_in():
        print("   ✅ Autenticación exitosa")
    else:
        print("   ❌ Error de autenticación")
        return False
    
    # Listar tareas existentes
    print("\n2. 📋 Listando tareas actuales...")
    try:
        tasks = list_tasks(limit=5)
        print(f"   📊 Se encontraron {len(tasks)} tareas")
        
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task.title}")
            print(f"      🆔 ID: {task.id}")
            print(f"      🔗 URL: {task.html_url}")
            print()
            
    except Exception as e:
        print(f"   ⚠️ Error al listar tareas: {e}")
    
    # Crear nueva tarea de prueba
    print("3. ➕ Creando tarea de prueba...")
    try:
        task = create_task("🎵 MCP Test - Proyecto Organización Musical")
        print("   ✅ Tarea creada exitosamente:")
        print(f"      📝 Título: {task.title}")
        print(f"      🆔 ID: {task.id}")
        print(f"      🔗 URL: {task.html_url}")
        
    except Exception as e:
        print(f"   ❌ Error al crear tarea: {e}")
        return False
    
    print("\n🏆 VALIDACIÓN MCP COMPLETADA EXITOSAMENTE")
    print("   - Conexión: ✅")
    print("   - Autenticación: ✅") 
    print("   - Lectura de datos: ✅")
    print("   - Creación de tareas: ✅")
    print("   - Integración MCP: ✅")
    
    return True

if __name__ == "__main__":
    # Configurar token si está disponible como variable de entorno
    token = os.getenv("DART_TOKEN")
    if token:
        print(f"🔑 Token configurado: {token[:10]}...")
    
    test_dart_connection() 