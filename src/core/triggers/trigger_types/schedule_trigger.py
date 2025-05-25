from typing import Dict, Any, Optional
import time
from datetime import datetime
import croniter  # Para parsear y evaluar expresiones cron

from ..base_trigger import BaseTrigger, TriggerEvent, TriggerType

class ScheduleError(Exception):
    """Error relacionado con la programación de triggers"""
    pass

class ScheduleTrigger(BaseTrigger):
    """
    Trigger que se ejecuta en momentos específicos según una programación.
    Soporta expresiones cron para definir horarios de ejecución.
    """
    
    def __init__(self, playlist_id: str):
        super().__init__(playlist_id)
        
        # Configuración por defecto
        self._config.update({
            'cron_expression': '0 0 * * *',  # Por defecto: diario a medianoche
            'timezone': 'UTC',               # Zona horaria para evaluación
            'skip_missed': False,            # Si ignorar ejecuciones perdidas
            'max_missed': 1,                 # Máximo de ejecuciones perdidas a recuperar
            'jitter': 0                      # Variación aleatoria en segundos
        })
        
        # Estado interno
        self._cron = None
        self._next_run = None
        self._missed_runs = []
        
    def configure(self, config: Dict[str, Any]):
        """
        Configura el trigger con parámetros específicos.
        
        Args:
            config: Diccionario de configuración
            
        Raises:
            ScheduleError: Si la expresión cron es inválida
        """
        super().configure(config)
        
        try:
            # Validar y compilar expresión cron
            cron_expression = self._config['cron_expression']
            self._cron = croniter.croniter(cron_expression)
            
            # Calcular próxima ejecución
            now = datetime.now()
            self._next_run = self._cron.get_next(datetime)
            
            # Identificar ejecuciones perdidas si es necesario
            if not self._config['skip_missed']:
                self._find_missed_runs(now)
                
        except Exception as e:
            raise ScheduleError(
                f"Error configurando schedule: {str(e)}"
            ) from e
            
    def should_trigger(self, event: TriggerEvent) -> bool:
        """
        Determina si el trigger debe ejecutarse basado en el horario.
        
        Args:
            event: El evento a evaluar
            
        Returns:
            bool: True si es hora de ejecutar
        """
        # Solo procesar eventos de tipo SCHEDULED
        if event.type != TriggerType.SCHEDULED:
            return False
            
        # Si no hay próxima ejecución programada
        if not self._next_run:
            return False
            
        now = datetime.now()
        
        # Primero procesar ejecuciones perdidas
        if self._missed_runs:
            return True
            
        # Verificar si es tiempo de la próxima ejecución
        return now >= self._next_run
        
    def execute(self, event: TriggerEvent) -> bool:
        """
        Ejecuta el trigger programado.
        
        Args:
            event: El evento que disparó el trigger
            
        Returns:
            bool: True si la ejecución fue exitosa
        """
        try:
            now = datetime.now()
            
            # Procesar ejecuciones perdidas primero
            if self._missed_runs:
                missed_time = self._missed_runs.pop(0)
                self._execute_at(missed_time)
                return True
                
            # Ejecución normal
            if now >= self._next_run:
                self._execute_at(self._next_run)
                
                # Programar siguiente ejecución
                self._next_run = self._cron.get_next(datetime)
                return True
                
            return False
            
        except Exception as e:
            self.record_execution(False, e)
            return False
            
    def _execute_at(self, target_time: datetime):
        """
        Ejecuta el trigger para un momento específico.
        
        Args:
            target_time: Momento para el que se ejecuta el trigger
        """
        # Aquí implementarías la lógica específica de ejecución
        # Por ejemplo, regenerar la playlist
        
        # Registrar ejecución exitosa
        self.record_execution(True)
        
    def _find_missed_runs(self, since: datetime):
        """
        Identifica ejecuciones perdidas desde un momento dado.
        
        Args:
            since: Momento desde el que buscar ejecuciones perdidas
        """
        if self._config['skip_missed']:
            return
            
        # Crear iterador desde el momento indicado
        iter = croniter.croniter(self._config['cron_expression'], since)
        
        # Encontrar todas las ejecuciones hasta ahora
        now = datetime.now()
        missed = []
        
        while len(missed) < self._config['max_missed']:
            next_time = iter.get_next(datetime)
            if next_time >= now:
                break
            missed.append(next_time)
            
        self._missed_runs = missed
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del trigger.
        
        Returns:
            Dict con estadísticas
        """
        stats = super().get_stats()
        stats.update({
            'cron_expression': self._config['cron_expression'],
            'next_run': self._next_run,
            'missed_runs': len(self._missed_runs),
            'timezone': self._config['timezone']
        })
        return stats
        
    def get_next_run(self) -> Optional[datetime]:
        """
        Retorna el momento de la próxima ejecución programada.
        
        Returns:
            datetime o None si no hay ejecución programada
        """
        return self._next_run
        
    def get_missed_runs(self) -> List[datetime]:
        """
        Retorna lista de ejecuciones perdidas pendientes.
        
        Returns:
            Lista de momentos de ejecución perdidos
        """
        return self._missed_runs.copy()
