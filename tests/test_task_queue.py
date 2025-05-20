"""Pruebas unitarias para el sistema de cola de tareas."""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from src.gui.threads.task_queue import TaskQueue, Task, TaskState, CircuitBreaker

def test_task():
    """Test creación y estados de una tarea."""
    def dummy_func(): 
        pass
    
    task = Task("test_id", dummy_func, (), {})
    assert task.id == "test_id"
    assert task.state == TaskState.PENDING
    assert task.result is None
    assert task.error is None

@pytest.fixture
def task_queue():
    """Fixture que proporciona una cola de tareas para pruebas."""
    return TaskQueue()

def test_add_task(task_queue):
    """Prueba añadir una tarea a la cola."""
    def test_func(x): 
        return x * 2
    
    task = task_queue.add_task("task1", test_func, 5)
    assert task.id == "task1"
    assert task.state == TaskState.PENDING
    assert task.func == test_func
    assert task.args == (5,)

def test_get_next_task(task_queue):
    """Prueba obtener la siguiente tarea de la cola."""
    def test_func(): 
        pass
    
    # Añadir tarea
    task_queue.add_task("task1", test_func)
    
    # Obtener tarea
    task = task_queue.get_next_task()
    assert task is not None
    assert task.id == "task1"
    
    # Cola vacía
    assert task_queue.get_next_task() is None

def test_complete_task(task_queue):
    """Prueba completar una tarea con éxito y con error."""
    def test_func(): 
        pass
    
    # Completar con éxito
    task1 = task_queue.add_task("task1", test_func)
    task_queue.complete_task(task1, result="success")
    assert task1.state == TaskState.COMPLETED
    assert task1.result == "success"
    assert task1.error is None
    
    # Completar con error
    task2 = task_queue.add_task("task2", test_func)
    task_queue.complete_task(task2, error="error message")
    assert task2.state == TaskState.FAILED
    assert task2.error == "error message"

def test_cancel_task(task_queue):
    """Prueba cancelar una tarea."""
    def test_func(): 
        pass
    
    # Cancelar tarea pendiente
    task = task_queue.add_task("task1", test_func)
    assert task_queue.cancel_task("task1")
    assert task.state == TaskState.CANCELLED
    
    # Intentar cancelar tarea inexistente
    assert not task_queue.cancel_task("nonexistent")

def test_get_task_status(task_queue):
    """Prueba obtener el estado de una tarea."""
    def test_func(): 
        pass
    
    task = task_queue.add_task("task1", test_func)
    assert task_queue.get_task_status("task1") == TaskState.PENDING
    
    task_queue.complete_task(task, result="success")
    assert task_queue.get_task_status("task1") == TaskState.COMPLETED
    
    # Tarea inexistente
    assert task_queue.get_task_status("nonexistent") is None

def test_circuit_breaker():
    """Prueba el comportamiento del circuit breaker."""
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout=1)
    
    # Estado inicial
    assert breaker.allow_request()
    assert not breaker.is_open
    
    # Primera falla
    breaker.record_failure()
    assert breaker.allow_request()
    
    # Segunda falla - debe abrir el circuito
    breaker.record_failure()
    assert not breaker.allow_request()
    assert breaker.is_open
    
    # Éxito debe reiniciar el circuito
    breaker.record_success()
    assert breaker.allow_request()
    assert not breaker.is_open

def test_task_queue_with_circuit_breaker(task_queue):
    """Prueba integración de cola de tareas con circuit breaker."""
    def failing_func():
        raise Exception("Test error")
    
    # Configurar umbral bajo para pruebas
    task_queue.circuit_breaker.failure_threshold = 2
    
    # Primera tarea fallida
    task1 = task_queue.add_task("task1", failing_func)
    task_queue.complete_task(task1, error="error1")
    assert task_queue.get_next_task() is not None  # Circuito aún cerrado
    
    # Segunda tarea fallida - debe abrir el circuito
    task2 = task_queue.add_task("task2", failing_func)
    task_queue.complete_task(task2, error="error2")
    assert task_queue.get_next_task() is None  # Circuito abierto

def test_concurrent_task_processing(task_queue):
    """Prueba procesamiento concurrente de tareas."""
    def worker_func(task_id):
        def test_func():
            time.sleep(0.1)
            return task_id
            
        task = task_queue.add_task(f"task_{task_id}", test_func)
        result = task.func()
        task_queue.complete_task(task, result=result)
        return task.id, task.result
    
    # Procesar tareas concurrentemente
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker_func, i) for i in range(10)]
        results = [future.result() for future in futures]
    
    # Verificar resultados
    for task_id, result in results:
        task_state = task_queue.get_task_status(task_id)
        assert task_state == TaskState.COMPLETED

def test_error_handling(task_queue):
    """Prueba manejo de errores en la cola de tareas."""
    # Función que siempre falla
    def error_func():
        raise ValueError("Test error")
    
    # Añadir y procesar tarea con error
    task = task_queue.add_task("error_task", error_func)
    try:
        task.func()
    except ValueError as e:
        task_queue.complete_task(task, error=str(e))
    
    assert task.state == TaskState.FAILED
    assert task.error == "Test error"

def test_queue_stress(task_queue):
    """Prueba de estrés para la cola de tareas."""
    def slow_task(task_id, sleep_time):
        time.sleep(sleep_time)
        return f"result_{task_id}"
    
    # Añadir múltiples tareas con diferentes tiempos
    tasks = []
    for i in range(20):
        sleep_time = 0.1 * (i % 3)  # Variar tiempos de ejecución
        task = task_queue.add_task(f"stress_task_{i}", slow_task, i, sleep_time)
        tasks.append(task)
    
    # Procesar tareas concurrentemente
    def process_task(task):
        result = task.func(*task.args)
        task_queue.complete_task(task, result=result)
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_task, task) for task in tasks]
        [future.result() for future in futures]
    
    # Verificar resultados
    completed_count = sum(1 for task in tasks if task.state == TaskState.COMPLETED)
    assert completed_count == len(tasks)

def test_task_priorities():
    """Prueba manejo de prioridades en tareas."""
    # Crear cola con prioridades
    pq = Queue()
    
    def priority_task(priority):
        return priority
    
    # Añadir tareas con diferentes prioridades
    tasks = []
    for i in range(5):
        task = Task(f"task_{i}", priority_task, (i,), {})
        tasks.append(task)
        pq.put((i, task))  # Tupla (prioridad, tarea)
    
    # Verificar orden de extracción
    extracted_tasks = []
    while not pq.empty():
        priority, task = pq.get()
        extracted_tasks.append(task)
    
    # Las tareas deberían estar en orden de prioridad
    for i, task in enumerate(extracted_tasks):
        assert task.args[0] == i