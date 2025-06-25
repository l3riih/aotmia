# Diseño de Bases de Datos - Atomia

## Arquitectura de Datos Multi-Base

### PostgreSQL (Datos Estructurados)

#### Schema: Users & Authentication
```sql
-- Tabla de usuarios
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    learning_style VARCHAR(50) DEFAULT 'mixed',
    preferred_difficulty VARCHAR(20) DEFAULT 'intermediate',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);

-- Índices
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- Tabla de sesiones
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(token_hash);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at) WHERE expires_at > NOW();
```

#### Schema: Study Progress
```sql
-- Progreso general del estudiante
CREATE TABLE student_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_study_time_minutes INTEGER DEFAULT 0,
    total_atoms_completed INTEGER DEFAULT 0,
    total_questions_answered INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    current_streak_days INTEGER DEFAULT 0,
    max_streak_days INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_study_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_progress_user_id ON student_progress(user_id);

-- Sesiones de estudio
CREATE TABLE study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    atoms_studied INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    average_response_time_seconds FLOAT,
    energy_level VARCHAR(20), -- 'high', 'medium', 'low'
    completed BOOLEAN DEFAULT false
);

CREATE INDEX idx_sessions_user_date ON study_sessions(user_id, started_at DESC);
CREATE INDEX idx_sessions_completed ON study_sessions(user_id, completed) WHERE completed = true;

-- Respuestas a preguntas
CREATE TABLE question_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES study_sessions(id) ON DELETE SET NULL,
    question_id UUID NOT NULL,
    atom_id UUID NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    user_answer TEXT,
    is_correct BOOLEAN NOT NULL,
    score FLOAT NOT NULL CHECK (score >= 0 AND score <= 1),
    time_spent_seconds INTEGER,
    attempt_number INTEGER DEFAULT 1,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_responses_user_atom ON question_responses(user_id, atom_id);
CREATE INDEX idx_responses_session ON question_responses(session_id);
CREATE INDEX idx_responses_date ON question_responses(user_id, answered_at DESC);
```

#### Schema: Gamification
```sql
-- Logros/Achievements
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    points INTEGER DEFAULT 0,
    category VARCHAR(50), -- 'progress', 'mastery', 'streak', 'social'
    criteria JSONB NOT NULL, -- Condiciones para desbloquear
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Logros desbloqueados por usuario
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    progress FLOAT DEFAULT 0, -- Para logros progresivos
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_user_achievements ON user_achievements(user_id, unlocked_at DESC);

-- Tabla de clasificación/Leaderboard
CREATE TABLE leaderboard (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'all_time'
    period_date DATE NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    atoms_completed INTEGER DEFAULT 0,
    accuracy_rate FLOAT,
    rank INTEGER,
    UNIQUE(user_id, period_type, period_date)
);

CREATE INDEX idx_leaderboard_period ON leaderboard(period_type, period_date, points DESC);
CREATE INDEX idx_leaderboard_user ON leaderboard(user_id, period_type);
```

### MongoDB (Contenido de Átomos)

#### Colección: learning_atoms
```javascript
{
  "_id": ObjectId("..."),
  "id": "atom_001",
  "title": "Introducción a la Fotosíntesis",
  "summary": "Proceso mediante el cual las plantas convierten luz en energía",
  "content": "La fotosíntesis es un proceso fundamental...", // Texto completo
  "content_html": "<p>La fotosíntesis es...</p>", // Versión HTML enriquecida
  "keywords": ["fotosíntesis", "plantas", "clorofila", "luz solar"],
  "learning_objectives": [
    "Comprender el proceso básico de la fotosíntesis",
    "Identificar los componentes necesarios"
  ],
  "prerequisites": ["atom_biology_basics", "atom_cell_structure"],
  "related_atoms": ["atom_002", "atom_003"],
  "difficulty_level": "intermediate",
  "type": "conceptual",
  "estimated_time_minutes": 10,
  "media": [
    {
      "type": "image",
      "url": "https://cdn.atomia.com/photosynthesis-diagram.png",
      "caption": "Diagrama del proceso de fotosíntesis"
    },
    {
      "type": "video",
      "url": "https://cdn.atomia.com/photosynthesis-animation.mp4",
      "duration_seconds": 120
    }
  ],
  "metadata": {
    "author": "system",
    "version": 1,
    "language": "es",
    "subject": "biology",
    "grade_level": "high_school",
    "tags": ["ciencias", "biología", "procesos-vitales"]
  },
  "created_at": ISODate("2024-01-15T10:00:00Z"),
  "updated_at": ISODate("2024-01-15T10:00:00Z"),
  "status": "active" // 'draft', 'active', 'archived'
}
```

