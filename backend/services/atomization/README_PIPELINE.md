# 🔬 Sistema de Atomización Independiente - Atomia

## 📋 Resumen

El **Sistema de Atomización Independiente** es una implementación completa de pipeline modular que convierte documentos largos en átomos de aprendizaje coherentes, manteniendo la consistencia conceptual y pedagógica entre divisiones.

## 🏗️ Arquitectura del Pipeline

### Pipeline de 7 Pasos

```
┌─────────────────────────────────────────────────────────────┐
│                  ATOMIZATION PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│  [Parse] → [Chunk] → [Atomize] → [Relate] → [Validate] →   │
│  [Store] → [Index]                                          │
└─────────────────────────────────────────────────────────────┘
```

### Descripción de Pasos

1. **Parse** - Extrae contenido de múltiples formatos (PDF, DOCX, TXT, HTML, MD)
2. **Chunk** - División jerárquica respetando límites de tokens y coherencia semántica
3. **Atomize** - Procesamiento con agente educativo para crear átomos de aprendizaje
4. **Relate** - Resolución de dependencias entre átomos de diferentes chunks
5. **Validate** - Validación pedagógica y control de calidad
6. **Store** - Persistencia en MongoDB y Neo4j con metadatos
7. **Index** - Creación de índices de búsqueda y cache

## 🔧 Componentes Implementados

### 1. Parsers Multi-Formato (`parsers.py`)

```python
# Formatos soportados
SUPPORTED_PARSERS = {
    "text/plain": TxtParser(),
    "application/pdf": PdfParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser(),
    "text/html": HtmlParser(),
    "text/markdown": MarkdownParser(),
}
```

**Características:**
- Auto-detección de tipo de contenido
- Manejo robusto de errores
- Extracción de metadatos
- Dependencias opcionales (graceful degradation)

### 2. Chunker Jerárquico (`chunker.py`)

```python
def chunk_text_hierarchical(text: str, max_tokens: int = 4000) -> List[Chunk]:
    """División inteligente respetando estructura del documento"""
```

**Estrategias:**
- Detección de encabezados (Markdown, numerados)
- División por párrafos como fallback
- Respeto de límites de tokens
- Preservación de jerarquía conceptual

### 3. Pipeline Orquestador (`pipeline.py`)

```python
async def run_atomization_pipeline(
    raw_data: bytes | str,
    filename: str | None = None,
    content_type: str | None = None,
    objectives: str | None = None,
    difficulty: str = "intermedio",
    user_id: str | None = None
) -> Dict[str, Any]:
```

**Flujo Completo:**
- Contexto compartido entre pasos
- Manejo de errores por paso
- Logging estructurado
- Métricas de calidad

### 4. Pasos Avanzados (`steps.py`)

#### RelateStep
- Extracción de conceptos globales
- Resolución de dependencias cruzadas
- Validación de grafos (detección de ciclos)

#### ValidateStep
- Validación de estructura de átomos
- Control de calidad pedagógica
- Cálculo de scores de calidad

#### StoreStep
- Persistencia en MongoDB
- Relaciones en Neo4j
- Metadatos de pipeline

#### IndexStep
- Índices de búsqueda
- Cache de resultados
- Optimización de consultas

## 🌐 Interfaz Web

### Dashboard de Gestión (`dashboard.py`)

**Rutas Disponibles:**
- `/dashboard/` - Dashboard principal
- `/dashboard/upload` - Interfaz de subida de archivos
- `/dashboard/monitor/{processing_id}` - Monitoreo en tiempo real
- `/dashboard/results/{result_id}` - Visualización de resultados
- `/dashboard/graph/{result_id}` - Grafo de dependencias

**Características:**
- Drag & drop para archivos
- Progreso en tiempo real
- Visualización de métricas
- Grafo interactivo de dependencias

## 🚀 Uso del Sistema

### 1. API Endpoint

```bash
curl -X POST "http://localhost:8001/api/v1/pipeline/process" \
  -F "file=@documento.pdf" \
  -F "objectives=Introducir conceptos de cálculo" \
  -F "difficulty=intermedio" \
  -F "user_id=usuario_123"
```

### 2. Interfaz Web

1. Visitar `http://localhost:8001/dashboard/`
2. Navegar a "Subir Documento"
3. Arrastrar archivo o seleccionar
4. Configurar parámetros
5. Monitorear progreso
6. Revisar resultados

### 3. Programáticamente

```python
from atomization.src.domain.pipeline import run_atomization_pipeline

result = await run_atomization_pipeline(
    raw_data=pdf_bytes,
    filename="documento.pdf",
    content_type="application/pdf",
    objectives="Introducir funciones matemáticas",
    difficulty="intermedio",
    user_id="user_123"
)

atoms = result["atoms"]
metadata = result["metadata"]
```

