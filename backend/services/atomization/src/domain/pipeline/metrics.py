"""Metrics and quality analysis for atomization pipeline.

This module provides comprehensive metrics to evaluate the quality of the
atomization process, including conceptual coherence, content coverage,
difficulty balance, and graph density.
"""

from typing import Dict, List, Any, Set, Tuple
import structlog
from collections import Counter, defaultdict
import statistics

logger = structlog.get_logger()


class AtomizationMetrics:
    """Calculate quality metrics for atomized content."""
    
    def __init__(self):
        self.metrics = {}
        
    def calculate_all_metrics(self, atoms: List[Dict[str, Any]], 
                            original_text: str,
                            global_concepts: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all quality metrics for the atomization result."""
        
        self.metrics = {
            "coherence": self._calculate_coherence_metrics(atoms, global_concepts),
            "coverage": self._calculate_coverage_metrics(atoms, original_text),
            "difficulty": self._calculate_difficulty_metrics(atoms),
            "graph": self._calculate_graph_metrics(atoms),
            "quality": self._calculate_overall_quality_score(atoms),
            "summary": self._generate_summary(atoms)
        }
        
        return self.metrics
    
    def _calculate_coherence_metrics(self, atoms: List[Dict[str, Any]], 
                                   global_concepts: Dict[str, Any]) -> Dict[str, float]:
        """Calculate conceptual coherence metrics."""
        
        total_atoms = len(atoms)
        if total_atoms == 0:
            return {"score": 0.0, "unresolved_deps": 0, "orphan_concepts": 0}
        
        # Count unresolved dependencies
        all_atom_ids = {str(atom.get("id", "")) for atom in atoms}
        unresolved_deps = 0
        
        for atom in atoms:
            prerequisites = atom.get("prerequisites", [])
            for prereq in prerequisites:
                if prereq not in all_atom_ids:
                    unresolved_deps += 1
        
        # Count orphan concepts (concepts not introduced anywhere)
        orphan_concepts = 0
        for concept, info in global_concepts.items():
            if not info.get("introduced_in"):
                orphan_concepts += 1
        
        # Calculate coherence score
        dep_penalty = unresolved_deps / (total_atoms * 2)  # Assume avg 2 deps per atom
        orphan_penalty = orphan_concepts / max(len(global_concepts), 1)
        
        coherence_score = max(0.0, 1.0 - dep_penalty - orphan_penalty)
        
        return {
            "score": round(coherence_score, 3),
            "unresolved_dependencies": unresolved_deps,
            "orphan_concepts": orphan_concepts,
            "total_concepts": len(global_concepts),
            "dependency_resolution_rate": round(1.0 - dep_penalty, 3)
        }
    
    def _calculate_coverage_metrics(self, atoms: List[Dict[str, Any]], 
                                  original_text: str) -> Dict[str, float]:
        """Calculate content coverage metrics."""
        
        # Estimate coverage by comparing total atom content length vs original
        atom_content_length = sum(len(atom.get("content", "")) for atom in atoms)
        original_length = len(original_text)
        
        # Coverage ratio (can be > 1.0 due to overlap/expansion)
        coverage_ratio = atom_content_length / max(original_length, 1)
        
        # Count unique concepts covered
        covered_concepts = set()
        for atom in atoms:
            covered_concepts.update(atom.get("tags", []))
            covered_concepts.update(atom.get("learning_objectives", []))
        
        return {
            "coverage_ratio": round(coverage_ratio, 3),
            "atom_content_chars": atom_content_length,
            "original_chars": original_length,
            "unique_concepts_covered": len(covered_concepts),
            "average_atom_length": round(atom_content_length / max(len(atoms), 1), 1)
        }
    
    def _calculate_difficulty_metrics(self, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate difficulty balance metrics."""
        
        difficulty_counts = Counter()
        time_estimates = []
        
        for atom in atoms:
            difficulty = atom.get("difficulty_level", "intermedio")
            difficulty_counts[difficulty] += 1
            
            time = atom.get("estimated_time_minutes", 10)
            time_estimates.append(time)
        
        # Calculate distribution balance
        total_atoms = len(atoms)
        if total_atoms == 0:
            return {"balance_score": 0.0, "distribution": {}}
        
        difficulty_distribution = {
            level: count / total_atoms 
            for level, count in difficulty_counts.items()
        }
        
        # Ideal distribution (can be configured)
        ideal_distribution = {
            "básico": 0.3,
            "intermedio": 0.5,
            "avanzado": 0.2
        }
        
        # Calculate balance score (how close to ideal)
        balance_score = 0.0
        for level, ideal_ratio in ideal_distribution.items():
            actual_ratio = difficulty_distribution.get(level, 0.0)
            balance_score += 1.0 - abs(ideal_ratio - actual_ratio)
        balance_score /= len(ideal_distribution)
        
        return {
            "balance_score": round(balance_score, 3),
            "distribution": difficulty_distribution,
            "counts": dict(difficulty_counts),
            "total_study_time_minutes": sum(time_estimates),
            "average_atom_time": round(statistics.mean(time_estimates), 1) if time_estimates else 0,
            "time_std_dev": round(statistics.stdev(time_estimates), 1) if len(time_estimates) > 1 else 0
        }
    
    def _calculate_graph_metrics(self, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate dependency graph metrics."""
        
        total_atoms = len(atoms)
        if total_atoms == 0:
            return {"density": 0.0, "avg_prerequisites": 0}
        
        # Build adjacency information
        total_edges = 0
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for atom in atoms:
            atom_id = str(atom.get("id", ""))
            prerequisites = atom.get("prerequisites", [])
            
            out_degree[atom_id] = len(prerequisites)
            total_edges += len(prerequisites)
            
            for prereq in prerequisites:
                in_degree[prereq] += 1
        
        # Calculate metrics
        max_possible_edges = total_atoms * (total_atoms - 1)
        density = total_edges / max(max_possible_edges, 1)
        
        # Find root nodes (no prerequisites) and leaf nodes (no dependents)
        root_nodes = sum(1 for atom in atoms if not atom.get("prerequisites", []))
        leaf_nodes = sum(1 for aid in out_degree if in_degree[aid] == 0)
        
        # Average prerequisites per atom
        avg_prerequisites = total_edges / total_atoms
        
        # Detect potential bottlenecks (atoms with high in-degree)
        bottlenecks = []
        for atom_id, degree in in_degree.items():
            if degree > avg_prerequisites * 2:  # Arbitrary threshold
                bottlenecks.append((atom_id, degree))
        
        return {
            "density": round(density, 4),
            "total_edges": total_edges,
            "avg_prerequisites": round(avg_prerequisites, 2),
            "root_nodes": root_nodes,
            "leaf_nodes": leaf_nodes,
            "bottlenecks": sorted(bottlenecks, key=lambda x: x[1], reverse=True)[:5],
            "max_in_degree": max(in_degree.values()) if in_degree else 0,
            "max_out_degree": max(out_degree.values()) if out_degree else 0
        }
    
    def _calculate_overall_quality_score(self, atoms: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score based on multiple factors."""
        
        if not atoms:
            return 0.0
        
        scores = []
        
        # Atom completeness score
        completeness_score = 0.0
        required_fields = ["title", "content", "learning_objectives", "difficulty_level", "prerequisites"]
        
        for atom in atoms:
            field_score = sum(1 for field in required_fields if atom.get(field)) / len(required_fields)
            completeness_score += field_score
        
        completeness_score /= len(atoms)
        scores.append(completeness_score)
        
        # Content quality indicators
        content_quality = 0.0
        for atom in atoms:
            content = atom.get("content", "")
            objectives = atom.get("learning_objectives", [])
            
            # Check content length (not too short, not too long)
            content_length = len(content)
            if 100 <= content_length <= 2000:
                content_quality += 0.5
            elif 50 <= content_length <= 3000:
                content_quality += 0.3
            
            # Check if objectives are present and meaningful
            if len(objectives) >= 1:
                content_quality += 0.5
        
        content_quality /= len(atoms)
        scores.append(content_quality)
        
        # Validation issues penalty
        validation_penalty = sum(
            1 for atom in atoms 
            if atom.get("status") == "needs_review" or atom.get("validation_issues")
        ) / len(atoms)
        scores.append(1.0 - validation_penalty)
        
        # Calculate weighted average
        overall_score = sum(scores) / len(scores)
        
        return round(overall_score, 3)
    
    def _generate_summary(self, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the atomization results."""
        
        total_atoms = len(atoms)
        
        # Group by status
        status_counts = Counter(atom.get("status", "active") for atom in atoms)
        
        # Identify most complex atoms
        complex_atoms = sorted(
            atoms,
            key=lambda a: len(a.get("prerequisites", [])),
            reverse=True
        )[:3]
        
        # Identify atoms with most objectives
        objective_rich = sorted(
            atoms,
            key=lambda a: len(a.get("learning_objectives", [])),
            reverse=True
        )[:3]
        
        return {
            "total_atoms": total_atoms,
            "status_breakdown": dict(status_counts),
            "needs_review": status_counts.get("needs_review", 0),
            "most_complex_atoms": [
                {
                    "id": str(a.get("id", "")),
                    "title": a.get("title", ""),
                    "prerequisites_count": len(a.get("prerequisites", []))
                }
                for a in complex_atoms
            ],
            "most_comprehensive_atoms": [
                {
                    "id": str(a.get("id", "")),
                    "title": a.get("title", ""),
                    "objectives_count": len(a.get("learning_objectives", []))
                }
                for a in objective_rich
            ]
        }
    
    def generate_report(self) -> str:
        """Generate a human-readable report of the metrics."""
        
        if not self.metrics:
            return "No metrics calculated yet."
        
        report = []
        report.append("📊 ATOMIZATION QUALITY REPORT")
        report.append("=" * 50)
        
        # Coherence section
        coh = self.metrics.get("coherence", {})
        report.append(f"\n🔗 CONCEPTUAL COHERENCE")
        report.append(f"   Score: {coh.get('score', 0):.1%}")
        report.append(f"   Unresolved dependencies: {coh.get('unresolved_dependencies', 0)}")
        report.append(f"   Orphan concepts: {coh.get('orphan_concepts', 0)}/{coh.get('total_concepts', 0)}")
        
        # Coverage section
        cov = self.metrics.get("coverage", {})
        report.append(f"\n📚 CONTENT COVERAGE")
        report.append(f"   Coverage ratio: {cov.get('coverage_ratio', 0):.1%}")
        report.append(f"   Unique concepts: {cov.get('unique_concepts_covered', 0)}")
        report.append(f"   Avg atom length: {cov.get('average_atom_length', 0):.0f} chars")
        
        # Difficulty section
        diff = self.metrics.get("difficulty", {})
        report.append(f"\n🎯 DIFFICULTY BALANCE")
        report.append(f"   Balance score: {diff.get('balance_score', 0):.1%}")
        report.append(f"   Total study time: {diff.get('total_study_time_minutes', 0)} minutes")
        report.append(f"   Distribution: {diff.get('counts', {})}")
        
        # Graph section
        graph = self.metrics.get("graph", {})
        report.append(f"\n🕸️ DEPENDENCY GRAPH")
        report.append(f"   Density: {graph.get('density', 0):.2%}")
        report.append(f"   Avg prerequisites: {graph.get('avg_prerequisites', 0):.1f}")
        report.append(f"   Root nodes: {graph.get('root_nodes', 0)}")
        report.append(f"   Bottlenecks: {len(graph.get('bottlenecks', []))}")
        
        # Overall quality
        report.append(f"\n⭐ OVERALL QUALITY SCORE: {self.metrics.get('quality', 0):.1%}")
        
        # Summary
        summary = self.metrics.get("summary", {})
        report.append(f"\n📋 SUMMARY")
        report.append(f"   Total atoms: {summary.get('total_atoms', 0)}")
        report.append(f"   Needs review: {summary.get('needs_review', 0)}")
        
        return "\n".join(report) 