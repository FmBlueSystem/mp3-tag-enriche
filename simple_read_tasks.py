#!/usr/bin/env python3

import dart
from dart import Dart

def simple_read_tasks():
    """Leer tareas de OrganizacionMusical de forma simple y robusta"""
    
    print('🎵 LECTURA SIMPLE DE TAREAS ORGANIZACIONMUSICAL')
    print('=' * 60)
    
    if not dart.is_logged_in():
        print("❌ Error: No autenticado en Dart")
        return False
    
    print("✅ Autenticado en Dart IA")
    
    client = Dart()
    
    try:
        # Listar tareas
        print('\n📋 OBTENIENDO TAREAS...')
        tasks_response = client.list_tasks(limit=100)
        
        # Convertir a lista manejando diferentes tipos de respuesta
        if hasattr(tasks_response, 'results'):
            tasks = tasks_response.results
        else:
            tasks = list(tasks_response)
        
        print(f'✅ Total tareas encontradas: {len(tasks)}')
        
        # Palabras clave para filtrar tareas relacionadas
        keywords = [
            'organizacion', 'musical', 'i0RZbdogj0J2', 'mp3', 
            'genre', 'detector', 'revisión', 'análisis', 'acceso',
            'búsqueda', 'tareas', 'proyecto', 'dark ai', 'resumen',
            'lectura', 'completa'
        ]
        
        print('\n🎵 TAREAS RELACIONADAS CON ORGANIZACIONMUSICAL:')
        print('=' * 60)
        
        org_tasks = []
        for i, task in enumerate(tasks):
            try:
                task_title_lower = task.title.lower()
                if any(keyword in task_title_lower for keyword in keywords):
                    org_tasks.append(task)
                    
                    print(f'\n📋 TAREA #{len(org_tasks)}:')
                    print(f'   📝 Título: {task.title}')
                    print(f'   🆔 ID: {task.id}')
                    print(f'   🔗 URL: {task.html_url}')
                    print(f'   📅 Creado: {task.created_at}')
                    
                    # Intentar obtener más detalles de forma segura
                    try:
                        task_detail = client.get_task(task.id)
                        
                        # Estado
                        if hasattr(task_detail, 'status') and task_detail.status:
                            status_name = getattr(task_detail.status, 'title', str(task_detail.status))
                            print(f'   📊 Estado: {status_name}')
                        
                        # Descripción
                        if hasattr(task_detail, 'description') and task_detail.description:
                            desc = task_detail.description[:200] + "..." if len(task_detail.description) > 200 else task_detail.description
                            print(f'   📋 Descripción: {desc}')
                        
                        # Prioridad
                        if hasattr(task_detail, 'priority') and task_detail.priority:
                            priority_name = getattr(task_detail.priority, 'title', str(task_detail.priority))
                            print(f'   🎯 Prioridad: {priority_name}')
                            
                    except Exception as detail_error:
                        print(f'   ⚠️ No se pudieron obtener detalles adicionales: {detail_error}')
                        
            except Exception as task_error:
                print(f'   ❌ Error procesando tarea {i}: {task_error}')
                continue
        
        print(f'\n📊 RESUMEN DE TAREAS:')
        print(f'   📋 Total tareas revisadas: {len(tasks)}')
        print(f'   🎵 Tareas OrganizacionMusical: {len(org_tasks)}')
        
        # Listar documentos de forma similar
        print('\n📄 OBTENIENDO DOCUMENTOS...')
        docs_response = client.list_docs(limit=50)
        
        if hasattr(docs_response, 'results'):
            docs = docs_response.results
        else:
            docs = list(docs_response)
            
        print(f'✅ Total documentos encontrados: {len(docs)}')
        
        print('\n📄 DOCUMENTOS RELACIONADOS CON ORGANIZACIONMUSICAL:')
        print('=' * 60)
        
        org_docs = []
        for i, doc in enumerate(docs):
            try:
                doc_title_lower = doc.title.lower()
                if any(keyword in doc_title_lower for keyword in keywords):
                    org_docs.append(doc)
                    
                    print(f'\n📄 DOCUMENTO #{len(org_docs)}:')
                    print(f'   📝 Título: {doc.title}')
                    print(f'   🆔 ID: {doc.id}')
                    print(f'   🔗 URL: {doc.html_url}')
                    print(f'   📅 Creado: {doc.created_at}')
                    
                    # Intentar obtener contenido de forma segura
                    try:
                        doc_detail = client.get_doc(doc.id)
                        if hasattr(doc_detail, 'text') and doc_detail.text:
                            # Mostrar primeras líneas
                            lines = [line.strip() for line in doc_detail.text.split('\n')[:3] if line.strip()]
                            if lines:
                                print(f'   📝 Contenido (preview):')
                                for line in lines:
                                    preview_line = line[:100] + "..." if len(line) > 100 else line
                                    print(f'      {preview_line}')
                                    
                    except Exception as doc_error:
                        print(f'   ⚠️ No se pudo obtener contenido: {doc_error}')
                        
            except Exception as doc_error:
                print(f'   ❌ Error procesando documento {i}: {doc_error}')
                continue
        
        print(f'\n📊 RESUMEN DE DOCUMENTOS:')
        print(f'   📄 Total documentos revisados: {len(docs)}')
        print(f'   🎵 Documentos OrganizacionMusical: {len(org_docs)}')
        
        # Análisis específico del proyecto i0RZbdogj0J2
        print('\n🎯 ANÁLISIS ESPECÍFICO DEL PROYECTO:')
        print('=' * 50)
        
        i0_items = [item for item in org_tasks + org_docs if 'i0RZbdogj0J2' in item.title.lower()]
        genre_items = [item for item in org_tasks + org_docs if any(word in item.title.lower() for word in ['genre', 'detector', 'musical'])]
        review_items = [item for item in org_tasks + org_docs if any(word in item.title.lower() for word in ['revisión', 'análisis', 'resumen'])]
        
        print(f'🎵 Items con ID i0RZbdogj0J2: {len(i0_items)}')
        print(f'🎵 Items relacionados con Genre Detector: {len(genre_items)}')
        print(f'🎵 Items de revisión/análisis: {len(review_items)}')
        
        # Crear tarea de confirmación de lectura
        print('\n✅ Creando confirmación de lectura...')
        try:
            summary_task = dart.create_task('✅ CONFIRMADO: Lectura completa tareas OrganizacionMusical')
            print(f'   ✅ Tarea de confirmación creada: {summary_task.id}')
            print(f'   🔗 URL: {summary_task.html_url}')
        except Exception as e:
            print(f'   ⚠️ No se pudo crear confirmación: {e}')
        
        print('\n🏆 LECTURA COMPLETADA EXITOSAMENTE')
        print('=' * 40)
        print(f'📋 Tareas OrganizacionMusical: {len(org_tasks)}')
        print(f'📄 Documentos OrganizacionMusical: {len(org_docs)}')
        print(f'🎯 Total items del proyecto: {len(org_tasks) + len(org_docs)}')
        
        return org_tasks, org_docs
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    simple_read_tasks() 