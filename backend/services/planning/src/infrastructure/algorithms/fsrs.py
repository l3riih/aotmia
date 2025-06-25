"""
Algoritmo FSRS (Free Spaced Repetition Scheduler)
Implementación simplificada para desarrollo
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import math
import structlog

logger = structlog.get_logger()


class FSRSAlgorithm:
    """
    Implementación del algoritmo FSRS para repetición espaciada.
    Basado en: https://github.com/open-spaced-repetition/fsrs4anki
    """
    
    def __init__(self, parameters: Dict[str, Any]):
        self.w = parameters.get("w", [0.4, 0.6, 2.4, 5.8])
        self.request_retention = parameters.get("request_retention", 0.9)
        self.maximum_interval = parameters.get("maximum_interval", 365)
        
        logger.info(
            "FSRS algorithm initialized",
            weights=self.w,
            retention=self.request_retention
        )
    
    async def generate_review_schedule(
        self,
        atoms: List[str],
        available_days_per_week: int
    ) -> Dict[int, List[str]]:
        """
        Genera calendario de revisiones usando FSRS.
        
        Args:
            atoms: Lista de IDs de átomos
            available_days_per_week: Días disponibles por semana
            
        Returns:
            Diccionario con día -> lista de átomos a revisar
        """
        schedule = {}
        
        # Para cada átomo, calcular sus intervalos de revisión
        for i, atom_id in enumerate(atoms):
            # Día inicial de estudio
            initial_day = (i // 2) + 1
            
            # Calcular intervalos usando FSRS simplificado
            intervals = self._calculate_intervals(
                difficulty=2.5,  # Dificultad media inicial
                stability=1.0    # Estabilidad inicial
            )
            
            # Programar revisiones
            for interval in intervals:
                review_day = initial_day + interval
                
                # Ajustar por días disponibles
                if available_days_per_week < 7:
                    # Saltar fines de semana si es necesario
                    week_number = review_day // 7
                    day_in_week = review_day % 7
                    if day_in_week >= available_days_per_week:
                        review_day = (week_number + 1) * 7
                
                if review_day not in schedule:
                    schedule[review_day] = []
                schedule[review_day].append(atom_id)
        
        logger.info(
            "Review schedule generated",
            total_atoms=len(atoms),
            review_days=len(schedule)
        )
        
        return schedule
    
    def _calculate_intervals(
        self, 
        difficulty: float, 
        stability: float
    ) -> List[int]:
        """
        Calcula intervalos de revisión basados en FSRS.
        
        Implementación simplificada que devuelve intervalos fijos
        basados en la curva de olvido.
        """
        # Intervalos simplificados en días
        base_intervals = [1, 3, 7, 14, 30, 60]
        
        # Ajustar por dificultad
        adjusted_intervals = []
        for interval in base_intervals:
            # Mayor dificultad = intervalos más cortos
            factor = 1.0 + (difficulty - 2.5) * 0.2
            adjusted = max(1, int(interval / factor))
            
            if adjusted <= self.maximum_interval:
                adjusted_intervals.append(adjusted)
        
        return adjusted_intervals
    
    def calculate_next_interval(
        self,
        current_interval: int,
        quality: int,  # 0-5 (0=fail, 5=perfect)
        ease_factor: float = 2.5
    ) -> Tuple[int, float]:
        """
        Calcula el siguiente intervalo basado en la calidad de respuesta.
        
        Returns:
            Tupla (nuevo_intervalo, nuevo_factor_facilidad)
        """
        # Ajustar factor de facilidad basado en calidad
        if quality < 3:
            ease_factor = max(1.3, ease_factor - 0.2)
        elif quality == 3:
            ease_factor = max(1.3, ease_factor - 0.1)
        elif quality == 4:
            ease_factor = ease_factor
        else:  # quality == 5
            ease_factor = min(2.5, ease_factor + 0.1)
        
        # Calcular nuevo intervalo
        if quality < 3:
            # Fallo: reiniciar
            new_interval = 1
        else:
            # Éxito: aumentar intervalo
            if current_interval == 0:
                new_interval = 1
            elif current_interval == 1:
                new_interval = 4
            else:
                new_interval = min(
                    self.maximum_interval,
                    int(current_interval * ease_factor)
                )
        
        logger.debug(
            "Interval calculated",
            current=current_interval,
            quality=quality,
            new_interval=new_interval,
            ease_factor=ease_factor
        )
        
        return new_interval, ease_factor
    
    def estimate_retention(
        self,
        interval: int,
        time_since_review: int
    ) -> float:
        """
        Estima la retención basada en el intervalo y tiempo transcurrido.
        Usa la curva de olvido de Ebbinghaus.
        """
        if time_since_review == 0:
            return 1.0
        
        # Fórmula simplificada de retención
        retention = math.exp(-time_since_review / (interval * 1.2))
        
        return max(0.0, min(1.0, retention))
    
    def optimize_schedule(
        self,
        atoms: List[Dict[str, Any]],
        time_constraint_hours: float
    ) -> List[str]:
        """
        Optimiza la selección de átomos para maximizar retención
        dentro de las restricciones de tiempo.
        """
        # Ordenar por prioridad de revisión
        # (menor retención = mayor prioridad)
        prioritized = sorted(
            atoms,
            key=lambda a: a.get("current_retention", 1.0)
        )
        
        selected = []
        total_time = 0.0
        
        for atom in prioritized:
            atom_time = atom.get("estimated_time_minutes", 15) / 60.0
            if total_time + atom_time <= time_constraint_hours:
                selected.append(atom["id"])
                total_time += atom_time
        
        return selected 