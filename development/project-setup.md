# Guía de Configuración del Proyecto - Atomia

## Inicio Rápido

### Prerrequisitos
- Python 3.11+
- Node.js 18+
- Flutter 3.16+
- PostgreSQL 15+
- MongoDB 7.0+
- Redis 7.0+
- Neo4j 5.0+
- RabbitMQ 3.12+
- Git

### Clonar y Configurar
```bash
# Clonar repositorio
git clone https://github.com/tu-org/atomia.git
cd atomia

# Crear archivo de variables de entorno
cp .env.example .env

# Editar .env con las credenciales de Azure
AZURE_AI_KEY="7iNKmFVaL5hhI9xKpNtOpf6ZduUbks8Dx6OJuanXRTlI7Lbmo5ctJQQJ99BFACfhMk5XJ3w3AAAAACOGJZUW"
AZURE_AI_ENDPOINT="https://ai-bryanjavierjaramilloc0912ai799661901077.services.ai.azure.com/models"
AZURE_AI_MODEL="deepseek-r1"
```

## Estructura del Proyecto

### Organización General
```
atomia/
├── .cursorrules             # Reglas para Cursor AI
├── development/             # Guías de desarrollo
│   ├── llm-integration.md
│   ├── flutter-architecture.md
│   ├── backend-services.md
│   └── database-design.md
├── backend/                 # Servicios backend
│   ├── api_gateway/
│   ├── services/
│   └── shared/
├── frontend/               # Aplicación Flutter
│   ├── lib/
│   ├── test/
│   └── pubspec.yaml
├── infrastructure/         # Scripts y configuraciones
│   ├── scripts/
│   └── configs/
├── docs/                   # Documentación original
└── tests/                  # Tests de integración
```

## Instalación de Dependencias del Sistema

### 1. PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (Homebrew)
brew install postgresql
brew services start postgresql

# Arch Linux
sudo pacman -S postgresql
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Configurar usuario y base de datos
sudo -u postgres createuser --interactive atomia
sudo -u postgres createdb atomia_dev
```

### 2. MongoDB
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install mongodb-org
sudo systemctl start mongod

# macOS (Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Arch Linux
sudo pacman -S mongodb-bin
sudo systemctl enable mongodb
sudo systemctl start mongodb
```

### 3. Redis
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# macOS (Homebrew)
brew install redis
brew services start redis

# Arch Linux
sudo pacman -S redis
sudo systemctl enable redis
sudo systemctl start redis
```

### 4. Neo4j
```bash
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j
sudo systemctl start neo4j

# macOS (Homebrew)
brew install neo4j
brew services start neo4j

# Arch Linux (AUR)
yay -S neo4j-community
sudo systemctl enable neo4j
sudo systemctl start neo4j
```

### 5. RabbitMQ
```bash
# Ubuntu/Debian
sudo apt install rabbitmq-server
sudo systemctl start rabbitmq-server

# macOS (Homebrew)
brew install rabbitmq
brew services start rabbitmq

# Arch Linux
sudo pacman -S rabbitmq
sudo systemctl enable rabbitmq
sudo systemctl start rabbitmq
```

## Configuración Backend

### 1. Configurar Entorno Virtual Python
```bash
# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias base
pip install -r backend/requirements-base.txt
```

### 2. Configurar Bases de Datos
```bash
# PostgreSQL - Crear esquemas y usuario
sudo -u postgres psql
CREATE DATABASE atomia_dev;
CREATE USER atomia_user WITH PASSWORD 'atomia_password';
GRANT ALL PRIVILEGES ON DATABASE atomia_dev TO atomia_user;
\q

# MongoDB - Configurar base de datos
mongosh
use atomia_dev
db.createCollection("atoms")
db.createCollection("learning_sessions")
exit

# Neo4j - Configurar base de datos (opcional, configuración web en http://localhost:7474)
# Usuario: neo4j, Password: configurar en primera ejecución

