#!/usr/bin/env python3

import dart
from dart import Dart
from datetime import datetime

def read_organizational_tasks():
    """Leer todas las tareas relacionadas con OrganizacionMusical"""
    
    print('🎵 LEYENDO TAREAS DE ORGANIZACIONMUSICAL')
    print('=' * 60)
    
    # Verificar autenticación
    if not dart.is_logged_in():
        print("❌ Error: No autenticado en Dart")
        return False
    
    print("✅ Autenticado en Dart IA")
    
    # Usar el cliente Dart directamente
    client = Dart()
    
    try:
        # Obtener configuración del espacio
        print('\n1. 🔧 Obteniendo configuración del espacio...')
        config = client.get_config()
        print(f'   ✅ Configuración obtenida')
        
        if hasattr(config, 'assignees') and config.assignees:
            print(f'   👥 Asignados disponibles: {len(config.assignees)}')
            for assignee in config.assignees[:3]:
                print(f'      • {assignee.display_name}')
                
        if hasattr(config, 'statuses') and config.statuses:
            print(f'   📊 Estados disponibles: {len(config.statuses)}')
            for status in config.statuses[:5]:
                print(f'      • {status.title}')
                
        if hasattr(config, 'dartboards') and config.dartboards:
            print(f'   📋 Dartboards disponibles: {len(config.dartboards)}')
            for board in config.dartboards[:3]:
                print(f'      • {board.title}')
        
        # Listar tareas - usar el objeto paginado correctamente
        print('\n2. 📋 Listando tareas...')
        tasks_response = client.list_tasks(limit=100)
        
        # Extraer la lista de tareas del objeto paginado
        if hasattr(tasks_response, 'results'):
            tasks = tasks_response.results
        else:
            tasks = list(tasks_response)  # Convertir a lista si es iterable
        
        print(f'   ✅ Tareas encontradas: {len(tasks)}')
        
        # Filtrar tareas relacionadas con OrganizacionMusical
        print('\n🎵 TAREAS RELACIONADAS CON ORGANIZACIONMUSICAL:')
        print('-' * 60)
        
        project_keywords = [
            'organizacion', 'musical', 'i0RZbdogj0J2', 'mp3', 
            'genre', 'detector', 'revisión', 'análisis', 'acceso',
            'búsqueda', 'tareas', 'proyecto', 'dark ai', 'resumen'
        ]
        
        org_musical_tasks = []
        for task in tasks:
            task_title_lower = task.title.lower()
            if any(keyword in task_title_lower for keyword in project_keywords):
                org_musical_tasks.append(task)
                
                print(f'📋 {task.title}')
                print(f'   🆔 ID: {task.id}')
                print(f'   🔗 URL: {task.html_url}')
                print(f'   📅 Creado: {task.created_at}')
                
                # Obtener detalles adicionales de la tarea
                try:
                    task_detail = client.get_task(task.id)
                    if hasattr(task_detail, 'status') and task_detail.status:
                        print(f'   📊 Estado: {task_detail.status.title}')
                    if hasattr(task_detail, 'description') and task_detail.description:
                        desc = task_detail.description[:150] + "..." if len(task_detail.description) > 150 else task_detail.description
                        print(f'   📝 Descripción: {desc}')
                    if hasattr(task_detail, 'assignees') and task_detail.assignees:
                        assignees = [a.display_name for a in task_detail.assignees]
                        print(f'   👥 Asignados: {", ".join(assignees)}')
                    if hasattr(task_detail, 'priority') and task_detail.priority:
                        print(f'   🎯 Prioridad: {task_detail.priority.title}')
                        
                except Exception as e:
                    print(f'   ⚠️ No se pudieron obtener detalles: {e}')
                
                print()
        
        print(f'📈 Tareas OrganizacionMusical encontradas: {len(org_musical_tasks)}')
        
        # Listar documentos relacionados
        print('\n3. 📄 Listando documentos...')
        docs_response = client.list_docs(limit=50)
        
        # Extraer la lista de documentos del objeto paginado
        if hasattr(docs_response, 'results'):
            docs = docs_response.results
        else:
            docs = list(docs_response)
        
        print(f'   ✅ Documentos encontrados: {len(docs)}')
        
        print('\n📄 DOCUMENTOS RELACIONADOS CON ORGANIZACIONMUSICAL:')
        print('-' * 60)
        
        org_musical_docs = []
        for doc in docs:
            doc_title_lower = doc.title.lower()
            if any(keyword in doc_title_lower for keyword in project_keywords):
                org_musical_docs.append(doc)
                
                print(f'📄 {doc.title}')
                print(f'   🆔 ID: {doc.id}')
                print(f'   🔗 URL: {doc.html_url}')
                print(f'   📅 Creado: {doc.created_at}')
                
                # Obtener contenido del documento
                try:
                    doc_detail = client.get_doc(doc.id)
                    if hasattr(doc_detail, 'text') and doc_detail.text:
                        # Mostrar las primeras líneas del contenido
                        lines = doc_detail.text.split('\n')[:3]
                        print(f'   📝 Contenido (preview):')
                        for line in lines:
                            if line.strip():
                                print(f'      {line[:80]}{"..." if len(line) > 80 else ""}')
                                
                except Exception as e:
                    print(f'   ⚠️ No se pudo obtener contenido: {e}')
                
                print()
        
        print(f'📊 Documentos OrganizacionMusical encontrados: {len(org_musical_docs)}')
        
        # Resumen final
        print('\n🏆 RESUMEN FINAL:')
        print('=' * 40)
        print(f'📋 Total tareas: {len(tasks)}')
        print(f'🎵 Tareas OrganizacionMusical: {len(org_musical_tasks)}')
        print(f'📄 Total documentos: {len(docs)}')
        print(f'🎵 Documentos OrganizacionMusical: {len(org_musical_docs)}')
        
        # Mostrar información específica del proyecto i0RZbdogj0J2
        print('\n🎯 INFORMACIÓN ESPECÍFICA DEL PROYECTO i0RZbdogj0J2:')
        print('-' * 50)
        
        i0_tasks = [t for t in org_musical_tasks if 'i0RZbdogj0J2' in t.title.lower()]
        if i0_tasks:
            print(f'📋 Tareas específicas del proyecto: {len(i0_tasks)}')
            for task in i0_tasks:
                print(f'   • {task.title} (ID: {task.id})')
        else:
            print('📋 No se encontraron tareas específicas con ID i0RZbdogj0J2')
            
        # Buscar tareas por contenido relacionado
        genre_tasks = [t for t in org_musical_tasks if any(word in t.title.lower() for word in ['genre', 'detector', 'musical'])]
        print(f'🎵 Tareas relacionadas con Genre Detector: {len(genre_tasks)}')
        for task in genre_tasks[:5]:  # Mostrar las primeras 5
            print(f'   • {task.title} (ID: {task.id})')
        
        # Crear tarea de resumen
        print('\n✅ Creando tarea de resumen...')
        try:
            summary_task = dart.create_task('📋 LECTURA COMPLETA: Tareas OrganizacionMusical')
            print(f'   ✅ Tarea de resumen creada: {summary_task.id}')
            print(f'   🔗 URL: {summary_task.html_url}')
        except Exception as e:
            print(f'   ⚠️ No se pudo crear tarea de resumen: {e}')
        
        return org_musical_tasks, org_musical_docs
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    read_organizational_tasks() 