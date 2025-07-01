from __future__ import annotations

"""Additional pipeline steps for atomization workflow.

These steps handle the post-atomization phases:
- RelateStep: Resolves cross-chunk dependencies and builds prerequisite graph
- ValidateStep: Validates pedagogical coherence and atom quality
- StoreStep: Persists atoms to database with metadata
- IndexStep: Creates search indexes and caches
"""

from typing import Dict, Any, List, Set
import structlog
from uuid import uuid4

from .base import PipelineStep, PipelineError
from ..services.agentic_atomization_service import AgenticAtomizationService
from .metrics import AtomizationMetrics

logger = structlog.get_logger()


class RelateStep(PipelineStep):
    """Resolves cross-chunk dependencies and builds global prerequisite graph."""
    
    name = "relate"

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        atoms: List[Dict] = context["atoms"]
        
        # Build global concept map
        global_concepts = self._extract_global_concepts(atoms)
        
        # Resolve cross-chunk dependencies
        resolved_atoms = self._resolve_cross_chunk_dependencies(atoms, global_concepts)
        
        # Validate dependency graph (no cycles, etc.)
        self._validate_dependency_graph(resolved_atoms)
        
        context["atoms"] = resolved_atoms
        context["global_concepts"] = global_concepts
        
        logger.info("RelateStep completed", 
                   atoms=len(resolved_atoms),
                   concepts=len(global_concepts))
        return context

    def _extract_global_concepts(self, atoms: List[Dict]) -> Dict[str, Any]:
        """Extract all concepts mentioned across all atoms."""
        concepts = {}
        
        for atom in atoms:
            # Extract from learning objectives
            objectives = atom.get("learning_objectives", [])
            for obj in objectives:
                concept_key = obj.lower().strip()
                if concept_key not in concepts:
                    concepts[concept_key] = {
                        "name": obj,
                        "introduced_in": [],
                        "referenced_in": []
                    }
                concepts[concept_key]["introduced_in"].append(atom["id"])
            
            # Extract from content keywords (simple heuristic)
            content = atom.get("content", "")
            tags = atom.get("tags", [])
            for tag in tags:
                concept_key = tag.lower().strip()
                if concept_key not in concepts:
                    concepts[concept_key] = {
                        "name": tag,
                        "introduced_in": [],
                        "referenced_in": []
                    }
                concepts[concept_key]["referenced_in"].append(atom["id"])
        
        return concepts

    def _resolve_cross_chunk_dependencies(self, atoms: List[Dict], global_concepts: Dict[str, Any]) -> List[Dict]:
        """Resolve dependencies between atoms from different chunks."""
        atom_by_id = {str(atom["id"]): atom for atom in atoms}
        
        for atom in atoms:
            current_prereqs = set(atom.get("prerequisites", []))
            
            # Check if this atom references concepts introduced in other atoms
            content = atom.get("content", "").lower()
            objectives = [obj.lower() for obj in atom.get("learning_objectives", [])]
            
            for concept_key, concept_info in global_concepts.items():
                # If this atom references a concept but doesn't introduce it
                if (concept_key in content or any(concept_key in obj for obj in objectives)):
                    if str(atom["id"]) not in concept_info["introduced_in"]:
                        # Add atoms that introduce this concept as prerequisites
                        for intro_atom_id in concept_info["introduced_in"]:
                            if intro_atom_id != str(atom["id"]):
                                current_prereqs.add(intro_atom_id)
            
            atom["prerequisites"] = list(current_prereqs)
        
        return atoms

    def _validate_dependency_graph(self, atoms: List[Dict]) -> None:
        """Validate that the dependency graph has no cycles."""
        atom_ids = {str(atom["id"]) for atom in atoms}
        
        def has_cycle(atom_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(atom_id)
            rec_stack.add(atom_id)
            
            atom = next((a for a in atoms if str(a["id"]) == atom_id), None)
            if not atom:
                return False
            
            for prereq_id in atom.get("prerequisites", []):
                if prereq_id not in atom_ids:
                    continue
                    
                if prereq_id not in visited:
                    if has_cycle(prereq_id, visited, rec_stack):
                        return True
                elif prereq_id in rec_stack:
                    return True
            
            rec_stack.remove(atom_id)
            return False
        
        visited = set()
        for atom in atoms:
            atom_id = str(atom["id"])
            if atom_id not in visited:
                if has_cycle(atom_id, visited, set()):
                    raise PipelineError(f"Circular dependency detected involving atom {atom_id}")


class ValidateStep(PipelineStep):
    """Validates pedagogical coherence and atom quality."""
    
    name = "validate"

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        atoms: List[Dict] = context["atoms"]
        
        validation_results = []
        for atom in atoms:
            result = self._validate_atom(atom)
            validation_results.append(result)
            
            if not result["is_valid"]:
                logger.warning("Atom validation failed", 
                             atom_id=atom["id"],
                             issues=result["issues"])
        
        # Filter out invalid atoms or mark them for review
        valid_atoms = []
        for i, atom in enumerate(atoms):
            if validation_results[i]["is_valid"]:
                valid_atoms.append(atom)
            else:
                # Mark for manual review
                atom["status"] = "needs_review"
                atom["validation_issues"] = validation_results[i]["issues"]
                valid_atoms.append(atom)
        
        context["atoms"] = valid_atoms
        context["validation_results"] = validation_results
        
        valid_count = sum(1 for r in validation_results if r["is_valid"])
        logger.info("ValidateStep completed",
                   total_atoms=len(atoms),
                   valid_atoms=valid_count,
                   needs_review=len(atoms) - valid_count)
        
        return context

    def _validate_atom(self, atom: Dict) -> Dict[str, Any]:
        """Validate a single atom's structure and content."""
        issues = []
        
        # Required fields
        required_fields = ["title", "content", "learning_objectives"]
        for field in required_fields:
            if not atom.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Content quality checks
        content = atom.get("content", "")
        if len(content.strip()) < 50:
            issues.append("Content too short (< 50 characters)")
        
        if len(content) > 10000:
            issues.append("Content too long (> 10000 characters)")
        
        # Learning objectives check
        objectives = atom.get("learning_objectives", [])
        if not objectives:
            issues.append("No learning objectives defined")
        elif len(objectives) > 5:
            issues.append("Too many learning objectives (> 5)")
        
        # Prerequisites validation
        prerequisites = atom.get("prerequisites", [])
        if len(prerequisites) > 10:
            issues.append("Too many prerequisites (> 10)")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "quality_score": self._calculate_quality_score(atom, issues)
        }

    def _calculate_quality_score(self, atom: Dict, issues: List[str]) -> float:
        """Calculate a quality score (0.0 to 1.0) for the atom."""
        base_score = 1.0
        
        # Deduct points for issues
        base_score -= len(issues) * 0.1
        
        # Bonus for good structure
        if atom.get("learning_objectives") and len(atom["learning_objectives"]) >= 2:
            base_score += 0.1
        
        if atom.get("tags") and len(atom["tags"]) >= 2:
            base_score += 0.05
        
        if atom.get("estimated_time_minutes", 0) > 0:
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score))


