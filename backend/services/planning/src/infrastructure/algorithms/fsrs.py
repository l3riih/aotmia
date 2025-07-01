"""
Algoritmo FSRS (Free Spaced Repetition Scheduler) - Versión Mejorada
Implementación avanzada basada en FSRS-5 con optimizaciones pedagógicas
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import math
import numpy as np
import structlog
from dataclasses import dataclass, field
from enum import Enum

logger = structlog.get_logger()


class Rating(Enum):
    """Calificaciones de respuesta FSRS"""
    AGAIN = 1      # Fallo total
    HARD = 2       # Difícil pero correcto
    GOOD = 3       # Correcto normal
    EASY = 4       # Fácil


class State(Enum):
    """Estados de las tarjetas FSRS"""
    NEW = 0        # Nueva tarjeta
    LEARNING = 1   # En aprendizaje
    REVIEW = 2     # En revisión
    RELEARNING = 3 # Re-aprendizaje


@dataclass
class Card:
    """Tarjeta FSRS mejorada con metadata educativa"""
    due: datetime
    stability: float
    difficulty: float
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: State
    last_review: Optional[datetime] = None
    
    # Metadata educativa adicional
    concept_id: Optional[str] = None
    difficulty_level: str = "intermediate"
    estimated_time_minutes: int = 15
    prerequisite_concepts: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    
    # Análisis de patrones de aprendizaje
    response_times: List[float] = field(default_factory=list)  # En segundos
    error_patterns: List[str] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)


@dataclass
class ReviewLog:
    """Log de revisión FSRS"""
    rating: Rating
    state: State
    due: datetime
    stability: float
    difficulty: float
    elapsed_days: int
    last_elapsed_days: int
    scheduled_days: int
    review: datetime
    
    # Metadata adicional
    response_time_seconds: Optional[float] = None
    confidence_score: Optional[float] = None
    hint_used: bool = False
    attempts_count: int = 1


class AdvancedFSRS:
    """
    Implementación avanzada del algoritmo FSRS con:
    - Parámetros optimizados para contexto educativo
    - Análisis de patrones de aprendizaje
    - Adaptación basada en dificultad del contenido
    - Predicción de retención mejorada
    """
    
    # Parámetros FSRS-5 optimizados para educación
    DEFAULT_WEIGHTS = [
        0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046,
        1.54575, 0.1192, 1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315,
        2.9898, 0.51655, 0.6621
    ]
    
    def __init__(self, weights: Optional[List[float]] = None, 
                 request_retention: float = 0.9,
                 maximum_interval: int = 365,
                 educational_mode: bool = True):
        """
        Inicializa FSRS avanzado
        
        Args:
            weights: Pesos del modelo (usa DEFAULT_WEIGHTS si es None)
            request_retention: Retención objetivo (0-1)
            maximum_interval: Intervalo máximo en días
            educational_mode: Habilita optimizaciones educativas
        """
        self.w = weights or self.DEFAULT_WEIGHTS.copy()
        self.request_retention = request_retention
        self.maximum_interval = maximum_interval
        self.educational_mode = educational_mode
        
        # Parámetros educativos adicionales
        self.difficulty_multipliers = {
            "basic": 0.8,
            "intermediate": 1.0,
            "advanced": 1.3
        }
        
        self.concept_stability_bonus = 0.1  # Bonus por conceptos relacionados
        
        logger.info(
            "Advanced FSRS initialized",
            weights_count=len(self.w),
            retention=request_retention,
            max_interval=maximum_interval,
            educational_mode=educational_mode
        )
    
    def create_new_card(self, 
                       concept_id: Optional[str] = None,
                       difficulty_level: str = "intermediate",
                       estimated_time: int = 15) -> Card:
        """Crea una nueva tarjeta con metadata educativa"""
        return Card(
            due=datetime.now(),
            stability=self.w[0],  # Estabilidad inicial
            difficulty=self.w[2],  # Dificultad inicial
            elapsed_days=0,
            scheduled_days=0,
            reps=0,
            lapses=0,
            state=State.NEW,
            concept_id=concept_id,
            difficulty_level=difficulty_level,
            estimated_time_minutes=estimated_time
        )
    
    def repeat(self, card: Card, rating: Rating, 
               response_time: Optional[float] = None,
               confidence_score: Optional[float] = None) -> Tuple[Card, ReviewLog]:
        """
        Procesa una revisión y devuelve la tarjeta actualizada
        
        Args:
            card: Tarjeta a actualizar
            rating: Calificación de la respuesta
            response_time: Tiempo de respuesta en segundos
            confidence_score: Nivel de confianza (0-1)
        """
        now = datetime.now()
        elapsed_days = (now - card.last_review).days if card.last_review else 0
        
        # Crear log de revisión
        review_log = ReviewLog(
            rating=rating,
            state=card.state,
            due=card.due,
            stability=card.stability,
            difficulty=card.difficulty,
            elapsed_days=elapsed_days,
            last_elapsed_days=card.elapsed_days,
            scheduled_days=card.scheduled_days,
            review=now,
            response_time_seconds=response_time,
            confidence_score=confidence_score
            )
            
        # Actualizar metadata de la tarjeta
        if response_time:
            card.response_times.append(response_time)
        if confidence_score:
            card.confidence_scores.append(confidence_score)
        
        # Procesar según el estado actual
        if card.state == State.NEW:
            card = self._repeat_new(card, rating)
        elif card.state in (State.LEARNING, State.RELEARNING):
            card = self._repeat_learning(card, rating)
        else:  # State.REVIEW
            card = self._repeat_review(card, rating, elapsed_days)
        
        # Aplicar modificaciones educativas
        if self.educational_mode:
            card = self._apply_educational_adjustments(card, rating, 
                                                     response_time, confidence_score)
        
        card.last_review = now
        
        logger.debug(
            "Card reviewed",
            card_id=card.concept_id,
            rating=rating.value,
            new_stability=card.stability,
            new_difficulty=card.difficulty,
            next_due=card.due
        )
        
        return card, review_log
    
    def _repeat_new(self, card: Card, rating: Rating) -> Card:
        """Procesa tarjeta nueva"""
        card.elapsed_days = 0
        card.reps += 1
        
        if rating == Rating.AGAIN:
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[3]
            card.due = datetime.now() + timedelta(minutes=1)
            card.scheduled_days = 0
            card.state = State.LEARNING
        elif rating == Rating.HARD:
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[4]
            card.due = datetime.now() + timedelta(minutes=5)
            card.scheduled_days = 0
            card.state = State.LEARNING
        elif rating == Rating.GOOD:
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[5]
            card.due = datetime.now() + timedelta(minutes=10)
            card.scheduled_days = 0
            card.state = State.LEARNING
        else:  # Rating.EASY
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[6]
            interval = self._next_interval(card.stability)
            card.scheduled_days = interval
            card.due = datetime.now() + timedelta(days=interval)
            card.state = State.REVIEW
        
        return card
    
    def _repeat_learning(self, card: Card, rating: Rating) -> Card:
        """Procesa tarjeta en aprendizaje"""
        card.reps += 1
        
        if rating == Rating.AGAIN:
            card.lapses += 1
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[9]
            card.due = datetime.now() + timedelta(minutes=5)
            card.scheduled_days = 0
            card.state = State.LEARNING
        elif rating == Rating.HARD:
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[10]
            card.due = datetime.now() + timedelta(minutes=10)
            card.scheduled_days = 0
            card.state = State.LEARNING
        elif rating == Rating.GOOD:
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[11]
            interval = self._next_interval(card.stability)
            card.scheduled_days = interval
            card.due = datetime.now() + timedelta(days=interval)
            card.state = State.REVIEW
        else:  # Rating.EASY
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self.w[12]
            interval = self._next_interval(card.stability)
            card.scheduled_days = max(interval, 4)
            card.due = datetime.now() + timedelta(days=card.scheduled_days)
            card.state = State.REVIEW
        
        return card
    
    def _repeat_review(self, card: Card, rating: Rating, elapsed_days: int) -> Card:
        """Procesa tarjeta en revisión"""
        card.elapsed_days = elapsed_days
        card.reps += 1
        
        if rating == Rating.AGAIN:
            card.lapses += 1
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self._next_forget_stability(card, elapsed_days)
            card.due = datetime.now() + timedelta(minutes=5)
            card.scheduled_days = 0
            card.state = State.RELEARNING
        else:
            card.difficulty = self._next_difficulty(card.difficulty, rating)
            card.stability = self._next_recall_stability(card, elapsed_days, rating)
            interval = self._next_interval(card.stability)
            card.scheduled_days = interval
            card.due = datetime.now() + timedelta(days=interval)
            card.state = State.REVIEW
        
        return card
    
    def _next_difficulty(self, difficulty: float, rating: Rating) -> float:
        """Calcula la próxima dificultad"""
        next_d = difficulty - self.w[6] * (rating.value - 3)
        return max(1, min(next_d, 10))
    
    def _next_recall_stability(self, card: Card, elapsed_days: int, rating: Rating) -> float:
        """Calcula estabilidad para respuesta correcta"""
        hard_penalty = self.w[15] if rating == Rating.HARD else 1
        easy_bonus = self.w[16] if rating == Rating.EASY else 1
        
        return card.stability * (
            math.exp(self.w[17]) *
            (11 - card.difficulty) *
            math.pow(card.stability, -self.w[18]) *
            (math.exp((1 - self._retention_from_stability(card.stability, elapsed_days)) * self.w[19]) - 1) *
            hard_penalty *
            easy_bonus
        )
    
    def _next_forget_stability(self, card: Card, elapsed_days: int) -> float:
        """Calcula estabilidad para olvido"""
        return (
            self.w[11] *
            math.pow(card.difficulty, -self.w[12]) *
            (math.pow(card.stability + 1, self.w[13]) - 1) *
            math.exp((1 - self._retention_from_stability(card.stability, elapsed_days)) * self.w[14])
        )
    
    def _retention_from_stability(self, stability: float, elapsed_days: int) -> float:
        """Calcula retención a partir de estabilidad"""
        return math.exp(-elapsed_days / stability) if stability > 0 else 0
    
    def _next_interval(self, stability: float) -> int:
        """Calcula próximo intervalo"""
        interval = stability / math.log(self.request_retention) * math.log(0.9)
        return min(max(1, round(interval)), self.maximum_interval)
    
    def _apply_educational_adjustments(self, card: Card, rating: Rating,
                                     response_time: Optional[float],
                                     confidence_score: Optional[float]) -> Card:
        """Aplica ajustes específicos para contexto educativo"""
        
        # Ajuste por dificultad del contenido
        difficulty_multiplier = self.difficulty_multipliers.get(
            card.difficulty_level, 1.0
        )
        card.stability *= difficulty_multiplier
        
        # Ajuste por tiempo de respuesta
        if response_time and card.estimated_time_minutes:
            expected_time = card.estimated_time_minutes * 60  # a segundos
            if response_time > expected_time * 2:  # Muy lento
                card.stability *= 0.9
            elif response_time < expected_time * 0.5:  # Muy rápido
                card.stability *= 1.1
        
        # Ajuste por confianza
        if confidence_score:
            if confidence_score < 0.5:  # Baja confianza
                card.stability *= 0.8
            elif confidence_score > 0.8:  # Alta confianza
                card.stability *= 1.1
        
        # Bonus por conceptos relacionados dominados
        if len(card.prerequisite_concepts) > 0:
            card.stability *= (1 + self.concept_stability_bonus)
        
        return card
    
    def predict_retention(self, card: Card, days_ahead: int = 0) -> float:
        """Predice la retención de una tarjeta en X días"""
        target_date = datetime.now() + timedelta(days=days_ahead)
        elapsed = (target_date - card.last_review).days if card.last_review else 0
        return self._retention_from_stability(card.stability, elapsed)
    
    def get_optimal_interval(self, card: Card, target_retention: float) -> int:
        """Obtiene el intervalo óptimo para una retención objetivo"""
        if target_retention <= 0 or target_retention >= 1:
            return 1
        
        optimal_interval = card.stability * math.log(target_retention) / math.log(0.9)
        return min(max(1, round(optimal_interval)), self.maximum_interval)
    
    def analyze_learning_patterns(self, cards: List[Card]) -> Dict[str, Any]:
        """Analiza patrones de aprendizaje del usuario"""
        if not cards:
            return {}
        
        total_cards = len(cards)
        review_cards = [c for c in cards if c.state == State.REVIEW]
        
        # Estadísticas básicas
        avg_stability = np.mean([c.stability for c in cards])
        avg_difficulty = np.mean([c.difficulty for c in cards])
        avg_reps = np.mean([c.reps for c in cards])
        
        # Análisis de tiempo de respuesta
        all_response_times = []
        for card in cards:
            all_response_times.extend(card.response_times)
        
        avg_response_time = np.mean(all_response_times) if all_response_times else 0
        
        # Análisis de confianza
        all_confidence_scores = []
        for card in cards:
            all_confidence_scores.extend(card.confidence_scores)
        
        avg_confidence = np.mean(all_confidence_scores) if all_confidence_scores else 0
        
        # Predicción de retención general
        retention_predictions = [
            self.predict_retention(card, 1) for card in review_cards
        ]
        avg_retention = np.mean(retention_predictions) if retention_predictions else 0
        
        return {
            "total_cards": total_cards,
            "review_cards": len(review_cards),
            "average_stability": float(avg_stability),
            "average_difficulty": float(avg_difficulty),
            "average_repetitions": float(avg_reps),
            "average_response_time_seconds": float(avg_response_time),
            "average_confidence": float(avg_confidence),
            "predicted_retention_tomorrow": float(avg_retention),
            "learning_efficiency": float(avg_stability / max(avg_reps, 1)),
            "mastery_rate": len([c for c in cards if c.stability > 50]) / total_cards
        }
    
    async def generate_review_schedule(self, 
                                     cards: List[Card],
                                     days_ahead: int = 7,
                                     daily_limit: int = 50) -> Dict[str, List[Card]]:
        """
        Genera un calendario de revisiones optimizado
        
        Args:
            cards: Lista de tarjetas
            days_ahead: Días hacia adelante a planificar
            daily_limit: Límite diario de revisiones
        """
        schedule = {}
        now = datetime.now()
        
        # Obtener tarjetas que necesitan revisión
        due_cards = [
            card for card in cards 
            if card.due <= now + timedelta(days=days_ahead)
        ]
        
        # Ordenar por prioridad (urgencia + importancia)
        due_cards.sort(key=lambda c: (
            c.due,  # Urgencia
            -c.stability,  # Importancia (menor estabilidad = más importante)
            c.difficulty  # Dificultad como desempate
        ))
        
        # Distribuir en días
        for day in range(days_ahead + 1):
            date_key = (now + timedelta(days=day)).strftime("%Y-%m-%d")
            schedule[date_key] = []
            
            day_start = now + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            
            # Tarjetas programadas para este día
            day_cards = [
                card for card in due_cards
                if day_start <= card.due < day_end
            ]
            
            # Aplicar límite diario
            schedule[date_key] = day_cards[:daily_limit]
        
        logger.info(
            "Review schedule generated",
            total_cards=len(due_cards),
            days_ahead=days_ahead,
            daily_limit=daily_limit
        )
        
        return schedule


# Instancia global mejorada
fsrs_algorithm = AdvancedFSRS()

# Función de compatibilidad con el código existente
class FSRSAlgorithm:
    """Wrapper para mantener compatibilidad con el código existente"""
    
    def __init__(self, parameters: Dict[str, Any]):
        self.fsrs = AdvancedFSRS(
            weights=parameters.get("w"),
            request_retention=parameters.get("request_retention", 0.9),
            maximum_interval=parameters.get("maximum_interval", 365)
        )
        logger.info("FSRS wrapper initialized", params=parameters)
    
    async def generate_review_schedule(self, atoms: List[str], 
                                     available_days_per_week: int) -> Dict[int, List[str]]:
        """Método de compatibilidad"""
        # Convertir a formato legacy
        schedule = {}
        cards = [self.fsrs.create_new_card(concept_id=atom_id) for atom_id in atoms]
        
        modern_schedule = await self.fsrs.generate_review_schedule(
            cards, days_ahead=7, daily_limit=10
        )
        
        # Convertir de vuelta al formato esperado
        day_counter = 1
        for date_str, day_cards in modern_schedule.items():
            if day_cards:
                schedule[day_counter] = [card.concept_id for card in day_cards]
                day_counter += 1
        
        return schedule 