#### Colección: questions
```javascript
{
  "_id": ObjectId("..."),
  "id": "q_001",
  "atom_id": "atom_001",
  "type": "multiple_choice", // 'true_false', 'short_answer', 'flashcard'
  "difficulty": "medium",
  "question_text": "¿Cuál es el producto principal de la fotosíntesis?",
  "options": [
    {
      "id": "opt_a",
      "text": "Dióxido de carbono",
      "is_correct": false,
      "explanation": "El CO2 es un reactante, no un producto"
    },
    {
      "id": "opt_b",
      "text": "Glucosa",
      "is_correct": true,
      "explanation": "Correcto! La glucosa es el azúcar producido"
    },
    {
      "id": "opt_c",
      "text": "Nitrógeno",
      "is_correct": false,
      "explanation": "El nitrógeno no participa en la fotosíntesis"
    }
  ],
  "correct_answer_model": "La fotosíntesis produce glucosa (C6H12O6) y oxígeno como productos principales",
  "hints": [
    "Piensa en qué tipo de molécula necesitan las plantas para obtener energía",
    "Es un tipo de azúcar"
  ],
  "tags": ["conceptual", "productos", "fotosíntesis"],
  "usage_stats": {
    "times_shown": 150,
    "times_answered": 145,
    "correct_rate": 0.72,
    "average_time_seconds": 25
  },
  "created_at": ISODate("2024-01-15T11:00:00Z"),
  "generated_by": "deepseek-r1"
}
```

#### Colección: user_knowledge_state
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "knowledge_graph": {
    "atom_001": {
      "mastery_level": 0.75, // 0-1
      "last_reviewed": ISODate("2024-01-20T15:30:00Z"),
      "review_count": 3,
      "average_score": 0.8,
      "time_spent_total_seconds": 450,
      "fsrs_state": {
        "difficulty": 0.3,
        "stability": 2.5,
        "elapsed_days": 5,
        "scheduled_days": 7,
        "reps": 3,
        "lapses": 0,
        "state": 2, // Learning, Review, Relearning
        "last_review": ISODate("2024-01-20T15:30:00Z")
      }
    },
    "atom_002": {
      "mastery_level": 0.9,
      // ...
    }
  },
  "concept_connections": [
    {
      "from": "atom_001",
      "to": "atom_002",
      "strength": 0.8,
      "type": "prerequisite"
    }
  ],
  "learning_patterns": {
    "best_time_of_day": "morning",
    "average_session_length": 25,
    "preferred_question_types": ["multiple_choice", "flashcard"],
    "struggle_areas": ["chemistry", "complex_processes"],
    "strength_areas": ["definitions", "basic_concepts"]
  },
  "updated_at": ISODate("2024-01-20T16:00:00Z")
}
```

### Neo4j (Grafo de Conocimiento)

#### Nodos y Relaciones
```cypher
// Crear nodo de Átomo
CREATE (a:Atom {
  id: 'atom_001',
  title: 'Fotosíntesis',
  difficulty: 'intermediate',
  subject: 'biology',
  estimated_time: 10
})

// Crear nodo de Concepto
CREATE (c:Concept {
  id: 'concept_photosynthesis',
  name: 'Fotosíntesis',
  category: 'biological_process'
})

// Crear nodo de Habilidad
CREATE (s:Skill {
  id: 'skill_identify_process',
  name: 'Identificar procesos biológicos',
  level: 'analysis'
})

// Relaciones entre átomos
MATCH (a1:Atom {id: 'atom_001'}), (a2:Atom {id: 'atom_002'})
CREATE (a1)-[:PREREQUISITE_OF {importance: 'high'}]->(a2)

// Relación átomo-concepto
MATCH (a:Atom {id: 'atom_001'}), (c:Concept {id: 'concept_photosynthesis'})
CREATE (a)-[:TEACHES]->(c)

// Relación concepto-habilidad
MATCH (c:Concept {id: 'concept_photosynthesis'}), (s:Skill {id: 'skill_identify_process'})
CREATE (c)-[:DEVELOPS]->(s)

// Progreso del usuario
MATCH (u:User {id: 'user_123'}), (a:Atom {id: 'atom_001'})
CREATE (u)-[:COMPLETED {
  score: 0.85,
  date: datetime(),
  time_spent: 600
}]->(a)

// Consulta: Encontrar siguiente átomo óptimo
MATCH (u:User {id: $userId})-[:COMPLETED]->(completed:Atom)
MATCH (next:Atom)-[:PREREQUISITE_OF*0..2]-(completed)
WHERE NOT (u)-[:COMPLETED]->(next)
AND ALL(prereq IN [(next)<-[:PREREQUISITE_OF]-(p:Atom) | p] 
    WHERE (u)-[:COMPLETED]->(prereq))