## 📊 Métricas y Monitoreo

### Métricas de Calidad

```python
{
    "quality_metrics": {
        "average_quality_score": 0.87,
        "validation_pass_rate": 0.93,
        "dependency_coherence": 0.91
    },
    "processing_metrics": {
        "total_time_seconds": 154,
        "chunks_processed": 4,
        "concepts_identified": 12,
        "cross_chunk_dependencies": 6
    }
}
```

### Logging Estructurado

```json
{
    "event": "pipeline_complete",
    "filename": "documento.pdf",
    "user_id": "user_123",
    "atoms_created": 15,
    "chunks_processed": 4,
    "processing_time": "2m 34s",
    "quality_score": 0.87
}
```

## 🔍 Resolución de Dependencias

### Algoritmo Multi-Pasada

1. **Pasada 1**: Atomización local por chunk
2. **Pasada 2**: Mapeo conceptual global
3. **Pasada 3**: Resolución de referencias cruzadas
4. **Pasada 4**: Validación de coherencia

### Manejo de Conceptos

```python
{
    "concepto_funcion": {
        "name": "Función Matemática",
        "introduced_in": ["atom_001"],
        "referenced_in": ["atom_002", "atom_003"],
        "dependencies": []
    }
}
```

## 🛠️ Configuración

### Variables de Entorno

```bash
# LLM Orchestrator
LLM_ORCHESTRATOR_URL=http://localhost:8002

# Bases de datos
MONGODB_URL=mongodb://localhost:27017
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379

# Pipeline
MAX_TOKENS_PER_CHUNK=4000
ENABLE_VALIDATION=true
CACHE_TTL_SECONDS=3600
```

### Dependencias

```bash
pip install python-docx beautifulsoup4 markdown
```

## 🧪 Testing

### Tests de Pipeline

```python
# Test completo del pipeline
pytest tests/test_pipeline_integration.py

# Test de parsers específicos
pytest tests/test_parsers.py

# Test de chunker
pytest tests/test_chunker.py
```

### Casos de Prueba

1. **Documentos PDF largos** (>50 páginas)
2. **Archivos DOCX con estructura compleja**
3. **Contenido HTML con múltiples secciones**
4. **Markdown con jerarquía anidada**
5. **Texto plano sin estructura**

## 🚦 Estado Actual

### ✅ Implementado

- [x] Pipeline completo de 7 pasos
- [x] Parsers para 5 formatos
- [x] Chunker jerárquico
- [x] Resolución de dependencias
- [x] Validación pedagógica
- [x] Interfaz web básica
- [x] API endpoints
- [x] Logging estructurado

### 🔄 En Desarrollo

- [ ] Tests de integración completos
- [ ] Optimización de performance
- [ ] Cache avanzado
- [ ] Métricas detalladas
- [ ] Documentación de API

### 🎯 Próximas Mejoras

- [ ] Soporte para EPUB
- [ ] Extracción de imágenes/diagramas
- [ ] IA para detección de estructura
- [ ] Paralelización de chunks
- [ ] Dashboard en tiempo real

## 📈 Performance

### Benchmarks Estimados

| Tamaño Documento | Tiempo Procesamiento | Átomos Generados |
|------------------|---------------------|------------------|
| 1-5 páginas      | 30-60 segundos      | 5-15 átomos      |
| 5-20 páginas     | 1-3 minutos         | 15-50 átomos     |
| 20-50 páginas    | 3-8 minutos         | 50-150 átomos    |
| 50+ páginas      | 8-20 minutos        | 150+ átomos      |

### Optimizaciones

- **Procesamiento paralelo** de chunks independientes
- **Cache inteligente** de resultados similares
- **Streaming** para documentos muy largos
- **Compresión** de metadatos

## 🤝 Contribución

### Agregar Nuevo Parser

```python
class EpubParser(BaseParser):
    content_type = "application/epub+zip"
    
    def parse(self, data: bytes, *, filename: str | None = None):
        # Implementar extracción EPUB
        pass

# Registrar en SUPPORTED_PARSERS
SUPPORTED_PARSERS["application/epub+zip"] = EpubParser()
```

### Agregar Paso de Pipeline

```python
class CustomStep(PipelineStep):
    name = "custom"
    
    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Implementar lógica personalizada
        return context

# Agregar al pipeline
steps.append(CustomStep())
```

---

**El Sistema de Atomización Independiente representa un avance significativo en el procesamiento automático de contenido educativo, combinando técnicas de NLP avanzadas con principios pedagógicos sólidos para crear experiencias de aprendizaje personalizadas y efectivas.** 