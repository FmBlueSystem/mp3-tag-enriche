#!/usr/bin/env python3

import dart
from dart import Dart

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
        if hasattr(config, 'statuses') and config.statuses:
            print(f'   📊 Estados disponibles: {len(config.statuses)}')
            for status in config.statuses[:5]:  # Mostrar primeros 5
                print(f'      • {status.title}')
        if hasattr(config, 'dartboards') and config.dartboards:
            print(f'   📋 Dartboards disponibles: {len(config.dartboards)}')
            for board in config.dartboards[:3]:  # Mostrar primeros 3
                print(f'      • {board.title}')
        
        # Listar tareas
        print('\n2. 📋 Listando tareas...')
        tasks = client.list_tasks(limit=100)
        print(f'   ✅ Tareas encontradas: {len(tasks)}')
        
        # Filtrar tareas relacionadas con OrganizacionMusical
        print('\n🎵 TAREAS RELACIONADAS CON ORGANIZACIONMUSICAL:')
        print('-' * 60)
        
        project_keywords = [
            'organizacion', 'musical', 'i0RZbdogj0J2', 'mp3', 
            'genre', 'detector', 'revisión', 'análisis', 'acceso',
            'búsqueda', 'tareas', 'proyecto', 'dark ai'
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
        docs = client.list_docs(limit=50)
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
                        lines = doc_detail.text.split('\n')[:5]
                        preview = '\n'.join(lines)
                        if len(doc_detail.text) > 300:
                            preview += "\n..."
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
        
        # Crear tarea de resumen
        print('\n✅ Creando tarea de resumen...')
        summary_content = f"""# 📋 Resumen de Tareas OrganizacionMusical

## 🎯 Proyecto i0RZbdogj0J2 - Genre Detector Dark AI

### 📊 Estadísticas Encontradas:
- **📋 Tareas relacionadas**: {len(org_musical_tasks)}
- **📄 Documentos relacionados**: {len(org_musical_docs)}
- **🔍 Búsqueda realizada**: {len(tasks)} tareas y {len(docs)} documentos revisados

### 🎵 Tareas Identificadas:
"""
        for task in org_musical_tasks[:10]:  # Primeras 10 tareas
            summary_content += f"- **{task.title}** (ID: {task.id})\n"
        
        summary_content += f"""
### 📄 Documentos Identificados:
"""
        for doc in org_musical_docs[:10]:  # Primeros 10 documentos
            summary_content += f"- **{doc.title}** (ID: {doc.id})\n"
        
        summary_content += f"""
---
*Resumen generado automáticamente via MCP Dart*
*Fecha: {dart.annotations.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""
        
        try:
            summary_task = dart.create_task('📋 RESUMEN: Tareas OrganizacionMusical Leídas')
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