"""
Sistema de triggers automáticos para acciones en la biblioteca musical.
"""
import logging
import time
import threading
import schedule
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Trigger:
    """Trigger para ejecutar acciones automáticas."""
    name: str
    description: str = ""
    type: str = "scheduled"  # scheduled, event, condition
    schedule_config: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    is_active: bool = True
    last_execution: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trigger':
        """Crea un trigger desde un diccionario."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            type=data.get("type", "scheduled"),
            schedule_config=data.get("schedule_config", {}),
            actions=data.get("actions", []),
            is_active=data.get("is_active", True),
            last_execution=data.get("last_execution")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el trigger a un diccionario."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "schedule_config": self.schedule_config,
            "actions": self.actions,
            "is_active": self.is_active,
            "last_execution": self.last_execution
        }
    
    def to_json(self) -> str:
        """Convierte el trigger a JSON."""
        return json.dumps(self.to_dict())

class TriggerSystem:
    """Sistema para manejar y ejecutar triggers automáticos."""
    
    def __init__(self, db_manager=None):
        """
        Inicializa el sistema de triggers.
        
        Args:
            db_manager: Gestor de base de datos opcional
        """
        self.triggers: List[Trigger] = []
        self.db_manager = db_manager
        self.is_running = False
        self.scheduler_thread = None
        self.actions_registry: Dict[str, Callable] = {}
        self.event_handlers: Dict[str, List[Trigger]] = {}
        
    def register_action(self, action_name: str, handler_func: Callable):
        """Registra una función manejadora para un tipo de acción."""
        self.actions_registry[action_name] = handler_func
        logger.debug(f"Acción registrada: {action_name}")
        
    def load_triggers(self):
        """Carga los triggers desde la base de datos."""
        if not self.db_manager:
            logger.warning("No hay gestor de base de datos, no se cargarán triggers")
            return
            
        try:
            # Verificar si existe la tabla de triggers
            self._ensure_triggers_table()
            
            # Cargar los triggers
            rows = self.db_manager.fetch_query("SELECT * FROM triggers WHERE is_active = 1")
            
            self.triggers = []
            for row in rows:
                try:
                    trigger = Trigger(
                        name=row["name"],
                        description=row["description"],
                        type=row["type"],
                        schedule_config=json.loads(row["schedule_config"]),
                        actions=json.loads(row["actions"]),
                        is_active=bool(row["is_active"]),
                        last_execution=row["last_execution"]
                    )
                    self.triggers.append(trigger)
                    
                    # Registrar trigger en event_handlers si es de tipo "event"
                    if trigger.type == "event":
                        event_name = trigger.schedule_config.get("event_name")
                        if event_name:
                            if event_name not in self.event_handlers:
                                self.event_handlers[event_name] = []
                            self.event_handlers[event_name].append(trigger)
                
                except Exception as e:
                    logger.error(f"Error cargando trigger {row['name']}: {e}")
            
            logger.info(f"Cargados {len(self.triggers)} triggers desde la base de datos")
        
        except Exception as e:
            logger.error(f"Error cargando triggers: {e}")
    
    def _ensure_triggers_table(self):
        """Asegura que la tabla de triggers exista."""
        if not self.db_manager or not hasattr(self.db_manager, "connection"):
            return
            
        try:
            self.db_manager.connection.execute('''
                CREATE TABLE IF NOT EXISTS triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT '',
                    type TEXT NOT NULL,
                    schedule_config TEXT DEFAULT '{}',
                    actions TEXT DEFAULT '[]',
                    is_active BOOLEAN DEFAULT 1,
                    last_execution TEXT
                )
            ''')
            self.db_manager.connection.commit()
            logger.debug("Tabla de triggers verificada/creada")
        
        except Exception as e:
            logger.error(f"Error creando tabla de triggers: {e}")
    
    def add_trigger(self, trigger: Trigger) -> bool:
        """
        Añade un trigger al sistema y a la base de datos.
        
        Args:
            trigger: Trigger a añadir
            
        Returns:
            True si se añadió correctamente
        """
        try:
            # Añadir a la lista en memoria
            self.triggers.append(trigger)
            
            # Registrar en event_handlers si es de tipo "event"
            if trigger.type == "event":
                event_name = trigger.schedule_config.get("event_name")
                if event_name:
                    if event_name not in self.event_handlers:
                        self.event_handlers[event_name] = []
                    self.event_handlers[event_name].append(trigger)
            
            # Persistir en la base de datos
            if self.db_manager:
                self._ensure_triggers_table()
                
                self.db_manager.execute_query(
                    """
                    INSERT INTO triggers 
                    (name, description, type, schedule_config, actions, is_active, last_execution)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trigger.name, 
                        trigger.description,
                        trigger.type,
                        json.dumps(trigger.schedule_config),
                        json.dumps(trigger.actions),
                        trigger.is_active,
                        trigger.last_execution
                    )
                )
            
            # Si ya está corriendo el scheduler, programar este trigger
            if self.is_running and trigger.is_active and trigger.type == "scheduled":
                self._schedule_trigger(trigger)
                
            logger.info(f"Trigger '{trigger.name}' añadido correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error añadiendo trigger: {e}")
            return False
    
    def update_trigger(self, trigger: Trigger) -> bool:
        """
        Actualiza un trigger existente.
        
        Args:
            trigger: Trigger con datos actualizados
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Actualizar en memoria
            for i, t in enumerate(self.triggers):
                if t.name == trigger.name:
                    self.triggers[i] = trigger
                    break
            
            # Actualizar en event_handlers si corresponde
            if trigger.type == "event":
                event_name = trigger.schedule_config.get("event_name")
                
                # Primero eliminar de cualquier lista en la que estuviera
                for handlers in self.event_handlers.values():
                    handlers[:] = [h for h in handlers if h.name != trigger.name]
                
                # Luego añadir al evento correcto
                if event_name:
                    if event_name not in self.event_handlers:
                        self.event_handlers[event_name] = []
                    self.event_handlers[event_name].append(trigger)
            
            # Actualizar en la base de datos
            if self.db_manager:
                self.db_manager.execute_query(
                    """
                    UPDATE triggers
                    SET description = ?, type = ?, schedule_config = ?, 
                        actions = ?, is_active = ?, last_execution = ?
                    WHERE name = ?
                    """,
                    (
                        trigger.description,
                        trigger.type,
                        json.dumps(trigger.schedule_config),
                        json.dumps(trigger.actions),
                        trigger.is_active,
                        trigger.last_execution,
                        trigger.name
                    )
                )
            
            # Si está corriendo el scheduler, reprogramar
            if self.is_running:
                schedule.clear()
                self._setup_scheduler()
                
            logger.info(f"Trigger '{trigger.name}' actualizado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando trigger: {e}")
            return False
    
    def delete_trigger(self, name: str) -> bool:
        """
        Elimina un trigger.
        
        Args:
            name: Nombre del trigger a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            # Eliminar de la memoria
            self.triggers = [t for t in self.triggers if t.name != name]
            
            # Eliminar de event_handlers
            for handlers in self.event_handlers.values():
                handlers[:] = [h for h in handlers if h.name != name]
            
            # Eliminar de la base de datos
            if self.db_manager:
                self.db_manager.execute_query("DELETE FROM triggers WHERE name = ?", (name,))
            
            # Si está corriendo el scheduler, reprogramar
            if self.is_running:
                schedule.clear()
                self._setup_scheduler()
                
            logger.info(f"Trigger '{name}' eliminado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando trigger: {e}")
            return False
    
    def start(self):
        """Inicia el sistema de triggers."""
        if self.is_running:
            logger.warning("El sistema de triggers ya está en ejecución")
            return
            
        try:
            self.load_triggers()
            self._setup_scheduler()
            
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("Sistema de triggers iniciado")
            
        except Exception as e:
            logger.error(f"Error iniciando sistema de triggers: {e}")
    
    def stop(self):
        """Detiene el sistema de triggers."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1.0)
        schedule.clear()
        
        logger.info("Sistema de triggers detenido")
    
    def _setup_scheduler(self):
        """Configura el scheduler con los triggers programados."""
        for trigger in self.triggers:
            if trigger.is_active and trigger.type == "scheduled":
                self._schedule_trigger(trigger)
    
    def _schedule_trigger(self, trigger: Trigger):
        """Programa un trigger según su configuración."""
        if trigger.type != "scheduled":
            return
            
        config = trigger.schedule_config
        schedule_type = config.get("type", "daily")
        
        job = None
        
        # Crear el trabajo según el tipo de programación
        if schedule_type == "daily":
            time_str = config.get("time", "00:00")
            job = schedule.every().day.at(time_str)
            
        elif schedule_type == "weekly":
            day = config.get("day", "monday").lower()
            time_str = config.get("time", "00:00")
            
            if day == "monday":
                job = schedule.every().monday.at(time_str)
            elif day == "tuesday":
                job = schedule.every().tuesday.at(time_str)
            elif day == "wednesday":
                job = schedule.every().wednesday.at(time_str)
            elif day == "thursday":
                job = schedule.every().thursday.at(time_str)
            elif day == "friday":
                job = schedule.every().friday.at(time_str)
            elif day == "saturday":
                job = schedule.every().saturday.at(time_str)
            elif day == "sunday":
                job = schedule.every().sunday.at(time_str)
                
        elif schedule_type == "interval":
            interval = config.get("interval", 60)  # segundos
            job = schedule.every(interval).seconds
        
        # Asociar la función a ejecutar
        if job:
            job.do(self._execute_trigger, trigger_name=trigger.name)
            logger.debug(f"Trigger '{trigger.name}' programado: {schedule_type}")
    
    def _run_scheduler(self):
        """Ejecuta el loop del scheduler en un hilo separado."""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def _execute_trigger(self, trigger_name: str):
        """
        Ejecuta un trigger por su nombre.
        
        Args:
            trigger_name: Nombre del trigger a ejecutar
        """
        try:
            # Buscar el trigger
            trigger = next((t for t in self.triggers if t.name == trigger_name), None)
            if not trigger:
                logger.warning(f"Trigger '{trigger_name}' no encontrado para ejecución")
                return
                
            logger.info(f"Ejecutando trigger '{trigger_name}'")
            
            # Ejecutar cada acción del trigger
            results = []
            for action in trigger.actions:
                action_type = action.get("type")
                params = action.get("params", {})
                
                handler = self.actions_registry.get(action_type)
                if handler:
                    try:
                        result = handler(params)
                        results.append({
                            "action_type": action_type,
                            "success": bool(result),
                            "result": result
                        })
                    except Exception as action_error:
                        logger.error(f"Error ejecutando acción '{action_type}': {action_error}")
                        results.append({
                            "action_type": action_type,
                            "success": False,
                            "error": str(action_error)
                        })
                else:
                    logger.warning(f"Manejador no encontrado para acción '{action_type}'")
                    results.append({
                        "action_type": action_type,
                        "success": False,
                        "error": f"Manejador no encontrado para acción '{action_type}'"
                    })
            
            # Actualizar última ejecución
            trigger.last_execution = datetime.now().isoformat()
            
            # Actualizar en la base de datos
            if self.db_manager:
                self.db_manager.execute_query(
                    "UPDATE triggers SET last_execution = ? WHERE name = ?",
                    (trigger.last_execution, trigger.name)
                )
            
            logger.info(f"Trigger '{trigger_name}' ejecutado con {sum(1 for r in results if r.get('success'))} acciones exitosas")
            
        except Exception as e:
            logger.error(f"Error ejecutando trigger '{trigger_name}': {e}")
    
    def fire_event(self, event_name: str, context: Dict[str, Any] = None):
        """
        Dispara un evento que puede activar triggers.
        
        Args:
            event_name: Nombre del evento
            context: Contexto con datos del evento
        """
        if context is None:
            context = {}
            
        handlers = self.event_handlers.get(event_name, [])
        if not handlers:
            logger.debug(f"No hay manejadores para el evento '{event_name}'")
            return
        
        logger.info(f"Disparando evento '{event_name}' con {len(handlers)} manejadores")
        
        for trigger in handlers:
            if trigger.is_active:
                self._execute_trigger(trigger.name)

# Acciones predefinidas para el sistema de triggers
def create_dynamic_playlist_action(params: Dict[str, Any]) -> bool:
    """Crea una playlist dinámica basada en parámetros."""
    from ..database.music_database import MusicDatabase
    from .utils import PlaylistGenerator
    
    db_path = params.get("db_path")
    if not db_path:
        logger.error("db_path no especificado para create_dynamic_playlist_action")
        return False
    
    playlist_type = params.get("playlist_type")
    if not playlist_type:
        logger.error("playlist_type no especificado")
        return False
    
    try:
        with MusicDatabase(db_path) as db:
            generator = PlaylistGenerator(db)
            
            if playlist_type == "genre":
                genre = params.get("genre")
                limit = params.get("limit", 50)
                return generator.generate_by_genre(genre, limit) is not None
                
            elif playlist_type == "bpm_range":
                min_bpm = params.get("min_bpm", 0)
                max_bpm = params.get("max_bpm", 200)
                limit = params.get("limit", 50)
                return generator.generate_by_bpm_range(min_bpm, max_bpm, limit) is not None
                
            elif playlist_type == "energy_progression":
                start = params.get("start_energy", 0.3)
                end = params.get("end_energy", 0.8)
                steps = params.get("steps", 10)
                return generator.generate_energy_progression(start, end, steps) is not None
                
            elif playlist_type == "camelot_mix":
                start_key = params.get("start_key")
                transitions = params.get("transitions", 12)
                energy = params.get("energy_direction", "up")
                return generator.generate_camelot_mix(start_key, transitions, energy) is not None
            
            else:
                logger.error(f"Tipo de playlist desconocido: {playlist_type}")
                return False
    
    except Exception as e:
        logger.error(f"Error en create_dynamic_playlist_action: {e}")
        return False

def export_playlist_action(params: Dict[str, Any]) -> bool:
    """Exporta una playlist a formato M3U."""
    from ..database.music_database import MusicDatabase
    from .utils import M3UExporter
    
    db_path = params.get("db_path")
    if not db_path:
        logger.error("db_path no especificado para export_playlist_action")
        return False
    
    playlist_id = params.get("playlist_id")
    if not playlist_id:
        logger.error("playlist_id no especificado")
        return False
    
    output_path = params.get("output_path")
    if not output_path:
        logger.error("output_path no especificado")
        return False
    
    try:
        with MusicDatabase(db_path) as db:
            return M3UExporter.export_playlist(db, playlist_id, output_path)
    
    except Exception as e:
        logger.error(f"Error en export_playlist_action: {e}")
        return False
