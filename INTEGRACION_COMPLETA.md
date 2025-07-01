# 🔌 Integración Frontend-Backend Completa

## ✅ Estado de la Integración

### 1. **Servicios Backend Conectados**

| Servicio | Puerto | Estado | Integración Frontend |
|----------|--------|---------|---------------------|
| API Gateway | 8000 | ✅ Listo | N/A |
| Atomization | 8001 | ✅ Listo | AtomLibraryPage, ChatService |
| LLM Orchestrator | 8002 | ✅ Listo | ChatService |
| Evaluation | 8003 | ✅ Listo | QuizPage, ChatService |
| Planning | 8004 | ✅ Listo | LearningPathPage, HomePage |
| Questions | 8005 | ✅ Listo | QuizPage |

### 2. **Nuevos Servicios Frontend**

#### **LearningService** (`frontend/lib/core/services/learning_service.dart`)
- Gestiona átomos de aprendizaje y rutas educativas
- Integra con servicios de Atomization y Planning
- Funciones principales:
  - `getAtoms()`: Obtiene átomos con filtros
  - `getLearningPaths()`: Obtiene rutas de aprendizaje
  - `markAtomAsCompleted()`: Marca progreso
  - `generatePersonalizedPath()`: Crea rutas personalizadas

#### **QuizService** (`frontend/lib/core/services/quiz_service.dart`)
- Gestiona quizzes y evaluaciones
- Integra con servicios de Questions y Evaluation
- Funciones principales:
  - `generateQuestionsForAtom()`: Genera preguntas para un átomo
  - `evaluateSingleResponse()`: Evalúa respuestas individuales
  - `getUserStatistics()`: Obtiene estadísticas del usuario

### 3. **Páginas Actualizadas**

#### **AtomLibraryPage** ✅
- Usa `LearningService` para cargar átomos desde el backend
- Búsqueda y filtros conectados con API real
- Fallback a datos de ejemplo si el backend no está disponible

#### **LearningPathPage** ✅
- Usa `LearningService` para cargar rutas de aprendizaje
- Sincronización de progreso con el backend
- Actualización en tiempo real del estado de completado

#### **QuizPage** ✅
- Usa `QuizService` para generar preguntas desde el backend
- Evaluación en tiempo real con el servicio de evaluación
- Retroalimentación mejorada con IA

#### **HomePage** ✅
- Muestra estadísticas reales del usuario
- Navegación funcional a todas las secciones
- Carga progreso desde el backend

## 🚀 Cómo Usar el Sistema Integrado

### 1. **Iniciar Todo el Sistema**

```bash
# Desde la raíz del proyecto
./scripts/start_atomia.sh
```

Este script:
- Verifica que todos los servicios de infraestructura estén corriendo
- Inicia todos los servicios backend
- Inicia el frontend Flutter en modo web
- Muestra las URLs de acceso

### 2. **Verificar Estado**

```bash
./scripts/status_atomia.sh
```

Muestra el estado de:
- Servicios de infraestructura (PostgreSQL, MongoDB, Neo4j, Redis, RabbitMQ)
- Servicios backend (todos los microservicios)
- Frontend Flutter

### 3. **Detener Todo**

```bash
./scripts/stop_atomia.sh
```

Detiene ordenadamente:
- Frontend Flutter
- Todos los servicios backend
- Limpia archivos temporales

## 📡 URLs de Acceso

| Componente | URL | Descripción |
|------------|-----|-------------|
| Frontend Web | http://localhost:3000 | Aplicación Flutter |
| API Gateway | http://localhost:8000 | Gateway principal |
| Atomization | http://localhost:8001 | Servicio de atomización |
| LLM Orchestrator | http://localhost:8002 | Orquestador agéntico |
| Evaluation | http://localhost:8003 | Servicio de evaluación |
| Planning | http://localhost:8004 | Planificador adaptativo |
| Questions | http://localhost:8005 | Generador de preguntas |

## 🔧 Configuración

### Variables de Entorno Necesarias

```bash
# En backend/services/llm_orchestrator/.env
AZURE_AI_KEY=tu_clave_azure

# Bases de datos ya configuradas localmente
# PostgreSQL, MongoDB, Neo4j, Redis, RabbitMQ
```

### Modo de Desarrollo vs Producción

El sistema está configurado para funcionar con:
- **Backend disponible**: Usa datos reales desde los servicios
- **Backend no disponible**: Fallback automático a datos de ejemplo

## 🧪 Probar la Integración

### 1. **Chat Educativo**
1. Navega a http://localhost:3000
2. Ve a la sección Chat
3. Haz preguntas educativas
4. Observa cómo el agente razona y usa herramientas

### 2. **Biblioteca de Átomos**
1. Ve a la Biblioteca desde el menú
2. Busca y filtra átomos
3. Los datos vienen del servicio de Atomization

### 3. **Rutas de Aprendizaje**
1. Accede a una ruta desde el home
2. Completa átomos secuencialmente
3. El progreso se sincroniza con Planning Service

### 4. **Quizzes Interactivos**
1. Inicia un quiz desde cualquier átomo
2. Las preguntas se generan dinámicamente
3. La evaluación usa el servicio de Evaluation

## 📊 Monitoreo

### Ver Logs de Servicios

```bash
# Ver logs de un servicio específico
tail -f /tmp/llm_orchestrator.log

# Ver todos los logs
tail -f /tmp/*.log
```

### Verificar Salud de Servicios

```bash
# Health check del orquestador
curl http://localhost:8002/health

# Health check de atomización
curl http://localhost:8001/api/v1/atomization/health
```

## 🐛 Solución de Problemas

### El frontend no se conecta al backend

1. Verifica que todos los servicios estén corriendo:
   ```bash
   ./scripts/status_atomia.sh
   ```

2. Verifica los logs del servicio problemático:
   ```bash
   tail -f /tmp/<nombre_servicio>.log
   ```

3. Reinicia el servicio específico:
   ```bash
   cd backend/services/<servicio>
   python src/main.py
   ```

### Errores de CORS

Si hay problemas de CORS, verifica que los servicios backend tengan configurado:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🎯 Próximos Pasos

1. **Autenticación Real**: Implementar JWT tokens
2. **Persistencia de Sesión**: Mantener el estado del usuario
3. **WebSockets**: Para actualizaciones en tiempo real
4. **Cache**: Mejorar performance con cache estratégico
5. **Tests E2E**: Pruebas de integración completas

---

**¡El sistema está completamente integrado y listo para usar!** 🎉

Los servicios backend y el frontend ahora trabajan juntos para proporcionar una experiencia de aprendizaje personalizada y adaptativa con IA. 