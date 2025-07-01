from __future__ import annotations

"""High-level AtomizationPipeline that orchestrates all individual steps.

This pipeline is **format-agnostic**: it starts from raw file bytes (uploaded
by the user) and ends with a list of *learning atoms* already saved and
indexed.
"""

from typing import Dict, Any, List, Optional
import structlog

from .base import PipelineStep, PipelineOrchestrator, PipelineError
from .parsers import parse_content, ParserError
from .chunker import chunk_text_hierarchical, Chunk
from .steps import RelateStep, ValidateStep, StoreStep, IndexStep, MetricsStep

# Import existing agentic service and repositories
from ..services.agentic_atomization_service import AgenticAtomizationService
from ...infrastructure.agentic.orchestrator_client import OrchestratorClient  # type: ignore

# Neo4j repository might live in planning package; we attempt import with fallback
try:
    from ...infrastructure.database.neo4j_knowledge_graph import Neo4jKnowledgeGraph as _RealNeo4jKG  # type: ignore
    Neo4jKnowledgeGraph = _RealNeo4jKG  # alias for downstream usage
except ImportError:  # pragma: no cover
    class Neo4jKnowledgeGraph:  # type: ignore
        """Fallback stub when real repository is unavailable."""

        async def save_atoms_with_relationships(self, *_, **__):  # noqa: D401
            return None

from ...core.dependencies import (
    get_cache_service,
    get_atom_repository,
    get_neo4j_repository,
)  # type: ignore

logger = structlog.get_logger()


class ParseStep(PipelineStep):
    name = "parse"

    def __init__(self, filename: str | None, content_type: str | None):
        self.filename = filename
        self.content_type = content_type

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raw_data = context["raw_data"]  # bytes | str
        try:
            text, metadata = parse_content(raw_data, filename=self.filename, content_type=self.content_type)
        except ParserError as exc:
            raise PipelineError(str(exc)) from exc
        context["text"] = text
        context["file_metadata"] = metadata
        logger.info("ParseStep completed", filename=self.filename, metadata=metadata)
        return context


class ChunkStep(PipelineStep):
    name = "chunk"

    def __init__(self, max_tokens: int = 4000, overlap_ratio: float = 0.1):
        self.max_tokens = max_tokens
        self.overlap_ratio = overlap_ratio

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context["text"]
        chunks = chunk_text_hierarchical(text, self.max_tokens, self.overlap_ratio)
        context["chunks"] = chunks
        logger.info("ChunkStep completed", chunks=len(chunks), max_tokens=self.max_tokens, overlap_ratio=self.overlap_ratio)
        return context


class AtomizeChunkStep(PipelineStep):
    name = "atomize"

    def __init__(self, atomization_service: AgenticAtomizationService, objectives: str | None, difficulty: str, user_id: str | None):
        self.svc = atomization_service
        self.objectives = objectives or ""
        self.difficulty = difficulty
        self.user_id = user_id

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        chunks: List[Chunk] = context["chunks"]
        all_atoms: list = []
        for idx, chunk in enumerate(chunks):
            atoms = await self.svc.atomize_with_agent(
                content=chunk.text,
                objectives=self.objectives,
                difficulty=self.difficulty,
                user_id=self.user_id,
            )
            all_atoms.extend(atoms)
        context["atoms"] = all_atoms
        logger.info("AtomizeChunkStep completed", atoms=len(all_atoms))
        return context


async def build_default_pipeline(filename: str | None, content_type: str | None, *, objectives: str | None = None, difficulty: str = "intermedio", user_id: str | None = None) -> PipelineOrchestrator:
    """Factory that constructs a ready-to-run pipeline with sensible defaults."""
    from datetime import datetime
    
    # Build agentic service dependencies
    atom_repo = get_atom_repository()
    orchestrator_client = OrchestratorClient(base_url="http://localhost:8002")
    redis_cache = get_cache_service()
    knowledge_graph = get_neo4j_repository()
    atom_service = AgenticAtomizationService(atom_repo, orchestrator_client, redis_cache, knowledge_graph)

    steps: List[PipelineStep] = [
        ParseStep(filename, content_type),
        ChunkStep(max_tokens=4000),
        AtomizeChunkStep(atom_service, objectives, difficulty, user_id),
        RelateStep(),
        ValidateStep(),
        StoreStep(atom_repo, knowledge_graph),
        IndexStep(redis_cache),
        MetricsStep(),
    ]

    return PipelineOrchestrator(steps)


async def build_custom_pipeline(filename: str | None, content_type: str | None, *, 
                               objectives: str | None = None, 
                               difficulty: str = "intermedio", 
                               user_id: str | None = None,
                               overlap_ratio: float = 0.1) -> PipelineOrchestrator:
    """Factory that constructs a pipeline with custom parameters including overlap ratio."""
    from datetime import datetime
    
    # Build agentic service dependencies
    atom_repo = get_atom_repository()
    orchestrator_client = OrchestratorClient(base_url="http://localhost:8002")
    redis_cache = get_cache_service()
    knowledge_graph = get_neo4j_repository()
    atom_service = AgenticAtomizationService(atom_repo, orchestrator_client, redis_cache, knowledge_graph)

    steps: List[PipelineStep] = [
        ParseStep(filename, content_type),
        ChunkStep(max_tokens=4000, overlap_ratio=overlap_ratio),  # Custom overlap
        AtomizeChunkStep(atom_service, objectives, difficulty, user_id),
        RelateStep(),
        ValidateStep(),
        StoreStep(atom_repo, knowledge_graph),
        IndexStep(redis_cache),
        MetricsStep(),
    ]

    return PipelineOrchestrator(steps)


async def run_atomization_pipeline(
    raw_data: bytes | str,
    filename: str | None = None,
    content_type: str | None = None,
    objectives: str | None = None,
    difficulty: str = "intermedio",
    user_id: str | None = None
) -> Dict[str, Any]:
    """High-level function to run the complete atomization pipeline."""
    from datetime import datetime
    
    pipeline = await build_default_pipeline(
        filename=filename,
        content_type=content_type,
        objectives=objectives,
        difficulty=difficulty,
        user_id=user_id
    )
    
    initial_context = {
        "raw_data": raw_data,
        "processing_start_time": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "pipeline_version": "1.0"
    }
    
    try:
        final_context = await pipeline.run(initial_context)
        
        return {
            "success": True,
            "atoms": final_context.get("saved_atoms", []),
            "metadata": {
                "chunks_processed": len(final_context.get("chunks", [])),
                "atoms_created": len(final_context.get("saved_atoms", [])),
                "validation_results": final_context.get("validation_results", []),
                "global_concepts": final_context.get("global_concepts", {}),
                "cache_key": final_context.get("cache_key"),
                "processing_time": final_context.get("processing_start_time")
            },
            "metrics": final_context.get("metrics", {}),
            "metrics_report": final_context.get("metrics_report", "")
        }
    except PipelineError as e:
        logger.error("Pipeline execution failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "atoms": [],
            "metadata": {},
            "metrics": {}
        } 