#!/usr/bin/env python3

import dart
import inspect

def explore_dart_api():
    """Explorar la API de Dart y buscar tareas relacionadas"""
    
    print('🔍 EXPLORANDO API DE DART')
    print('=' * 40)
    
    # Verificar autenticación
    if not dart.is_logged_in():
        print("❌ Error: No autenticado en Dart")
        return False
    
    print("✅ Autenticado en Dart IA")
    
    # Explorar métodos disponibles
    print('\n📋 MÉTODOS DISPONIBLES EN DART:')
    print('-' * 30)
    
    dart_methods = [method for method in dir(dart) if not method.startswith('_')]
    for method in dart_methods:
        print(f'   • {method}')
    
    print('\n🎯 INTENTANDO DIFERENTES MÉTODOS PARA OBTENER TAREAS:')
    print('-' * 50)
    
    # Intentar obtener información de configuración
    try:
        print('\n1. 🔧 Obteniendo configuración...')
        config = dart.get_config()
        print(f'   ✅ Configuración obtenida: {type(config)}')
        if hasattr(config, 'assignees'):
            print(f'   👥 Asignados disponibles: {len(config.assignees)}')
        if hasattr(config, 'statuses'):
            print(f'   📊 Estados disponibles: {len(config.statuses)}')
    except Exception as e:
        print(f'   ❌ Error obteniendo configuración: {e}')
    
    # Intentar crear una tarea de búsqueda
    try:
        print('\n2. 📋 Creando tarea de búsqueda...')
        search_task = dart.create_task('🔍 Búsqueda: Tareas OrganizacionMusical')
        print(f'   ✅ Tarea creada: {search_task.id}')
        print(f'   🔗 URL: {search_task.html_url}')
        
        # Intentar obtener detalles de la tarea
        task_detail = dart.get_task(search_task.id)
        print(f'   📝 Título: {task_detail.title}')
        
    except Exception as e:
        print(f'   ❌ Error creando/obteniendo tarea: {e}')
    
    # Intentar listar documentos
    try:
        print('\n3. 📄 Listando documentos...')
        docs = dart.list_docs()
        print(f'   ✅ Documentos encontrados: {len(docs)}')
        
        print('\n📄 DOCUMENTOS RELACIONADOS CON ORGANIZACIONMUSICAL:')
        print('-' * 50)
        
        project_keywords = [
            'organizacion', 'musical', 'i0RZbdogj0J2', 'mp3', 
            'genre', 'detector', 'revisión', 'análisis', 'acceso'
        ]
        
        relevant_docs = []
        for doc in docs:
            doc_title_lower = doc.title.lower()
            if any(keyword in doc_title_lower for keyword in project_keywords):
                relevant_docs.append(doc)
                print(f'📄 {doc.title}')
                print(f'   🆔 ID: {doc.id}')
                print(f'   🔗 URL: {doc.html_url}')
                print(f'   📅 Creado: {doc.created_at}')
                
                # Intentar obtener el contenido del documento
                try:
                    doc_detail = dart.get_doc(doc.id)
                    if hasattr(doc_detail, 'text') and doc_detail.text:
                        preview = doc_detail.text[:200] + "..." if len(doc_detail.text) > 200 else doc_detail.text
                        print(f'   📝 Vista previa: {preview}')
                except Exception as e:
                    print(f'   ⚠️ No se pudo obtener contenido: {e}')
                print()
        
        print(f'\n📊 RESUMEN DE DOCUMENTOS:')
        print(f'   Total documentos: {len(docs)}')
        print(f'   Documentos relacionados: {len(relevant_docs)}')
        
    except Exception as e:
        print(f'   ❌ Error listando documentos: {e}')
    
    # Intentar buscar usando el cliente Dart directamente
    try:
        print('\n4. 🎯 Usando cliente Dart directo...')
        from dart import Dart
        client = Dart()
        print(f'   ✅ Cliente Dart inicializado: {type(client)}')
        
        # Explorar métodos del cliente
        client_methods = [method for method in dir(client) if not method.startswith('_')]
        print(f'   📋 Métodos del cliente: {client_methods[:10]}...')  # Mostrar solo los primeros 10
        
    except Exception as e:
        print(f'   ❌ Error con cliente Dart: {e}')

if __name__ == "__main__":
    explore_dart_api() 