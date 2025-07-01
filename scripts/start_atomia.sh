#!/bin/bash

# Script para iniciar el sistema completo de Atomia
# Este script inicia todos los servicios backend y el frontend

echo "🚀 Iniciando Atomia - Sistema de Aprendizaje Agéntico"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar si un servicio está corriendo
check_service() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✓ $service_name ya está corriendo en puerto $port${NC}"
        return 0
    else
        echo -e "${YELLOW}○ $service_name no está corriendo${NC}"
        return 1
    fi
}

# Función para iniciar un servicio
start_service() {
    local service_path=$1
    local service_name=$2
    local port=$3
    
    echo -e "${YELLOW}Iniciando $service_name...${NC}"
    
    cd "$service_path" || exit
    
    # Activar entorno virtual si existe
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Instalar dependencias si es necesario
    if [ -f "requirements.txt" ] && [ ! -d "venv" ]; then
        echo "Instalando dependencias para $service_name..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Iniciar el servicio en background
    nohup python src/main.py > /tmp/${service_name}.log 2>&1 &
    
    # Esperar a que el servicio esté listo
    sleep 3
    
    if check_service $port "$service_name"; then
        echo -e "${GREEN}✓ $service_name iniciado correctamente${NC}"
    else
        echo -e "${RED}✗ Error al iniciar $service_name${NC}"
        echo "Ver logs en /tmp/${service_name}.log"
    fi
    
    cd - > /dev/null
}

# Verificar que estamos en el directorio correcto
if [ ! -f "README.md" ] || [ ! -d "backend" ]; then
    echo -e "${RED}Error: Este script debe ejecutarse desde la raíz del proyecto Atomia${NC}"
    exit 1
fi

echo ""
echo "1️⃣  Verificando servicios de infraestructura..."
echo "----------------------------------------------"

# Verificar PostgreSQL
if pg_isready -q; then
    echo -e "${GREEN}✓ PostgreSQL está corriendo${NC}"
else
    echo -e "${RED}✗ PostgreSQL no está corriendo${NC}"
    echo "Por favor, inicia PostgreSQL primero"
    exit 1
fi

# Verificar MongoDB
if pgrep -x mongod > /dev/null; then
    echo -e "${GREEN}✓ MongoDB está corriendo${NC}"
else
    echo -e "${RED}✗ MongoDB no está corriendo${NC}"
    echo "Por favor, inicia MongoDB primero"
    exit 1
fi

# Verificar Neo4j
if check_service 7474 "Neo4j" || check_service 7687 "Neo4j Bolt"; then
    echo -e "${GREEN}✓ Neo4j está corriendo${NC}"
else
    echo -e "${RED}✗ Neo4j no está corriendo${NC}"
    echo "Por favor, inicia Neo4j primero"
    exit 1
fi

# Verificar Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis está corriendo${NC}"
else
    echo -e "${RED}✗ Redis no está corriendo${NC}"
    echo "Por favor, inicia Redis primero"
    exit 1
fi

# Verificar RabbitMQ
if rabbitmqctl status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ RabbitMQ está corriendo${NC}"
else
    echo -e "${RED}✗ RabbitMQ no está corriendo${NC}"
    echo "Por favor, inicia RabbitMQ primero"
    exit 1
fi

echo ""
echo "2️⃣  Iniciando servicios backend..."
echo "----------------------------------------------"

# Array de servicios backend
declare -A services=(
    ["atomization"]="8001"
    ["llm_orchestrator"]="8002"
    ["evaluation"]="8003"
    ["planning"]="8004"
    ["questions"]="8005"
    ["api_gateway"]="8000"
)

# Iniciar cada servicio si no está corriendo
for service in "${!services[@]}"; do
    port="${services[$service]}"
    if ! check_service $port "$service"; then
        start_service "backend/services/$service" "$service" "$port"
    fi
done

echo ""
echo "3️⃣  Iniciando frontend Flutter..."
echo "----------------------------------------------"

# Verificar si Flutter está instalado
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}✗ Flutter no está instalado${NC}"
    echo "Por favor, instala Flutter: https://flutter.dev/docs/get-started/install"
    exit 1
fi

# Iniciar Flutter en modo web
cd frontend || exit

echo "Verificando dependencias de Flutter..."
flutter pub get

echo -e "${YELLOW}Iniciando Flutter en modo web...${NC}"
flutter run -d chrome --web-port 3000 &

cd - > /dev/null

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Atomia está iniciándose!${NC}"
echo ""
echo "📍 URLs de acceso:"
echo "   - Frontend:        http://localhost:3000"
echo "   - API Gateway:     http://localhost:8000"
echo "   - Atomization:     http://localhost:8001"
echo "   - LLM Orchestrator: http://localhost:8002"
echo "   - Evaluation:      http://localhost:8003"
echo "   - Planning:        http://localhost:8004"
echo "   - Questions:       http://localhost:8005"
echo ""
echo "📋 Comandos útiles:"
echo "   - Ver logs: tail -f /tmp/<service_name>.log"
echo "   - Detener todo: ./scripts/stop_atomia.sh"
echo "   - Estado: ./scripts/status_atomia.sh"
echo ""
echo "🎉 ¡Disfruta aprendiendo con Atomia!"
echo "==================================================" 