class StoreStep(PipelineStep):
    """Persists atoms to database with metadata."""
    
    name = "store"

    def __init__(self, atom_repository, graph_repository):
        self.atom_repository = atom_repository
        self.graph_repository = graph_repository

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        atoms: List[Dict] = context["atoms"]
        file_metadata = context.get("file_metadata", {})
        
        # Add pipeline metadata to each atom
        for atom in atoms:
            atom.update({
                "pipeline_version": "1.0",
                "source_file": file_metadata.get("filename"),
                "processing_timestamp": context.get("processing_start_time"),
                "chunk_hierarchy_level": getattr(atom, "hierarchy_level", 1),
            })
        
        # Save atoms to MongoDB
        try:
            saved_atoms = await self.atom_repository.save_many_with_agent_metadata(
                atoms,
                agent_metadata=context.get("agent_metadata", {})
            )
            
            # Save relationships to Neo4j
            await self.graph_repository.save_atoms_with_relationships(saved_atoms)
            
            context["saved_atoms"] = saved_atoms
            context["storage_success"] = True
            
            logger.info("StoreStep completed", atoms_saved=len(saved_atoms))
            
        except Exception as e:
            logger.error("Storage failed", error=str(e))
            context["storage_success"] = False
            context["storage_error"] = str(e)
            raise PipelineError(f"Failed to store atoms: {str(e)}")
        
        return context


class IndexStep(PipelineStep):
    """Creates search indexes and caches for fast retrieval."""
    
    name = "index"

    def __init__(self, cache_service):
        self.cache_service = cache_service

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        saved_atoms = context.get("saved_atoms", [])
        file_metadata = context.get("file_metadata", {})
        
        # Create search index entries
        search_entries = []
        for atom in saved_atoms:
            entry = {
                "id": str(atom["id"]),
                "title": atom["title"],
                "content_preview": atom["content"][:200] + "...",
                "tags": atom.get("tags", []),
                "difficulty": atom.get("difficulty_level"),
                "objectives": atom.get("learning_objectives", [])
            }
            search_entries.append(entry)
        
        # Cache the results for quick access
        filename = file_metadata.get("filename", "unknown")
        cache_key = f"atomization_result:{filename}"
        
        cache_data = {
            "atoms": search_entries,
            "total_count": len(saved_atoms),
            "processing_metadata": {
                "chunks_processed": len(context.get("chunks", [])),
                "validation_results": context.get("validation_results", []),
                "global_concepts": list(context.get("global_concepts", {}).keys())
            }
        }
        
        try:
            await self.cache_service.set(cache_key, cache_data, ttl=3600)  # 1 hour cache
            
            context["index_success"] = True
            context["cache_key"] = cache_key
            
            logger.info("IndexStep completed", 
                       entries_indexed=len(search_entries),
                       cache_key=cache_key)
            
        except Exception as e:
            logger.error("Indexing failed", error=str(e))
            context["index_success"] = False
            context["index_error"] = str(e)
        
        return context


class MetricsStep(PipelineStep):
    """Calculate quality metrics for the atomization result."""
    
    name = "metrics"

    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        saved_atoms = context.get("saved_atoms", [])
        original_text = context.get("text", "")
        global_concepts = context.get("global_concepts", {})
        
        # Initialize metrics calculator
        metrics = AtomizationMetrics()
        
        # Calculate all metrics
        metrics_data = metrics.calculate_all_metrics(
            atoms=saved_atoms,
            original_text=original_text,
            global_concepts=global_concepts
        )
        
        # Store metrics in context
        context["metrics"] = metrics_data
        context["metrics_report"] = metrics.generate_report()
        
        # Log summary metrics
        logger.info("MetricsStep completed",
                   coherence_score=metrics_data["coherence"]["score"],
                   coverage_ratio=metrics_data["coverage"]["coverage_ratio"],
                   difficulty_balance=metrics_data["difficulty"]["balance_score"],
                   overall_quality=metrics_data["quality"])
        
        # Add metrics to cache if available
        cache_key = context.get("cache_key")
        if cache_key and hasattr(self, 'cache_service'):
            try:
                cached_data = await self.cache_service.get(cache_key)
                if cached_data:
                    cached_data["metrics"] = metrics_data
                    await self.cache_service.set(cache_key, cached_data, ttl=3600)
            except Exception as e:
                logger.warning("Failed to update cache with metrics", error=str(e))
        
        return context 