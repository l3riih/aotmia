"""
Test de persistencia para el servicio de atomization
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from src.infrastructure.database.mongodb_repository import MongoDBAtomRepository

# Configurar la conexión a MongoDB para testing
TEST_MONGODB_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "atomia_atoms_test"


def create_sample_atom(atom_id: str = None, title: str = "Función Lineal", difficulty: str = "intermedio") -> dict:
    """Crear un átomo de ejemplo para testing"""
    return {
        "id": atom_id or str(uuid4()),
        "title": title,
        "content": "Una función lineal es una función de la forma f(x) = mx + b, donde m es la pendiente y b es la intersección con el eje y.",
        "difficulty_level": difficulty,
        "prerequisites": [],
        "learning_objectives": [
            "Identificar la estructura de una función lineal",
            "Calcular la pendiente de una función lineal",
            "Determinar la intersección con los ejes"
        ],
        "estimated_time_minutes": 15,
        "tags": ["matemáticas", "álgebra", "funciones"],
        "created_at": datetime.now(),
        "version": 1,
        "status": "active",
        "created_by_agent": True
    }


def create_agent_metadata() -> dict:
    """Crear metadatos de agente de ejemplo"""
    return {
        "reasoning_steps": [
            "Analyzed input content for educational structure",
            "Identified key mathematical concepts",
            "Generated learning objectives",
            "Structured content as learning atom"
        ],
        "tools_used": ["content_analyzer", "objective_generator", "atom_structurer"],
        "iterations": 2,
        "confidence_score": 0.87,
        "reasoning_quality": 0.92,
        "processing_time_ms": 1250
    }


@pytest.mark.asyncio
async def test_atomization_basic_persistence():
    """Test básico de persistencia del repositorio de atomization"""
    
    repository = MongoDBAtomRepository(TEST_MONGODB_URL, TEST_DB_NAME)
    
    try:
        print("✅ Repositorio de atomization creado")
        
        # Crear datos de prueba
        atom_id = str(uuid4())
        atom_data = create_sample_atom(atom_id, "Ecuaciones Cuadráticas", "avanzado")
        agent_metadata = create_agent_metadata()
        
        # Guardar el átomo
        saved_atoms = await repository.save_many_with_agent_metadata([atom_data], agent_metadata)
        assert len(saved_atoms) == 1
        assert saved_atoms[0]["id"] == atom_id
        
        print(f"✅ Átomo guardado con ID: {atom_id}")
        
        # Recuperar el átomo
        saved_atom = await repository.get(atom_id)
        
        # Verificar que se guardó correctamente
        assert saved_atom is not None
        assert saved_atom["id"] == atom_id
        assert saved_atom["title"] == "Ecuaciones Cuadráticas"
        assert saved_atom["difficulty_level"] == "avanzado"
        assert saved_atom["created_by_agent"] is True
        assert "agent_metadata" in saved_atom
        
        print(f"✅ Átomo recuperado exitosamente")
        print(f"   - ID: {saved_atom['id']}")
        print(f"   - Título: {saved_atom['title']}")
        print(f"   - Dificultad: {saved_atom['difficulty_level']}")
        print(f"   - Tags: {saved_atom['tags']}")
        print(f"   - Objetivos: {len(saved_atom['learning_objectives'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        # Limpiar y cerrar conexión
        await repository.close()


@pytest.mark.asyncio
async def test_atomization_multiple_atoms():
    """Test de múltiples átomos con diferentes dificultades"""
    
    repository = MongoDBAtomRepository(TEST_MONGODB_URL, TEST_DB_NAME)
    
    try:
        agent_metadata = create_agent_metadata()
        atom_ids = []
        
        # Crear múltiples átomos con diferentes dificultades
        difficulties = ["básico", "intermedio", "avanzado"]
        topics = ["Suma y Resta", "Multiplicación", "División Polinómica"]
        
        atoms_data = []
        for i, (difficulty, topic) in enumerate(zip(difficulties, topics)):
            atom_id = str(uuid4())
            atom_data = create_sample_atom(atom_id, topic, difficulty)
            atoms_data.append(atom_data)
            atom_ids.append(atom_id)
        
        # Guardar todos los átomos de una vez
        saved_atoms = await repository.save_many_with_agent_metadata(atoms_data, agent_metadata)
        
        assert len(saved_atoms) == 3
        print(f"✅ {len(saved_atoms)} átomos guardados exitosamente")
        
        # Verificar que todos se guardaron
        for i, atom_id in enumerate(atom_ids):
            saved_atom = await repository.get(atom_id)
            assert saved_atom is not None
            assert saved_atom["difficulty_level"] == difficulties[i]
            print(f"✅ Átomo {i+1}: {saved_atom['title']} ({saved_atom['difficulty_level']})")
        
        # Obtener todos los átomos
        all_atoms = await repository.get_all(limit=10)
        assert len(all_atoms) >= 3
        print(f"✅ Total de átomos en base: {len(all_atoms)}")
        
        # Buscar por dificultad específica
        intermediate_atoms = await repository.get_by_difficulty("intermedio")
        assert len(intermediate_atoms) >= 1
        print(f"✅ Átomos de nivel intermedio: {len(intermediate_atoms)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test múltiple: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await repository.close()


@pytest.mark.asyncio
async def test_atomization_search_functionality():
    """Test de funcionalidades de búsqueda"""
    
    repository = MongoDBAtomRepository(TEST_MONGODB_URL, TEST_DB_NAME)
    
    try:
        agent_metadata = create_agent_metadata()
        
        # Crear átomos con contenido específico para búsqueda
        search_atoms = [
            create_sample_atom(str(uuid4()), "Teorema de Pitágoras", "intermedio"),
            create_sample_atom(str(uuid4()), "Área del Triángulo", "básico"),
            create_sample_atom(str(uuid4()), "Volumen de Prismas", "avanzado")
        ]
        
        # Modificar contenido y tags para búsqueda
        search_atoms[0]["content"] = "El teorema de Pitágoras establece que en un triángulo rectángulo..."
        search_atoms[0]["tags"] = ["geometría", "triángulos", "teoremas"]
        
        search_atoms[1]["content"] = "El área de un triángulo se calcula como base por altura dividido entre dos..."
        search_atoms[1]["tags"] = ["geometría", "área", "triángulos"]
        
        search_atoms[2]["content"] = "El volumen de un prisma rectangular se calcula multiplicando..."
        search_atoms[2]["tags"] = ["geometría", "volumen", "prismas"]
        
        # Guardar átomos
        saved_atoms = await repository.save_many_with_agent_metadata(search_atoms, agent_metadata)
        assert len(saved_atoms) == 3
        print("✅ Átomos de búsqueda guardados")
        
        # Test búsqueda por contenido
        search_results = await repository.search_by_content("triángulo", limit=5)
        assert len(search_results) >= 2  # Debería encontrar los 2 átomos con "triángulo"
        print(f"✅ Búsqueda por 'triángulo': {len(search_results)} resultados")
        
        # Test búsqueda por tags
        geometry_atoms = await repository.get_by_tags(["geometría"], limit=10)
        assert len(geometry_atoms) >= 3  # Los 3 átomos tienen tag "geometría"
        print(f"✅ Búsqueda por tag 'geometría': {len(geometry_atoms)} resultados")
        
        # Test estadísticas
        stats = await repository.get_stats()
        assert stats["total_atoms"] >= 3
        assert stats["agent_created_atoms"] >= 3
        assert "difficulty_distribution" in stats
        
        print(f"✅ Estadísticas:")
        print(f"   - Total átomos: {stats['total_atoms']}")
        print(f"   - Creados por agente: {stats['agent_created_atoms']}")
        print(f"   - Distribución por dificultad: {stats['difficulty_distribution']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de búsqueda: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await repository.close()


@pytest.mark.asyncio
async def test_atomization_crud_operations():
    """Test de operaciones CRUD completas"""
    
    repository = MongoDBAtomRepository(TEST_MONGODB_URL, TEST_DB_NAME)
    
    try:
        agent_metadata = create_agent_metadata()
        atom_id = str(uuid4())
        
        # CREATE
        atom_data = create_sample_atom(atom_id, "Sistemas de Ecuaciones", "intermedio")
        saved_atoms = await repository.save_many_with_agent_metadata([atom_data], agent_metadata)
        assert len(saved_atoms) == 1
        print(f"✅ CREATE: Átomo creado con ID {atom_id}")
        
        # READ
        saved_atom = await repository.get(atom_id)
        assert saved_atom is not None
        assert saved_atom["title"] == "Sistemas de Ecuaciones"
        print(f"✅ READ: Átomo leído correctamente")
        
        # UPDATE
        update_data = {
            "title": "Sistemas de Ecuaciones Lineales",
            "difficulty_level": "avanzado",
            "tags": ["álgebra", "sistemas", "ecuaciones", "matrices"]
        }
        update_success = await repository.update_atom(atom_id, update_data)
        assert update_success is True
        
        # Verificar actualización
        updated_atom = await repository.get(atom_id)
        assert updated_atom["title"] == "Sistemas de Ecuaciones Lineales"
        assert updated_atom["difficulty_level"] == "avanzado"
        assert "matrices" in updated_atom["tags"]
        print(f"✅ UPDATE: Átomo actualizado correctamente")
        
        # DELETE
        delete_success = await repository.delete_atom(atom_id)
        assert delete_success is True
        
        # Verificar eliminación
        deleted_atom = await repository.get(atom_id)
        assert deleted_atom is None
        print(f"✅ DELETE: Átomo eliminado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test CRUD: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await repository.close()


if __name__ == "__main__":
    # Permitir ejecutar el test directamente
    async def run_tests():
        try:
            await test_atomization_basic_persistence()
            print("\n" + "="*50)
            await test_atomization_multiple_atoms()
            print("\n" + "="*50)
            await test_atomization_search_functionality()
            print("\n" + "="*50)
            await test_atomization_crud_operations()
            print("\n✅ Todos los tests de atomization completados exitosamente!")
        except Exception as e:
            print(f"\n❌ Error en los tests: {e}")
    
    asyncio.run(run_tests()) 