RETURN next
ORDER BY next.difficulty, next.estimated_time
LIMIT 5
```

### Redis (Cache y Estado de Sesión)

#### Estructuras de Datos
```python
# Cache de respuestas LLM
# Key: llm:atomization:hash(content)
# Value: JSON string de átomos generados
# TTL: 24 horas

# Sesiones de usuario activas
# Key: session:{user_id}
# Value: Hash con datos de sesión
{
    "session_id": "uuid",
    "started_at": "2024-01-20T10:00:00Z",
    "current_atom_id": "atom_001",
    "atoms_completed": ["atom_002", "atom_003"],
    "questions_answered": 15,
    "correct_answers": 12,
    "last_activity": "2024-01-20T10:25:00Z"
}
# TTL: 30 minutos desde última actividad

# Cola de procesamiento asíncrono
# Key: queue:atomization
# Type: List
# Value: JSON de tareas pendientes

# Rate limiting
# Key: rate_limit:{user_id}:{endpoint}
# Value: contador
# TTL: 1 minuto

# Caché de preguntas generadas
# Key: questions:atom:{atom_id}:{difficulty}
# Value: JSON array de preguntas
# TTL: 7 días

# Estado de notificaciones push
# Key: notifications:pending:{user_id}
# Type: List
# Value: Notificaciones pendientes de envío
```

## Migraciones y Versionado

### Alembic para PostgreSQL
```python
# alembic/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Crear tabla users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(), nullable=False, 
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), 
                  server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Crear índices
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email')
    op.drop_table('users')
```

### MongoDB Schema Versioning
```javascript
// migrations/mongodb/001_add_indexes.js
db.learning_atoms.createIndex({ "id": 1 }, { unique: true });
db.learning_atoms.createIndex({ "status": 1, "difficulty_level": 1 });
db.learning_atoms.createIndex({ "keywords": 1 });
db.learning_atoms.createIndex({ "metadata.subject": 1, "metadata.grade_level": 1 });

db.questions.createIndex({ "atom_id": 1, "type": 1 });
db.questions.createIndex({ "difficulty": 1 });

db.user_knowledge_state.createIndex({ "user_id": 1 }, { unique: true });
```

## Optimización y Performance

### Índices Compuestos PostgreSQL
```sql
-- Para consultas frecuentes de progreso
CREATE INDEX idx_responses_user_date_correct 
ON question_responses(user_id, answered_at DESC, is_correct);

-- Para cálculo de estadísticas por átomo
CREATE INDEX idx_responses_atom_stats 
ON question_responses(atom_id, is_correct, score);

-- Para búsqueda de sesiones activas
CREATE INDEX idx_sessions_active 
ON study_sessions(user_id, ended_at) 
WHERE ended_at IS NULL;
```

### Particionamiento de Tablas Grandes
```sql
-- Particionar respuestas por mes
CREATE TABLE question_responses_2024_01 PARTITION OF question_responses
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE question_responses_2024_02 PARTITION OF question_responses
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

### Agregaciones Precalculadas
```sql
-- Vista materializada para estadísticas de usuario
CREATE MATERIALIZED VIEW user_stats AS
SELECT 
    u.id as user_id,
    COUNT(DISTINCT ss.id) as total_sessions,
    SUM(ss.duration_minutes) as total_study_minutes,
    AVG(qr.score) as average_score,
    COUNT(DISTINCT DATE(ss.started_at)) as study_days
FROM users u
LEFT JOIN study_sessions ss ON u.id = ss.user_id
LEFT JOIN question_responses qr ON u.id = qr.user_id
GROUP BY u.id;

-- Refrescar cada hora
CREATE INDEX idx_user_stats_user_id ON user_stats(user_id);
```

## Backup y Recuperación

### Estrategia de Backup
```bash
#!/bin/bash
# backup_databases.sh

# PostgreSQL
pg_dump -h localhost -U atomia -d atomia_db -f /backups/postgres_$(date +%Y%m%d_%H%M%S).sql

# MongoDB
mongodump --uri="mongodb://atomia:pass@localhost:27017" --out=/backups/mongo_$(date +%Y%m%d_%H%M%S)

# Neo4j
neo4j-admin dump --database=neo4j --to=/backups/neo4j_$(date +%Y%m%d_%H%M%S).dump

# Redis (solo si es necesario persistir)
redis-cli --rdb /backups/redis_$(date +%Y%m%d_%H%M%S).rdb

# Subir a S3
aws s3 sync /backups s3://atomia-backups/$(date +%Y%m%d)/
```

### Configuración de Replicación
```yaml
# PostgreSQL Master-Slave
# postgresql.conf (master)
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 64

# MongoDB Replica Set
# mongod.conf
replication:
  replSetName: "atomia-rs"
  
# Neo4j Causal Clustering
dbms.mode=CORE
causal_clustering.initial_discovery_members=server1:5000,server2:5000,server3:5000
``` 