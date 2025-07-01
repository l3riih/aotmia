from __future__ import annotations

"""
Base definitions for the Atomization Pipeline.  
Each step is a callable object that receives a shared mutable **context** dict
and returns it (optionally after modification). The context object flows through
all the steps allowing them to exchange data in a loose-coupled fashion.  

All steps **must** obey the following contract:

    async def __call__(self, context: dict) -> dict:
        # Modify and return context

If an unrecoverable error occurs, the step should raise a `PipelineError` so the
orchestrator can abort the execution gracefully.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Sequence, Coroutine, Callable, Awaitable


class PipelineError(Exception):
    """Raised when any pipeline step fails irrecoverably."""


class PipelineStep(ABC):
    """Abstract base class for a single pipeline step."""

    name: str = "unnamed_step"

    async def __call__(self, context: Dict[str, Any]) -> Dict[str, Any]:  # noqa: D401
        """Run the step.
        Concrete subclasses should override ``_run`` instead of this method to
        get type checking for the context dict.
        """
        return await self._run(context)

    @abstractmethod
    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement the step logic and return the updated context."""


class PipelineOrchestrator:
    """Executes a sequence of PipelineSteps in order, passing a shared context."""

    def __init__(self, steps: Sequence[PipelineStep]):
        if not steps:
            raise ValueError("Pipeline must contain at least one step")
        self.steps: List[PipelineStep] = list(steps)

    async def run(self, initial_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Run all steps sequentially and return the final context."""
        context: Dict[str, Any] = initial_context or {}
        for step in self.steps:
            try:
                context = await step(context)
            except PipelineError:
                # Re-raise to caller so it can handle or log accordingly.
                raise
            except Exception as exc:  # pragma: no cover
                # Wrap unexpected exceptions to keep them homogeneous.
                raise PipelineError(f"Step '{step.name}' failed: {exc}") from exc
        return context 