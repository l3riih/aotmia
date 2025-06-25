"""
Algoritmo de Zona de Desarrollo Próximo (ZDP)
Basado en la teoría de Vygotsky
"""

from typing import List, Dict, Any, Tuple
import structlog

logger = structlog.get_logger()


class ZDPAlgorithm:
    """
    Implementación del algoritmo de Zona de Desarrollo Próximo.
    
    Ajusta la dificultad del contenido para mantenerlo en el nivel
    óptimo de desafío para el estudiante.
    """
    
    def __init__(self, difficulty_window: float = 0.2):
        self.difficulty_window = difficulty_window
        logger.info(
            "ZDP algorithm initialized",
            difficulty_window=difficulty_window
        )
    
    async def optimize_difficulty_progression(
        self,
        atoms: List[Dict[str, Any]],
        current_level: str
    ) -> List[Dict[str, Any]]:
        """
        Optimiza la progresión de dificultad de los átomos.
        
        Args:
            atoms: Lista de átomos con información de dificultad
            current_level: Nivel actual del estudiante
            
        Returns:
            Lista de átomos ordenados para progresión óptima
        """
        # Mapear nivel a valor numérico
        level_map = {
            "básico": 1.0,
            "intermedio": 2.0,
            "avanzado": 3.0
        }
        
        current_level_value = level_map.get(current_level, 2.0)
        
        # Calcular ZDP para cada átomo
        for atom in atoms:
            atom_difficulty = self._get_atom_difficulty(atom)
            atom["zdp_score"] = self._calculate_zdp_score(
                current_level_value,
                atom_difficulty
            )
        
        # Ordenar por ZDP score (mayor score = más apropiado)
        sorted_atoms = sorted(
            atoms,
            key=lambda a: a["zdp_score"],
            reverse=True
        )
        
        logger.info(
            "Difficulty progression optimized",
            total_atoms=len(atoms),
            current_level=current_level
        )
        
        return sorted_atoms
    
    def _get_atom_difficulty(self, atom: Dict[str, Any]) -> float:
        """Obtiene el valor numérico de dificultad de un átomo"""
        difficulty_map = {
            "básico": 1.0,
            "intermedio": 2.0,
            "avanzado": 3.0
        }
        
        difficulty_str = atom.get("difficulty", "intermedio")
        return difficulty_map.get(difficulty_str, 2.0)
    
    def _calculate_zdp_score(
        self,
        current_level: float,
        atom_difficulty: float
    ) -> float:
        """
        Calcula el score ZDP para un átomo.
        
        Score más alto = más apropiado para el estudiante
        """
        # Diferencia de dificultad
        diff = atom_difficulty - current_level
        
        # El contenido ideal está ligeramente por encima del nivel actual
        ideal_diff = 0.3  # 30% más difícil que el nivel actual
        
        # Calcular score basado en qué tan cerca está del ideal
        if diff < 0:
            # Contenido demasiado fácil
            score = max(0, 1 + diff)  # Penalizar contenido muy fácil
        elif diff <= ideal_diff + self.difficulty_window:
            # Contenido en la ZDP
            score = 1.0 - abs(diff - ideal_diff) / self.difficulty_window
        else:
            # Contenido demasiado difícil
            score = max(0, 1 - (diff - ideal_diff - self.difficulty_window))
        
        return score
    
    def adjust_difficulty_based_on_performance(
        self,
        current_difficulty: float,
        performance_score: float,  # 0.0 - 1.0
        adjustment_rate: float = 0.1
    ) -> float:
        """
        Ajusta la dificultad basándose en el rendimiento del estudiante.
        
        Args:
            current_difficulty: Dificultad actual
            performance_score: Score de rendimiento (0-1)
            adjustment_rate: Tasa de ajuste
            
        Returns:
            Nueva dificultad ajustada
        """
        # Si el rendimiento es alto, aumentar dificultad
        # Si es bajo, disminuir dificultad
        target_performance = 0.8  # 80% es el rendimiento objetivo
        
        performance_diff = performance_score - target_performance
        adjustment = performance_diff * adjustment_rate
        
        new_difficulty = current_difficulty + adjustment
        
        # Limitar entre 1.0 y 3.0
        new_difficulty = max(1.0, min(3.0, new_difficulty))
        
        logger.debug(
            "Difficulty adjusted",
            current=current_difficulty,
            performance=performance_score,
            new_difficulty=new_difficulty
        )
        
        return new_difficulty
    
    def group_atoms_by_zdp(
        self,
        atoms: List[Dict[str, Any]],
        current_level: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Agrupa átomos por su relación con la ZDP del estudiante.
        
        Returns:
            Diccionario con categorías: below_zdp, in_zdp, above_zdp
        """
        groups = {
            "below_zdp": [],  # Demasiado fácil
            "in_zdp": [],     # En la zona óptima
            "above_zdp": []   # Demasiado difícil
        }
        
        for atom in atoms:
            atom_difficulty = self._get_atom_difficulty(atom)
            diff = atom_difficulty - current_level
            
            if diff < 0:
                groups["below_zdp"].append(atom)
            elif diff <= 0.5:  # Hasta 50% más difícil está en ZDP
                groups["in_zdp"].append(atom)
            else:
                groups["above_zdp"].append(atom)
        
        return groups
    
    def recommend_scaffolding(
        self,
        atom: Dict[str, Any],
        student_level: float
    ) -> List[str]:
        """
        Recomienda estrategias de scaffolding para un átomo.
        
        Returns:
            Lista de estrategias recomendadas
        """
        atom_difficulty = self._get_atom_difficulty(atom)
        difficulty_gap = atom_difficulty - student_level
        
        scaffolding = []
        
        if difficulty_gap > 0.5:
            # Gran brecha de dificultad
            scaffolding.extend([
                "Proporcionar ejemplos paso a paso",
                "Dividir en sub-tareas más pequeñas",
                "Ofrecer pistas contextuales",
                "Permitir colaboración con pares"
            ])
        elif difficulty_gap > 0.2:
            # Brecha moderada
            scaffolding.extend([
                "Proporcionar esquema o estructura",
                "Ofrecer retroalimentación frecuente",
                "Permitir auto-evaluación guiada"
            ])
        else:
            # Brecha pequeña o contenido fácil
            scaffolding.extend([
                "Fomentar exploración independiente",
                "Proponer extensiones o variaciones"
            ])
        
        return scaffolding 