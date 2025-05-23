#!/usr/bin/env python3

import dart
import json

def list_organizational_tasks():
    """Listar todas las tareas relacionadas con OrganizacionMusical"""
    
    print('🔍 LISTANDO TAREAS RELACIONADAS CON ORGANIZACIONMUSICAL')
    print('=' * 60)
    
    # Verificar autenticación
    if not dart.is_logged_in():
        print("❌ Error: No autenticado en Dart")
        return False
    
    print("✅ Autenticado en Dart IA")
    
    try:
        # Listar todas las tareas
        tasks = dart.list_tasks(limit=100)
        print(f'📊 Total de tareas encontradas: {len(tasks)}')
        
        print('\n🎵 TAREAS RELACIONADAS CON ORGANIZACIONMUSICAL:')
        print('-' * 50)
        
        org_musical_tasks = []
        project_keywords = [
            'organizacion', 'musical', 'i0RZbdogj0J2', 'mp3', 
            'genre', 'detector', 'revisión', 'análisis', 'acceso'
        ]
        
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
                    task_detail = dart.get_task(task.id)
                    if hasattr(task_detail, 'status') and task_detail.status:
                        print(f'   📊 Estado: {task_detail.status}')
                    if hasattr(task_detail, 'description') and task_detail.description:
                        desc = task_detail.description[:100] + "..." if len(task_detail.description) > 100 else task_detail.description
                        print(f'   📝 Descripción: {desc}')
                except Exception as e:
                    print(f'   ⚠️ No se pudieron obtener detalles: {e}')
                
                print()
        
        print(f'\n📈 RESUMEN:')
        print(f'   Total tareas OrganizacionMusical: {len(org_musical_tasks)}')
        
        # Listar documentos relacionados también
        print('\n📄 DOCUMENTOS RELACIONADOS:')
        print('-' * 50)
        
        docs = dart.list_docs(limit=50)
        org_musical_docs = []
        
        for doc in docs:
            doc_title_lower = doc.title.lower()
            if any(keyword in doc_title_lower for keyword in project_keywords):
                org_musical_docs.append(doc)
                print(f'📄 {doc.title}')
                print(f'   🆔 ID: {doc.id}')
                print(f'   🔗 URL: {doc.html_url}')
                print(f'   📅 Creado: {doc.created_at}')
                print()
        
        print(f'\n📊 RESUMEN FINAL:')
        print(f'   📋 Tareas: {len(org_musical_tasks)}')
        print(f'   📄 Documentos: {len(org_musical_docs)}')
        
        return org_musical_tasks, org_musical_docs
        
    except Exception as e:
        print(f"❌ Error listando tareas: {e}")
        return None, None

if __name__ == "__main__":
    list_organizational_tasks() 