"""
Temporary module for dependency graph and topological sorting.
"""

from typing import Dict, List, Tuple, Set, Any


def build_dependency_graph(atoms: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Construye un grafo de dependencias a partir de una lista de átomos.
    
    Args:
        atoms: Lista de átomos con estructura {'id': str, 'dependencies': List[str], ...}
    
    Returns:
        Diccionario donde las claves son IDs de átomos y los valores son listas de dependencias
    """
    dependency_graph = {}
    
    for atom in atoms:
        atom_id = atom.get('id', '')
        dependencies = atom.get('dependencies', [])
        
        if atom_id:
            dependency_graph[atom_id] = dependencies
    
    return dependency_graph


def topological_sort_atoms(dependency_graph: Dict[str, List[str]]) -> Tuple[List[str], bool]:
    """
    Ordena los átomos topológicamente basándose en sus dependencias.
    
    Args:
        dependency_graph: Grafo de dependencias {atom_id: [dependency_ids]}
    
    Returns:
        Tuple con (lista_ordenada, hay_ciclo)
    """
    # Kahn's algorithm for topological sorting
    in_degree = {}
    
    # Initialize in-degree for all nodes
    for node in dependency_graph:
        in_degree[node] = 0
    
    # Calculate in-degrees
    for node in dependency_graph:
        for dependency in dependency_graph[node]:
            if dependency in in_degree:
                in_degree[dependency] += 1
    
    # Queue for nodes with no incoming edges
    queue = [node for node in in_degree if in_degree[node] == 0]
    result = []
    
    while queue:
        node = queue.pop(0)
        result.append(node)
        
        # For each dependency of the current node
        for dependency in dependency_graph.get(node, []):
            if dependency in in_degree:
                in_degree[dependency] -= 1
                if in_degree[dependency] == 0:
                    queue.append(dependency)
    
    # Check for cycles
    has_cycle = len(result) != len(dependency_graph)
    
    return result, has_cycle 