# Redis - Verificar funcionamiento
redis-cli ping
```

### 3. Ejecutar Migraciones y Setup Inicial
```bash
# Ejecutar migraciones PostgreSQL
cd backend/api_gateway
alembic upgrade head

# Inicializar MongoDB
python scripts/init_mongodb.py

# Configurar Neo4j
python scripts/init_neo4j.py
```

### 4. Configurar Servicios
```bash
# Para cada servicio
cd backend/services/{service_name}
pip install -r requirements.txt
python -m pytest tests/  # Ejecutar tests

# Iniciar servicio en modo desarrollo
uvicorn src.main:app --reload --port {puerto}
```

### Puertos por Servicio
- API Gateway: 8000
- Atomization Service: 8001
- Evaluation Service: 8002
- Planning Service: 8003
- Question Generation: 8004
- Gamification Service: 8005

## Configuración Frontend (Flutter)

### 1. Instalar Dependencias
```bash
cd frontend
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

### 2. Configurar Variables de Entorno
```dart
// frontend/lib/core/config/env.dart
class Environment {
  static const String apiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://localhost:8000/api',
  );
  
  static const String environment = String.fromEnvironment(
    'ENV',
    defaultValue: 'development',
  );
}
```

### 3. Ejecutar en Modo Desarrollo
```bash
# Web
flutter run -d chrome --dart-define=API_URL=http://localhost:8000/api

# iOS (requiere Mac)
flutter run -d ios --dart-define=API_URL=http://localhost:8000/api

# Android
flutter run -d android --dart-define=API_URL=http://10.0.2.2:8000/api
```

## Workflow de Desarrollo

### 1. Crear Nueva Feature
```bash
# Crear branch desde develop
git checkout develop
git pull origin develop
git checkout -b feature/nombre-feature

# Trabajar en la feature
# ...commits...

# Push y crear PR
git push origin feature/nombre-feature
```

### 2. Estructura de Commits
```
feat: Agregar servicio de atomización
fix: Corregir evaluación de respuestas abiertas
docs: Actualizar documentación de API
test: Agregar tests para planificador adaptativo
refactor: Extraer interfaz de cliente LLM
style: Formatear código según estándares
chore: Actualizar dependencias
```

### 3. Testing Local
```bash
# Backend: Unit tests
cd backend/services/{service}
python -m pytest tests/unit

# Backend: Integration tests
python -m pytest tests/integration

# Frontend: Unit tests
cd frontend
flutter test

# Frontend: Widget tests
flutter test test/widgets

# E2E tests
cd tests/e2e
npm install
npm run test
```

## Debugging y Desarrollo

### VS Code Launch Configurations
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "API Gateway",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--port", "8000"
      ],
      "cwd": "${workspaceFolder}/backend/api_gateway",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    },
    {
      "name": "Flutter Web",
      "type": "dart",
      "request": "launch",
      "program": "lib/main.dart",
      "cwd": "${workspaceFolder}/frontend",
      "args": [
        "--dart-define=API_URL=http://localhost:8000/api",
        "--dart-define=ENV=development"
      ]
    }
  ]
}
```

### Logging y Monitoreo Local
```python
# backend/shared/logging_config.py
import logging
import sys

def setup_logging(service_name: str):
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - {service_name} - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/{service_name}.log')
        ]
    )
```

## Scripts Útiles

### Resetear Base de Datos
```bash
#!/bin/bash
# scripts/reset_db.sh

# Parar servicios
sudo systemctl stop postgresql mongodb redis neo4j rabbitmq

# Limpiar datos PostgreSQL
sudo -u postgres dropdb atomia_dev
sudo -u postgres createdb atomia_dev
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE atomia_dev TO atomia_user;"

# Limpiar MongoDB
mongosh atomia_dev --eval "db.dropDatabase()"

# Reiniciar servicios
sudo systemctl start postgresql mongodb redis neo4j rabbitmq

