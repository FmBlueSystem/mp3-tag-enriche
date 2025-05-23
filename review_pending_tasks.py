#!/usr/bin/env python3

import dart
from dart import Dart

def review_pending_tasks():
    """Revisar tareas pendientes y por realizar del proyecto OrganizacionMusical"""
    
    print('📋 REVISIÓN DE TAREAS PENDIENTES - ORGANIZACIONMUSICAL')
    print('=' * 70)
    
    if not dart.is_logged_in():
        print("❌ Error: No autenticado en Dart")
        return False
    
    print("✅ Autenticado en Dart IA")
    
    client = Dart()
    
    try:
        # Obtener configuración para conocer los estados disponibles
        print('\n🔧 Obteniendo configuración del espacio...')
        config = client.get_config()
        
        # Mostrar estados disponibles
        if hasattr(config, 'statuses') and config.statuses:
            print(f'📊 Estados disponibles en el espacio:')
            for status in config.statuses:
                status_name = getattr(status, 'title', str(status))
                print(f'   • {status_name}')
        
        # Listar tareas
        print('\n📋 Obteniendo todas las tareas...')
        tasks_response = client.list_tasks(limit=100)
        
        if hasattr(tasks_response, 'results'):
            tasks = tasks_response.results
        else:
            tasks = list(tasks_response)
        
        print(f'✅ Total tareas encontradas: {len(tasks)}')
        
        # Filtrar tareas relacionadas con OrganizacionMusical
        keywords = [
            'organizacion', 'musical', 'i0RZbdogj0J2', 'mp3', 
            'genre', 'detector', 'revisión', 'análisis', 'acceso',
            'búsqueda', 'tareas', 'proyecto', 'dark ai', 'resumen',
            'lectura', 'completa', 'validación', 'mcp'
        ]
        
        org_tasks = []
        for task in tasks:
            task_title_lower = task.title.lower()
            if any(keyword in task_title_lower for keyword in keywords):
                org_tasks.append(task)
        
        print(f'🎵 Tareas relacionadas con OrganizacionMusical: {len(org_tasks)}')
        
        # Categorizar tareas por estado
        print('\n🔍 ANALIZANDO ESTADO DE TAREAS...')
        print('=' * 50)
        
        pending_tasks = []
        in_progress_tasks = []
        completed_tasks = []
        unknown_status_tasks = []
        
        for i, task in enumerate(org_tasks):
            try:
                print(f'\n📋 Analizando tarea {i+1}/{len(org_tasks)}: {task.title[:50]}...')
                
                # Obtener detalles completos de la tarea
                task_detail = client.get_task(task.id)
                
                # Determinar estado
                status_info = "Sin estado definido"
                if hasattr(task_detail, 'status') and task_detail.status:
                    status_name = getattr(task_detail.status, 'title', str(task_detail.status))
                    status_info = status_name
                    
                    # Categorizar según el estado
                    status_lower = status_name.lower()
                    if any(word in status_lower for word in ['pending', 'pendiente', 'todo', 'por hacer', 'new', 'nuevo']):
                        pending_tasks.append((task, task_detail, status_info))
                    elif any(word in status_lower for word in ['progress', 'progreso', 'doing', 'haciendo', 'working', 'trabajando']):
                        in_progress_tasks.append((task, task_detail, status_info))
                    elif any(word in status_lower for word in ['done', 'hecho', 'completed', 'completado', 'finished', 'terminado']):
                        completed_tasks.append((task, task_detail, status_info))
                    else:
                        unknown_status_tasks.append((task, task_detail, status_info))
                else:
                    unknown_status_tasks.append((task, task_detail, status_info))
                
                print(f'   📊 Estado: {status_info}')
                
            except Exception as e:
                print(f'   ❌ Error obteniendo detalles: {e}')
                unknown_status_tasks.append((task, None, "Error al obtener estado"))
        
        # Mostrar resumen de categorización
        print(f'\n📊 RESUMEN DE ESTADOS:')
        print('=' * 40)
        print(f'⏳ Tareas pendientes: {len(pending_tasks)}')
        print(f'🔄 Tareas en progreso: {len(in_progress_tasks)}')
        print(f'✅ Tareas completadas: {len(completed_tasks)}')
        print(f'❓ Estado desconocido: {len(unknown_status_tasks)}')
        
        # Mostrar tareas pendientes en detalle
        print(f'\n⏳ TAREAS PENDIENTES POR REALIZAR:')
        print('=' * 60)
        
        if pending_tasks:
            for i, (task, task_detail, status) in enumerate(pending_tasks):
                print(f'\n📋 TAREA PENDIENTE #{i+1}:')
                print(f'   📝 Título: {task.title}')
                print(f'   🆔 ID: {task.id}')
                print(f'   🔗 URL: {task.html_url}')
                print(f'   📊 Estado: {status}')
                
                if task_detail:
                    # Descripción
                    if hasattr(task_detail, 'description') and task_detail.description:
                        desc = task_detail.description[:200] + "..." if len(task_detail.description) > 200 else task_detail.description
                        print(f'   📋 Descripción: {desc}')
                    
                    # Prioridad
                    if hasattr(task_detail, 'priority') and task_detail.priority:
                        priority_name = getattr(task_detail.priority, 'title', str(task_detail.priority))
                        print(f'   🎯 Prioridad: {priority_name}')
                    
                    # Asignados
                    if hasattr(task_detail, 'assignees') and task_detail.assignees:
                        assignees = []
                        for assignee in task_detail.assignees:
                            name = getattr(assignee, 'display_name', getattr(assignee, 'name', str(assignee)))
                            assignees.append(name)
                        print(f'   👥 Asignados: {", ".join(assignees)}')
        else:
            print('   ✅ No hay tareas específicamente marcadas como pendientes')
        
        # Mostrar tareas en progreso
        print(f'\n🔄 TAREAS EN PROGRESO:')
        print('=' * 40)
        
        if in_progress_tasks:
            for i, (task, task_detail, status) in enumerate(in_progress_tasks):
                print(f'\n📋 TAREA EN PROGRESO #{i+1}:')
                print(f'   📝 Título: {task.title}')
                print(f'   🆔 ID: {task.id}')
                print(f'   📊 Estado: {status}')
        else:
            print('   ℹ️ No hay tareas específicamente en progreso')
        
        # Mostrar tareas con estado desconocido (potencialmente pendientes)
        print(f'\n❓ TAREAS CON ESTADO DESCONOCIDO (REVISAR):')
        print('=' * 50)
        
        if unknown_status_tasks:
            for i, (task, task_detail, status) in enumerate(unknown_status_tasks[:10]):  # Mostrar solo primeras 10
                print(f'\n📋 TAREA #{i+1}:')
                print(f'   📝 Título: {task.title}')
                print(f'   🆔 ID: {task.id}')
                print(f'   📊 Estado: {status}')
                print(f'   💡 Recomendación: Revisar y asignar estado apropiado')
        
        # Identificar tareas críticas por palabras clave
        print(f'\n🚨 TAREAS CRÍTICAS IDENTIFICADAS:')
        print('=' * 45)
        
        critical_keywords = ['implementar', 'desarrollar', 'crear', 'completar', 'mejorar', 'gestionar']
        critical_tasks = []
        
        for task, task_detail, status in pending_tasks + unknown_status_tasks:
            task_title_lower = task.title.lower()
            if any(keyword in task_title_lower for keyword in critical_keywords):
                critical_tasks.append((task, task_detail, status))
        
        if critical_tasks:
            for i, (task, task_detail, status) in enumerate(critical_tasks):
                print(f'\n🚨 TAREA CRÍTICA #{i+1}:')
                print(f'   📝 Título: {task.title}')
                print(f'   🆔 ID: {task.id}')
                print(f'   📊 Estado: {status}')
                print(f'   ⚠️ Requiere atención prioritaria')
        else:
            print('   ✅ No se identificaron tareas críticas pendientes')
        
        # Crear tarea de reporte
        print(f'\n📝 Creando reporte de tareas pendientes...')
        try:
            report_task = dart.create_task('📋 REPORTE: Tareas Pendientes OrganizacionMusical')
            print(f'   ✅ Reporte creado: {report_task.id}')
            print(f'   🔗 URL: {report_task.html_url}')
        except Exception as e:
            print(f'   ⚠️ No se pudo crear reporte: {e}')
        
        # Resumen final
        print(f'\n🏆 RESUMEN FINAL DE REVISIÓN:')
        print('=' * 45)
        print(f'📋 Total tareas del proyecto: {len(org_tasks)}')
        print(f'⏳ Tareas pendientes: {len(pending_tasks)}')
        print(f'🔄 Tareas en progreso: {len(in_progress_tasks)}')
        print(f'✅ Tareas completadas: {len(completed_tasks)}')
        print(f'❓ Requieren revisión de estado: {len(unknown_status_tasks)}')
        print(f'🚨 Tareas críticas identificadas: {len(critical_tasks)}')
        
        # Recomendaciones
        print(f'\n💡 RECOMENDACIONES:')
        print('-' * 30)
        if pending_tasks:
            print(f'1. Revisar y priorizar {len(pending_tasks)} tareas pendientes')
        if in_progress_tasks:
            print(f'2. Dar seguimiento a {len(in_progress_tasks)} tareas en progreso')
        if unknown_status_tasks:
            print(f'3. Definir estado para {len(unknown_status_tasks)} tareas sin clasificar')
        if critical_tasks:
            print(f'4. Atender prioritariamente {len(critical_tasks)} tareas críticas')
        
        return {
            'pending': pending_tasks,
            'in_progress': in_progress_tasks,
            'completed': completed_tasks,
            'unknown': unknown_status_tasks,
            'critical': critical_tasks
        }
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    review_pending_tasks() 