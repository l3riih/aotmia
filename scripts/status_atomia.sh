#!/bin/bash

# Script para verificar el estado de todos los servicios de Atomia
echo "📊 Estado de Atomia - Sistema de Aprendizaje Agéntico"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar si un servicio está corriendo
check_service_status() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pid=$(lsof -ti:$port)
        echo -e "${GREEN}✓ $service_name${NC} - Puerto $port (PID: $pid)"
        return 0
    else
        echo -e "${RED}✗ $service_name${NC} - Puerto $port"
        return 1
    fi
}

echo ""
echo "🏗️  Servicios de Infraestructura:"
echo "----------------------------------------------"

# PostgreSQL
if pg_isready -q 2>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL${NC}"
else
    echo -e "${RED}✗ PostgreSQL${NC}"
fi

# MongoDB
if pgrep -x mongod > /dev/null; then
    echo -e "${GREEN}✓ MongoDB${NC}"
else
    echo -e "${RED}✗ MongoDB${NC}"
fi

# Neo4j
if lsof -Pi :7474 -sTCP:LISTEN -t >/dev/null 2>&1 || lsof -Pi :7687 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Neo4j${NC}"
else
    echo -e "${RED}✗ Neo4j${NC}"
fi

# Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis${NC}"
else
    echo -e "${RED}✗ Redis${NC}"
fi

# RabbitMQ
if rabbitmqctl status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ RabbitMQ${NC}"
else
    echo -e "${RED}✗ RabbitMQ${NC}"
fi

echo ""
echo "🚀 Servicios Backend:"
echo "----------------------------------------------"

# Array de servicios backend
declare -A services=(
    ["API Gateway"]="8000"
    ["Atomization Service"]="8001"
    ["LLM Orchestrator"]="8002"
    ["Evaluation Service"]="8003"
    ["Planning Service"]="8004"
    ["Questions Service"]="8005"
)

running_count=0
total_count=0

# Verificar cada servicio
for service in "API Gateway" "Atomization Service" "LLM Orchestrator" "Evaluation Service" "Planning Service" "Questions Service"; do
    port="${services[$service]}"
    check_service_status $port "$service"
    if [ $? -eq 0 ]; then
        ((running_count++))
    fi
    ((total_count++))
done

echo ""
echo "🌐 Frontend:"
echo "----------------------------------------------"

# Flutter Web
if pgrep -f "flutter.*run.*web-port 3000" > /dev/null; then
    flutter_pid=$(pgrep -f "flutter.*run.*web-port 3000")
    echo -e "${GREEN}✓ Flutter Web${NC} - Puerto 3000 (PID: $flutter_pid)"
else
    echo -e "${RED}✗ Flutter Web${NC} - Puerto 3000"
fi

echo ""
echo "📈 Resumen:"
echo "----------------------------------------------"
echo "Servicios backend activos: $running_count/$total_count"

if [ $running_count -eq $total_count ]; then
    echo -e "${GREEN}✅ Todos los servicios están funcionando correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Algunos servicios no están funcionando${NC}"
    echo "Ejecuta ./scripts/start_atomia.sh para iniciar todos los servicios"
fi

echo ""
echo "==================================================" 