# Ejecutar migraciones
cd backend/api_gateway && alembic upgrade head
python scripts/seed_initial_data.py
```

### Generar Datos de Prueba
```python
# scripts/generate_test_data.py
import asyncio
from backend.services.atomization import AtomizationService

async def generate_test_atoms():
    service = AtomizationService()
    
    test_content = """
    La fotosíntesis es el proceso mediante el cual las plantas 
    convierten la luz solar en energía química...
    """
    
    atoms = await service.atomize(test_content)
    print(f"Generated {len(atoms)} atoms")
    
asyncio.run(generate_test_atoms())
```

### Ejecutar Todos los Servicios
```bash
#!/bin/bash
# scripts/run_all_services.sh

# Verificar que todos los servicios del sistema estén corriendo
sudo systemctl status postgresql mongodb redis neo4j rabbitmq

# Terminal 1: API Gateway
cd backend/api_gateway && uvicorn src.main:app --reload

# Terminal 2: Atomization Service  
cd backend/services/atomization && uvicorn src.main:app --reload --port 8001

# Terminal 3: Evaluation Service
cd backend/services/evaluation && uvicorn src.main:app --reload --port 8002

# Terminal 4: Planning Service
cd backend/services/planning && uvicorn src.main:app --reload --port 8003

# Terminal 5: Question Generation Service
cd backend/services/questions && uvicorn src.main:app --reload --port 8004

# Terminal 6: Gamification Service
cd backend/services/gamification && uvicorn src.main:app --reload --port 8005

# O usar Procfile con honcho/foreman
honcho start
```

## Troubleshooting Común

### Error: Azure AI Connection Failed
```python
# Verificar credenciales
import os
print(os.getenv("AZURE_AI_KEY"))
print(os.getenv("AZURE_AI_ENDPOINT"))

# Test conexión
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

client = ChatCompletionsClient(
    endpoint=os.getenv("AZURE_AI_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_AI_KEY"))
)
```

### Error: Servicios del Sistema No Funcionan
```bash
# Ver estado de servicios
sudo systemctl status postgresql mongodb redis neo4j rabbitmq

# Reiniciar servicio específico
sudo systemctl restart {service_name}

# Ver logs de un servicio
sudo journalctl -u {service_name} -f

# Verificar puertos en uso
sudo netstat -tlnp | grep :5432  # PostgreSQL
sudo netstat -tlnp | grep :27017 # MongoDB
sudo netstat -tlnp | grep :6379  # Redis
sudo netstat -tlnp | grep :7474  # Neo4j
sudo netstat -tlnp | grep :5672  # RabbitMQ
```

### Error: Flutter Build Issues
```bash
# Limpiar cache
flutter clean
flutter pub cache clean
flutter pub get

# Regenerar código
flutter pub run build_runner build --delete-conflicting-outputs

# Reset iOS pods (Mac)
cd ios && pod deintegrate && pod install
```

## Recursos Adicionales

### Documentación Interna
- [Arquitectura General](.cursorrules)
- [Integración LLM](development/llm-integration.md)
- [Arquitectura Flutter](development/flutter-architecture.md)
- [Servicios Backend](development/backend-services.md)
- [Diseño de BD](development/database-design.md)

### Herramientas Recomendadas
- **IDE**: VS Code con extensiones Python, Flutter
- **API Testing**: Postman o Insomnia
- **DB Client**: DBeaver o TablePlus
- **Git GUI**: GitKraken o SourceTree
- **System Monitor**: htop, btop, o Activity Monitor (macOS)

### Convenciones de Código
- **Python**: Black + isort + flake8
- **Dart/Flutter**: dart format + flutter analyze
- **SQL**: SQLFluff
- **Commits**: Conventional Commits

## Checklist Pre-Commit

- [ ] Tests pasan localmente
- [ ] Código formateado según estándares
- [ ] Documentación actualizada si necesario
- [ ] Sin credenciales hardcodeadas
- [ ] Logs apropiados agregados
- [ ] Error handling implementado
- [ ] Performance considerada
- [ ] Seguridad revisada 